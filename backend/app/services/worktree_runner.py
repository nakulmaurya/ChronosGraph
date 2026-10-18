"""Explicit operator opt-in execution of TRUSTED local repo tests, not a sandbox.

No path or shell command is accepted from HTTP/MCP. Tenant-to-checkout mapping is
operator configuration, matched to the saved connection. Do not enable on public
or shared hosting: pytest executes arbitrary repository code with host privileges.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
from fastapi import HTTPException
from pydantic import BaseModel, Field
from app.db.client import db_manager
from app.ingestion.git_safety import git_command, git_environment
from app.ingestion.workspace import allowed_repository, connection_id
from app.services.common import read
from app.services.change_lifecycle import _node, _fresh, _record_execution, ExecutionInput
from app.services.mutation_guard import mutation_guard, require_lease


class WorktreeInput(BaseModel):
    tenant_graph: str
    expected_revision: str = Field(pattern=r'^[0-9a-f]{40}$')
    proposal_hash: str = Field(pattern=r'^[0-9a-f]{64}$')
    idempotency_key: str = Field(min_length=1, max_length=128)
    acknowledge_code_execution: bool = False


def configured_root(tenant):
    if os.environ.get('CHRONOSGRAPH_ENABLE_WORKTREE_EXECUTION') != '1':
        raise HTTPException(403, 'Trusted local test execution is disabled by the operator')
    try:
        mapping = json.loads(os.environ.get('CHRONOSGRAPH_EXECUTION_REPOSITORIES', '{}'))
        root = allowed_repository(mapping[tenant])
    except (ValueError, KeyError, TypeError, OSError):
        raise HTTPException(403, 'No allowlisted operator-owned local checkout for this saved version') from None
    rows, _ = read(tenant, '''MATCH (m:RepoMetadata) RETURN m.connection_kind AS kind,
        m.connection_id AS connection,m.selected_branch AS branch LIMIT 1''')
    if not rows or rows[0]['kind'] != 'ALLOWLISTED_LOCAL_GIT' or rows[0]['connection'] != connection_id(root, rows[0]['branch']):
        raise HTTPException(403, 'Execution checkout does not match the selected local connection')
    return root


def capabilities(tenant):
    try:
        configured_root(tenant)
        return {'enabled': True, 'scope': 'TRUSTED_LOCAL_CHECKOUT_TESTS_EXECUTE_HOST_CODE'}
    except HTTPException:
        return {'enabled': False, 'scope': 'OPERATOR_OPT_IN_AND_EXACT_LOCAL_CONNECTION_REQUIRED'}


def _run_pytest(worktree, tests):
    # No shell, no client commands, sanitized environment; still not code isolation.
    env = {'PATH': os.path.dirname(sys.executable) + os.pathsep + '/usr/bin:/bin',
           'HOME': str(worktree), 'LANG': 'C.UTF-8', 'PYTHONPATH': str(worktree),
           'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
    command = [sys.executable, '-m', 'pytest', '--', *tests]
    process = subprocess.Popen(command, cwd=worktree, env=env, stdin=subprocess.DEVNULL,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
    excerpt = bytearray()
    def drain():
        while True:
            chunk = process.stdout.read(4096)
            if not chunk:
                return
            excerpt.extend(chunk[:max(0, 24000-len(excerpt))])
    reader = threading.Thread(target=drain, daemon=True); reader.start()
    timed_out = False
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        timed_out = True
    finally:
        # Reap descendants in the process group even if pytest exited first.
        try: os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        process.wait();reader.join(timeout=2)
        process.stdout.close()
    text = excerpt.decode('utf-8', errors='replace')[:7800]
    if timed_out:
        text += '\nStopped: 30-second timeout.'
    return (124 if timed_out else process.returncode), text[:8000]


def verify_candidate_tree(worktree, proposal, bodies):
    """Runner observation, separate from a plugin-declared digest. No test approval minted."""
    from app.services.change_lifecycle import digest
    manifest = proposal.get('candidate_manifest_json')
    if not manifest:
        return 'LEGACY_UNAVAILABLE'
    manifest = json.loads(manifest)
    for entry in manifest['entries']:
        path = worktree / entry['path']
        if path.is_symlink():
            raise HTTPException(409, 'Candidate became a symlink')
        observed = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if observed != entry['result_sha256']:
            raise HTTPException(409, 'Materialized candidate differs from immutable proposal: '+entry['path'])
    def names(*args):
        return subprocess.check_output([*git_command(),'-C',str(worktree),*args],env=git_environment(),timeout=10).decode().split('\0')
    changed = names('diff','--no-ext-diff','--no-textconv','--name-only','--no-renames','-z','HEAD','--')
    changed += names('ls-files','--others','--exclude-standard','-z')
    # Explicitly generated pytest cache is not a proposed source file.
    extra = [p for p in changed if p and p not in bodies and '.pytest_cache' not in p.split('/') and '__pycache__' not in p.split('/')]
    if extra:
        raise HTTPException(409, 'Unexpected changes outside tested candidate: '+', '.join(sorted(extra)[:20]))
    observed_digest = digest(manifest)
    if observed_digest != proposal['candidate_digest']:
        raise HTTPException(409, 'Runner candidate digest mismatch')
    return observed_digest


def execute(proposal_id, req: WorktreeInput):
    if not req.acknowledge_code_execution:
        raise HTTPException(422, 'Confirm that candidate pytest executes trusted repository code on this machine')
    root = configured_root(req.tenant_graph)
    with mutation_guard(req.tenant_graph) as lease:
        p = _node(req.tenant_graph, 'ChangeProposal', proposal_id)
        if _fresh(req.tenant_graph, p, req.expected_revision):
            raise HTTPException(409, p['status'])
        if req.proposal_hash != p.get('approved_proposal_hash') or req.proposal_hash != p['proposal_hash']:
            raise HTTPException(409, 'Exact human approval is required')
        # A retained observed receipt is returned without running repository code twice.
        prior, _ = read(req.tenant_graph, '''MATCH (e:ExecutionRecord {idempotency_key:$key}) RETURN e''', {'key': req.idempotency_key})
        if prior:
            e = dict(prior[0]['e'].properties)
            if e['proposal_id'] != proposal_id or e['proposal_hash'] != req.proposal_hash or e['provenance_kind'] != 'LOCAL_WORKTREE_OBSERVED':
                raise HTTPException(409, 'Execution key belongs to different inputs')
            return e
        if p['status'] != 'APPROVED':
            raise HTTPException(409, 'Proposal is not approved')
        attempts, _ = read(req.tenant_graph, '''MATCH (a:ExecutionAttempt) OPTIONAL MATCH (owner:ChangeProposal)-[:HAS_ATTEMPT]->(a) WITH a,owner WHERE a.idempotency_key=$key OR owner.id=$id RETURN a.id AS id''', {'key': req.idempotency_key, 'id': proposal_id})
        if attempts:
            raise HTTPException(409, 'Execution already started for this proposal or key; outcome unknown. Inspect records before any new run')
        impact = json.loads(p['impact_summary_json'])
        tests = [path for path in impact['impacted_test_files']
                 if json.loads(p['proposed_files_json']).get(path, 'present') is not None]
        if not tests:
            raise HTTPException(422, 'No runnable candidate tests; no command executed')
        def git(*args):
            return subprocess.check_output([*git_command(), '-C', str(root), *args], env=git_environment(),
                                           stderr=subprocess.PIPE, timeout=10)
        if git('rev-parse', 'HEAD').decode().strip() != req.expected_revision or git('status', '--porcelain'):
            raise HTTPException(409, 'Local checkout changed or is dirty; create and select a new snapshot')
        entries = git('ls-tree', '-rz', req.expected_revision).split(b'\0')
        if any(row and row.split(b' ',1)[0] not in (b'100644',b'100755') for row in entries):
            raise HTTPException(422, 'Trusted runner refuses symlinks/submodules in the base tree')
        # Local checkout is explicitly trusted, including its Git configuration.
        # Refuse configured checkout filters instead of invoking arbitrary smudge programs.
        try:
            filters = git('config', '--get-regexp', r'^filter\..*\.(smudge|process)$')
        except subprocess.CalledProcessError as exc:
            if exc.returncode != 1: raise
            filters = b''
        if filters:
            raise HTTPException(422, 'Runner refuses repositories with configured checkout filters')
        require_lease(lease)
        db_manager.query(req.tenant_graph, '''MATCH (p:ChangeProposal {id:$id})
            CREATE (p)-[:HAS_ATTEMPT]->(:ExecutionAttempt {id:$attempt,idempotency_key:$key,
                status:'STARTED_OUTCOME_UNKNOWN',proposal_hash:$hash})''',
            {'id': proposal_id, 'attempt': 'attempt_'+req.idempotency_key, 'key': req.idempotency_key, 'hash': req.proposal_hash})
        bodies = json.loads(p['proposed_files_json'])
        with tempfile.TemporaryDirectory(prefix='chronos-approved-') as tmp:
            worktree = Path(tmp)/'checkout'
            try:
                git('worktree', 'add', '--detach', str(worktree), req.expected_revision)
                for path, expected in json.loads(p['base_file_shas_json']).items():
                    target = worktree/path
                    actual = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
                    if actual != expected:
                        raise HTTPException(409, 'Worktree base file hash mismatch')
                for path, text in bodies.items():
                    target = worktree/path
                    if text is None: target.unlink()
                    else: target.parent.mkdir(parents=True, exist_ok=True);target.write_text(text, encoding='utf-8')
                verify_candidate_tree(worktree,p,bodies)
                require_lease(lease)
                code, output = _run_pytest(worktree, tests)
                verify_candidate_tree(worktree,p,bodies)
                # Revalidate after the real subprocess; a changed policy cannot be promoted.
                if _fresh(req.tenant_graph, p, req.expected_revision):
                    raise HTTPException(409, p['status'])
                require_lease(lease)
                return _record_execution(proposal_id, ExecutionInput(tenant_graph=req.tenant_graph,
                    expected_revision=req.expected_revision, proposal_hash=req.proposal_hash,
                    command_executed=impact['recommended_pytest_command'], exit_code=code,
                    output_excerpt=output, idempotency_key=req.idempotency_key,
                    create_finding_summary='Candidate test result: '+p['task_title']),
                    'LOCAL_WORKTREE_OBSERVED', 'TRUSTED_LOCAL_OPERATOR_RUNNER', req.expected_revision, lease=lease)
            finally:
                if worktree.exists():
                    git('worktree', 'remove', '--force', str(worktree))
