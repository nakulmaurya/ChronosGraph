"""Explicit trusted-local connections and new-snapshot refresh. No source writes.

CLI-only mutation, disabled without configured allowed roots. Reads selected Git
commits, never imports repository code. This is not a public importer sandbox.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import time
from app.db.client import db_manager
from app.ingestion.git_safety import git_command, git_environment
from app.ingestion.ingest_repo import _ingest_repo, writer_locks, EXCLUDED
from app.services.common import TENANT_PATTERN, tenant_exists, read

SHA = re.compile(r'[0-9a-f]{40}\Z')


def git_bytes(root, *args):
    return subprocess.check_output([*git_command(), '-C', str(root), *args],
                                   env=git_environment(), timeout=30, stderr=subprocess.PIPE)


def allowed_repository(source):
    configured = os.environ.get('CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS', '')
    if not configured:
        raise ValueError('Local connections disabled: configure CHRONOSGRAPH_ALLOWED_LOCAL_ROOTS')
    if '://' in source or '\0' in source:
        raise ValueError('Only allowlisted local Git directories are supported in this slice')
    root = Path(source).expanduser().resolve(strict=True)
    allowed = [Path(p).expanduser().resolve(strict=True) for p in configured.split(os.pathsep) if p]
    if not any(p.is_dir() and root.is_relative_to(p) for p in allowed):
        raise ValueError('Repository is outside allowed local roots')
    # Linked worktrees/submodules have separate gitdirs and need a future explicit policy.
    gitdir = root/'.git'
    if not root.is_dir() or gitdir.is_symlink() or not gitdir.is_dir():
        raise ValueError('Require a non-bare repository with an in-root .git directory')
    if git_bytes(root, 'rev-parse', '--show-toplevel').decode().strip() != str(root):
        raise ValueError('Source must be the repository top-level directory')
    return root


def inspect_workspace(root, branch):
    if not branch or len(branch) > 200 or branch.startswith('-'):
        raise ValueError('Require an explicit local branch name, not a ref expression')
    try:
        git_bytes(root, 'check-ref-format', 'refs/heads/'+branch)
        revision = git_bytes(root, 'rev-parse', '--verify', '--end-of-options',
                             'refs/heads/'+branch+'^{commit}').decode().strip()
        head = git_bytes(root, 'rev-parse', '--verify', 'HEAD^{commit}').decode().strip()
        selected = git_bytes(root, 'symbolic-ref', '--quiet', '--short', 'HEAD').decode().strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError('Selected local branch must exist and HEAD must be attached') from exc
    if not SHA.fullmatch(revision) or not SHA.fullmatch(head):
        raise ValueError('Require full SHA-1 commit revisions')
    # Ignore hooks/fsmonitor and external diff commands. Never echo dirty paths/content.
    dirty = bool(git_bytes(root, 'status', '--porcelain=v1', '-z', '--untracked-files=normal',
                           '--ignore-submodules=all'))
    return {'selected_branch': branch, 'selected_revision': revision, 'head_revision': head,
            'head_branch': selected, 'dirty': dirty}


def connection_id(root, branch):
    return hashlib.sha256((str(root)+'\0'+branch).encode()).hexdigest()


def bounded_python_tree(root, revision):
    """Preflight byte/path limits before any graph/cache writes. No blob execution."""
    raw = git_bytes(root, 'ls-tree', '-rz', '-l', revision)
    total, count = 0, 0
    for record in raw.split(b'\0'):
        if not record:
            continue
        header, path_bytes = record.split(b'\t', 1)
        mode, kind, _, size = header.split()
        path = path_bytes.decode('utf-8', errors='strict')
        if mode == b'160000':
            raise ValueError('Submodules require a future explicit ingestion policy')
        parts = PurePosixPath(path).parts
        if any(p in EXCLUDED for p in parts) or not path.endswith('.py'):
            continue
        if (mode not in (b'100644', b'100755') or kind != b'blob' or
            path.startswith('/') or '..' in parts or '\\' in path or
            len(path) > 1024 or any(ord(c) < 32 or ord(c) == 127 for c in path)):
            raise ValueError('Unsupported Python path or non-regular Git blob')
        count += 1
        length = int(size)
        total += length
        if length > 1_000_000 or count > 10000 or total > 16_000_000:
            raise ValueError('Python snapshot exceeds file/count/total byte limits')
    if not count:
        raise ValueError('Require at least one tracked Python file')
    return {'python_files': count, 'python_blob_bytes': total}


def require_clean_selected(state, expected_head):
    if not SHA.fullmatch(expected_head):
        raise ValueError('Expected HEAD must be a full SHA-1 revision')
    if state['selected_revision'] != expected_head or state['head_revision'] != expected_head or state['head_branch'] != state['selected_branch']:
        raise ValueError('HEAD/selected branch changed; explicitly select and confirm the target revision')
    if state['dirty']:
        raise ValueError('Workspace is dirty; commit or separately preserve edits before snapshot refresh')


def metadata(tenant):
    tenant_exists(tenant)
    rows, _ = read(tenant, '''MATCH (m:RepoMetadata) RETURN m.connection_id AS connection_id,
      m.selected_branch AS selected_branch,m.source_revision AS source_revision LIMIT 1''')
    if not rows or not rows[0].get('connection_id'):
        raise ValueError('Snapshot has no local connection; connect into a new tenant first')
    return rows[0]


def validate_connection(root, branch, tenant):
    meta = metadata(tenant)
    if meta['connection_id'] != connection_id(root, branch) or meta['selected_branch'] != branch:
        raise ValueError('Source or branch does not match this snapshot connection')
    return meta


def freshness_check(source, branch, tenant):
    root = allowed_repository(source)
    with writer_locks(str(root), tenant):
        meta = validate_connection(root, branch, tenant)
        state = inspect_workspace(root, branch)
        reasons = []
        if state['selected_revision'] != meta['source_revision']: reasons.append('BRANCH_ADVANCED_OR_REWRITTEN')
        if state['head_branch'] != branch or state['head_revision'] != state['selected_revision']: reasons.append('DIFFERENT_CHECKOUT')
        if state['dirty']: reasons.append('UNCOMMITTED_OR_UNTRACKED_CHANGES')
        status = 'CHANGED' if reasons else 'MATCHED_AT_CHECK'
        now = int(time.time())
        db_manager.get_graph(tenant).query('''MATCH (m:RepoMetadata) SET m.workspace_check_status=$status,
          m.workspace_checked_at=$now,m.workspace_observed_revision=$revision,
          m.workspace_dirty=$dirty,m.workspace_check_reasons=$reasons''',
          {'status':status,'now':now,'revision':state['selected_revision'],'dirty':state['dirty'],'reasons':reasons})
        return {'tenant_graph':tenant,'status':status,'checked_at':now,'reasons':reasons,
                'observed_revision':state['selected_revision'], 'freshness_is_live':False}


def create_snapshot(source, branch, tenant, expected_head, *, previous_tenant=None, expected_base=None):
    if not TENANT_PATTERN.fullmatch(tenant):
        raise ValueError('Tenant must match ^repo_[a-z0-9_]+$')
    root = allowed_repository(source)
    with writer_locks(str(root), tenant):
        if tenant in db_manager.list_tenant_graphs():
            raise ValueError('Tenant already exists; select a new tenant (no overwrite)')
        if previous_tenant:
            prior = validate_connection(root, branch, previous_tenant)
            if not expected_base or prior['source_revision'] != expected_base:
                raise ValueError('Expected base does not match the previous pinned snapshot')
        elif expected_base is not None:
            raise ValueError('Expected base requires a previous snapshot')
        state = inspect_workspace(root, branch)
        require_clean_selected(state, expected_head)
        limits = bounded_python_tree(root, expected_head)
        info = {'connection_kind':'ALLOWLISTED_LOCAL_GIT','connection_id':connection_id(root,branch),
                'selected_branch':branch, 'parent_snapshot':previous_tenant or '',
                'workspace_check_status':'VALIDATING','workspace_checked_at':0,
                'workspace_observed_revision':expected_head,'workspace_dirty':False,
                'workspace_check_reasons':[]}
        created = False
        try:
            stats = _ingest_repo(str(root), tenant, expected_head, False,
                                 snapshot_metadata=info, publish_ready=False)
            created = True
            # Recheck source HEAD, branch and dirty state before publication.
            require_clean_selected(inspect_workspace(root,branch), expected_head)
            now = int(time.time())
            db_manager.get_graph(tenant).query('''MATCH (m:RepoMetadata) SET m.status='READY',
              m.workspace_check_status='MATCHED_AT_CHECK',m.workspace_checked_at=$now''', {'now':now})
            return {**stats,'selected_branch':branch,'parent_snapshot':previous_tenant,
                    'workspace_check_status':'MATCHED_AT_CHECK','workspace_checked_at':now,
                    'freshness_is_live':False,'preflight':limits,
                    'sync_semantics':'NEW_IMMUTABLE_SNAPSHOT_OLD_GRAPH_AND_FINDINGS_UNCHANGED'}
        except Exception:
            if created:
                db_manager.get_graph(tenant).delete()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['connect','check','refresh'])
    parser.add_argument('--source', required=True)
    parser.add_argument('--branch', required=True)
    parser.add_argument('--tenant', required=True, help='New tenant for connect/refresh; existing tenant for check')
    parser.add_argument('--expected-head')
    parser.add_argument('--from-tenant')
    parser.add_argument('--expected-base')
    args = parser.parse_args()
    try:
        if args.operation == 'check':
            if any((args.expected_head,args.from_tenant,args.expected_base)):
                raise ValueError('check does not accept revision/refresh arguments')
            result = freshness_check(args.source,args.branch,args.tenant)
        else:
            if not args.expected_head:
                raise ValueError('connect/refresh requires --expected-head')
            if args.operation == 'refresh' and (not args.from_tenant or not args.expected_base):
                raise ValueError('refresh requires --from-tenant and --expected-base')
            if args.operation == 'connect' and (args.from_tenant or args.expected_base):
                raise ValueError('connect does not accept refresh arguments')
            result = create_snapshot(args.source,args.branch,args.tenant,args.expected_head,
                                     previous_tenant=args.from_tenant,expected_base=args.expected_base)
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        # Subprocess diagnostics may contain source paths/URLs; do not echo them.
        parser.exit(2, ('Workspace operation refused: '+str(exc) if isinstance(exc,ValueError)
                        else 'Workspace operation failed; check local Git access and configuration')+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
