"""Trusted-local Git/AST ingestion. Never import or execute downloaded Python.

Git author identities are unverified; commit-backed PullRequest nodes are transport
compatibility records, not fabricated GitHub PRs or definitive code ownership.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse
from app.db.client import db_manager
from app.ingestion.ast_parser import parse_python_file
from app.ingestion.seed_repos import CACHE
from app.ingestion.dependencies import analyze_dependencies
from app.services.common import TENANT_PATTERN
from app.ingestion.git_safety import git_command, git_environment

EXCLUDED = {'.venv', 'venv', 'node_modules', '.git', 'build', 'dist', '__pycache__', '.tox', '.nox', '.source-cache'}


def git(source, *args):
    return subprocess.check_output([*git_command(), '-C', str(source), *args],
        env=git_environment(), timeout=300).decode('utf-8', errors='replace').rstrip('\n')


def repository_source(source: str, ref: str | None = None):
    """Use a separate immutable checkout; never checkout/reset the user's source tree."""
    parsed = urlparse(source)
    if parsed.scheme:
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Use a public credential-free HTTPS Git URL or a local Git path')
        locator = source
    else:
        path = Path(source).expanduser().resolve()
        if not path.is_dir():
            raise ValueError('Local repository directory does not exist')
        git(path, 'rev-parse', '--git-dir')
        locator = str(path)
    cache = CACHE / 'dynamic' / hashlib.sha256(locator.encode()).hexdigest()[:24]
    cache.parent.mkdir(parents=True, exist_ok=True)
    if not cache.exists():
        subprocess.run([*git_command(), 'clone', '--quiet', '--no-hardlinks', '--',
            locator, str(cache)], env=git_environment(), check=True, timeout=300)
    if ref and ref.startswith('-'):
        raise ValueError('Invalid Git ref')
    # Exact hashes are immutable pins. Branch/tag/default imports must resolve
    # against origin now, not a stale cache branch or detached cache HEAD.
    pinned = bool(ref and len(ref) == 40 and all(c in '0123456789abcdef' for c in ref))
    if pinned:
        try:
            revision = git(cache, 'rev-parse', '--verify', '--end-of-options', ref+'^{commit}')
        except subprocess.CalledProcessError:
            git(cache, 'fetch', '--quiet', 'origin', ref)
            revision = git(cache, 'rev-parse', 'FETCH_HEAD^{commit}')
    else:
        git(cache, 'fetch', '--quiet', 'origin', ref or 'HEAD')
        revision = git(cache, 'rev-parse', 'FETCH_HEAD^{commit}')
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Expected a full Git SHA-1 commit revision')
    git(cache, 'checkout', '--quiet', '--detach', revision)
    # Preserve only safe public HTTPS source URLs; never persist local paths or credentials.
    try:
        origin = locator if parsed.scheme else git(Path(locator), 'config', '--get', 'remote.origin.url')
    except subprocess.CalledProcessError:
        origin = ''
    url = urlparse(origin)
    origin = origin.removesuffix('.git').rstrip('/') if url.scheme == 'https' and url.hostname and not url.username and not url.password and not url.query and not url.fragment else ''
    repository = urlparse(origin).path.strip('/') if origin else Path(locator).name
    return cache, revision, origin, repository


def commit_history(source: Path, revision: str, limit: int = 40, file_paths=None):
    """Bounded real history; --no-renames and NUL records preserve exact paths.

    Path-targeted backfill is separately labeled, not claimed as the global latest 40.
    Merge commits without an ordinary diff have no invented MODIFIES relationships.
    """
    if not 1 <= limit <= 200:
        raise ValueError('history limit must be in 1..200')
    shas = git(source, 'log', '-n', str(limit), '--format=%H', revision, '--', *(file_paths or [])).splitlines()
    records = []
    for sha in shas:
        name, email, timestamp, title = git(source, 'show', '-s', '--format=%an%x00%ae%x00%ct%x00%s', sha).split('\0', 3)
        changes = []
        statuses = {}
        names = git(source, 'show', '--format=', '--name-status', '-z', '--no-renames', sha, '--').split('\0')
        for i in range(0, len(names)-1, 2):
            statuses[names[i+1]] = names[i].strip()
        output = git(source, 'show', '--format=', '--numstat', '-z', '--no-renames', sha, '--')
        for part in output.split('\0'):
            if not part.strip('\n'):
                continue
            fields = part.lstrip('\n').split('\t', 2)
            if len(fields) != 3:
                raise ValueError('Unexpected git numstat record')
            adds, deletes, path = fields
            changes.append({'path': path, 'status': statuses.get(path,'M'), 'additions': int(adds) if adds.isdigit() else 0,
                'deletions': int(deletes) if deletes.isdigit() else 0, 'binary_diff': adds == '-'})
        # A hash identity is NOT a GitHub login; emails need not be exposed/stored.
        author = 'git:' + hashlib.sha256((name+'\0'+email.casefold()).encode()).hexdigest()[:20]
        records.append({'sha': sha, 'author': author, 'name': name, 'timestamp': int(timestamp),
            'title': title, 'changes': changes})
    return records


def append_history(graph, records, origin: str, known: set[str]):
    linked = 0
    for record in records:
        sha = record['sha']
        url = origin+'/commit/'+sha if origin else ''
        graph.query('''MERGE (c:Contributor {login:$author}) SET c.name=$name,
          c.identity_kind='GIT_AUTHOR_UNVERIFIED',c.source_type='GIT_COMMIT_HISTORY'
          MERGE (p:PullRequest {id:$id}) SET p.number=$number,p.title=$title,p.url=$url,
          p.source_type='GIT_COMMIT_HISTORY',p.record_kind='COMMIT',p.commit_sha=$sha,
          p.committed_at=$timestamp,p.state='COMMITTED'
          MERGE (c)-[r:AUTHORED]->(p) SET r.source_type='GIT_COMMIT_HISTORY' ''',
          {'author':record['author'], 'name':record['name'], 'id':'git:'+sha,
           'number':-int(sha[:12],16), 'title':record['title'], 'url':url,
           'sha':sha, 'timestamp':record['timestamp']})
        for change in record['changes']:
            graph.query('''MATCH (p:PullRequest {id:$id})
              MERGE (c:CommitFileChange {id:$change_id}) SET c.path=$path,c.status=$status,
              c.additions=$additions,c.deletions=$deletions,c.binary_diff=$binary_diff,c.commit_sha=$sha
              MERGE (p)-[:CHANGED]->(c)''',
              {'id':'git:'+sha,'change_id':sha+':'+change['path'],'sha':sha,
               'status':change.get('status','M'),**change})
            if change['path'] not in known:
                continue
            graph.query('''MATCH (p:PullRequest {id:$id}),(f:File {path:$path})
              MERGE (p)-[r:MODIFIES]->(f) SET r.additions=$additions,r.deletions=$deletions,
              r.binary_diff=$binary_diff,r.source_type='GIT_COMMIT_HISTORY',r.commit_sha=$sha''',
              {'id':'git:'+sha, 'sha':sha, **change})
            linked += 1
    return linked


def imports_for(item, known):
    return sorted(analyze_dependencies(item, known, set())[0] - {item['file']['path']})


def batch(graph, query, rows):
    for offset in range(0, len(rows), 250):
        graph.query(query, {'rows':rows[offset:offset+250]})


def demo_policies(graph, paths):
    now = int(time.time())
    for index, path in enumerate(paths):
        pair = f'demo_{graph.name}_{index}'
        for suffix, status, rule, vf, vt in [('old','SUPERSEDED','Demo: unbounded discovery reads allowed.',now-7200,now-3600),
            ('active','ACTIVE','Demo: discovery reads must be read-only and bounded.',now-3600,0)]:
            graph.query('''MATCH (f:File {path:$path}) CREATE (d:Decision {id:$id,
              scope_symbol:'module_root',rule:$rule,status:$status,valid_from:$vf,valid_to:$vt,
              recorded_from:$now,recorded_to:0,recorded_at:$now,time_basis:'DEMO_SCENARIO_CLOCK',
              source_type:'DEMO_POLICY_SCENARIO',source_url:$url,
              rationale:'Fictional opt-in local demo; not an upstream engineering policy.',
              embedding:vecf32($embedding)}) CREATE (d)-[:GOVERNS]->(f)''',
              {'path':path,'id':pair+'_'+suffix,'rule':rule,'status':status,'vf':vf,'vt':vt,'now':now,
               'url':'https://github.com/nakulmaurya/ChronosGraph/blob/build/t05-real-world-repos/backend/app/ingestion/ingest_repo.py',
               'embedding':db_manager.embed_text(rule)})
        graph.query('MATCH (a:Decision {id:$a}),(o:Decision {id:$o}) CREATE (a)-[:SUPERSEDED]->(o)',
            {'a':pair+'_active','o':pair+'_old'})


def snapshot_stats(tenant):
    graph = db_manager.get_graph(tenant)
    stats = {'tenant_graph':tenant}
    for label, key in [(None,'nodes'),('File','files'),('Function','functions'),('Class','classes'),
                       ('Contributor','contributors'),('PullRequest','indexed_records')]:
        pattern = '(n)' if label is None else '(n:'+label+')'
        stats[key] = graph.ro_query('MATCH '+pattern+' RETURN count(n)').result_set[0][0]
    stats['edges'] = graph.ro_query('MATCH ()-[r]->() RETURN count(r)').result_set[0][0]
    return stats


@contextmanager
def writer_locks(source, tenant):
    source_identity = source if urlparse(source).scheme else str(Path(source).expanduser().resolve())
    locks = [db_manager.db.connection.lock('chronosgraph:ingest:'+tenant, timeout=1800, blocking_timeout=0),
        db_manager.db.connection.lock('chronosgraph:source:'+hashlib.sha256(source_identity.encode()).hexdigest(),
            timeout=1800, blocking_timeout=60)]
    acquired = []
    try:
        for index, lock in enumerate(locks):
            if not lock.acquire(blocking=index > 0):
                raise ValueError('Another ingestion is using this tenant or source cache')
            acquired.append(lock)
        yield
    finally:
        for lock in reversed(acquired):
            lock.release()


def ingest_repo(source: str, tenant: str, ref: str | None = None, seed_demo_policies: bool = False):
    if not TENANT_PATTERN.fullmatch(tenant):
        raise ValueError('Tenant must match ^repo_[a-z0-9_]+$')
    with writer_locks(source, tenant):
        return _ingest_repo(source, tenant, ref, seed_demo_policies)


def _ingest_repo(source, tenant, ref, seed_demo_policies, *, snapshot_metadata=None, publish_ready=True, prepared_snapshot=None):
    created = False
    try:
        if tenant in db_manager.list_tenant_graphs():
            raise ValueError('Tenant already exists; use a new tenant name (no implicit destructive reset)')
        if prepared_snapshot is None:
            root, revision, origin, repository = repository_source(source, ref)
        else:
            root, revision, origin, repository = prepared_snapshot["source"]
        paths = sorted(p for p in (git(root, 'ls-files', '-z', '*.py').split('\0') if prepared_snapshot is None else prepared_snapshot['paths']) if p and
            not any(part in EXCLUDED for part in Path(p).parts) and not (root/p).is_symlink())
        if not paths or len(paths) > 10000:
            raise ValueError('Require 1..10000 tracked Python files')
        items = [parse_python_file(root/path, relative_to=root) for path in paths]
        errors = [{'path':i['file']['path'],'errors':i['errors']} for i in items if i['errors']]
        known = set(paths)
        definitions = {f['qualified_name'] for item in items for f in item['functions']}
        imports, calls, unresolved = [], [], 0
        for item in items:
            targets, resolved, unknown = analyze_dependencies(item, known, definitions)
            imports += [{'source':item['file']['path'],'target':p} for p in sorted(targets)]
            calls += [{'source':call['caller'],'target':target,'line':call['line']} for call, target in resolved]
            unresolved += len(unknown)
        from app.ingestion.inventory import records as inventory_records
        if prepared_snapshot is None:
            entries=[]
            for record in git(root,'ls-tree','-r','-l','-z',revision,'--').split('\0'):
                if not record:continue
                header,path=record.split('\t',1)
                mode,kind,sha,size=header.split()
                entries.append({'path':path,'mode':mode,'sha':sha,'size':int(size) if size.isdigit() else 0})
        else:
            entries=prepared_snapshot.get('inventory',[{'path':path,'size':(root/path).stat().st_size} for path in paths])
        inventory=inventory_records(entries,revision,origin,{i['file']['path']:i for i in items})
        history = commit_history(root,revision) if prepared_snapshot is None else []
        graph = db_manager.get_graph(tenant)
        graph.query('''CREATE (:RepoMetadata {repository:$repository,source_url:$url,
          source_revision:$revision,status:'INGESTING',source_type:'GIT_AST_SNAPSHOT'})''',
          {'repository':repository,'url':origin,'revision':revision})
        created = True
        if snapshot_metadata:
            graph.query('MATCH (m:RepoMetadata) SET m += $metadata', {'metadata':snapshot_metadata})
        db_manager.ensure_indexes(tenant)
        batch(graph, '''UNWIND $rows AS r CREATE (f:File) SET f=r''',
            [{**item['file'],'source_revision':revision,'source_url':origin+'/blob/'+revision+'/'+item['file']['path'] if origin else '',
              'source_type':'GIT_AST_SNAPSHOT','parse_error_count':len(item['errors'])} for item in items])
        batch(graph, 'UNWIND $rows AS r CREATE (f:TrackedFile) SET f=r', inventory)
        graph.query('MATCH (t:TrackedFile),(f:File) WHERE t.path=f.path MERGE (t)-[:HAS_ANALYSIS]->(f)')
        for label, key in [('Class','classes'),('Function','functions')]:
            batch(graph, f'''UNWIND $rows AS r MATCH (f:File {{path:r.file_path}})
              MERGE (n:{label} {{qualified_name:r.qualified_name}}) SET n+=r
              MERGE (f)-[:DEFINES]->(n)''', [f for item in items for f in item[key]])
        batch(graph, '''UNWIND $rows AS r MATCH (a:File {path:r.source}),(b:File {path:r.target})
          MERGE (a)-[:IMPORTS]->(b)''', imports)
        batch(graph, '''UNWIND $rows AS r MATCH (a:Function {qualified_name:r.source}),(b:Function {qualified_name:r.target})
          MERGE (a)-[c:CALLS {line:r.line}]->(b) SET c.resolution='conservative_static' ''', calls)
        # FalkorDB returns no rows for an absent relationship type. At this stage
        # File-to-File edges are exclusively IMPORTS; NULL handles the edgeless
        # File projection natively rather than inventing Python fallback scores.
        relation = "'IMPORTS'" if imports else "NULL"
        ranking = graph.ro_query(f"CALL algo.pageRank('File',{relation}) YIELD node,score RETURN node.path,score").result_set
        total = sum(score for _, score in ranking)
        if not ranking or total <= 0 or not all(math.isfinite(score) and score>=0 for _,score in ranking):
            raise ValueError('Native PageRank did not produce valid scores')
        batch(graph, '''UNWIND $rows AS r MATCH (f:File {path:r.path})
          SET f.pagerank=r.score,f.pagerank_method='native_falkordb_pagerank_normalized' ''',
          [{'path':path,'score':score/total} for path,score in ranking])
        from app.ingestion.repo_rules import enrich_repository
        extracted_rules = enrich_repository(graph,root,revision,origin,paths)
        from app.ingestion.codeowners import index_codeowners
        declared_ownership = index_codeowners(graph,root,revision,origin,known,
            document=prepared_snapshot["ownership_document"] if prepared_snapshot else None)
        from app.ingestion.organization import index_organization
        organization = index_organization(graph,root,revision,origin,known) if prepared_snapshot is None else {
            'status':'NOT_INDEXED_ARCHIVE_IMPORT','decisions':0}
        linked = append_history(graph,history,origin,known)
        policy_paths = []
        if seed_demo_policies:
            # Prefer high-PageRank files with actual bounded history coverage. Never
            # invent an author or give all files policies just to force a replay.
            candidates = graph.ro_query('''MATCH (p:PullRequest)-[:MODIFIES]->(f:File)
              RETURN DISTINCT f.path,f.pagerank ORDER BY f.pagerank DESC,f.path''').result_set
            policy_paths = [p for p,_ in candidates[:min(4,max(0,len(paths)-2))]]
            if not policy_paths:
                policy_paths = [p for p,_ in sorted(ranking,key=lambda r:(-r[1],r[0]))[:min(4,max(0,len(paths)-2))]]
            demo_policies(graph,policy_paths)
        graph.query('''MATCH (m:RepoMetadata) SET m.status=$status,m.pagerank_method='native_falkordb_pagerank_normalized',
          m.parse_errors_json=$errors,m.history_limit=$history_limit,m.history_scope=$history_scope,
          m.inventory_count=$inventory,m.unresolved_calls=$unresolved,m.seeded_policy_files=$paths,m.ingested_at=$now''',
          {'status':'READY' if publish_ready else 'VALIDATING_WORKSPACE',
           'inventory':len(inventory),'errors':json.dumps(errors),'unresolved':unresolved,'paths':policy_paths,'now':int(time.time()),
           'history_limit':40 if prepared_snapshot is None else 0,
           'history_scope':'latest_commits_at_source_revision' if prepared_snapshot is None else 'NOT_FETCHED_GITHUB_ARCHIVE'})
        return {**snapshot_stats(tenant),'repository':repository,'source_revision':revision,
            'declared_ownership':declared_ownership,'organization':organization,
            'extracted_repository_rules':extracted_rules,'resolved_calls':len(calls),'unresolved_calls':unresolved,'parse_errors':errors,
            'history_records':len(history),'history_file_links':linked,'policy_files':policy_paths,
            'pagerank_method':'native_falkordb_pagerank_normalized',
            'ownership_limit':'Bounded Git author evidence, not verified maintainers or exhaustive ownership.'}
    except Exception:
        if created:
            db_manager.get_graph(tenant).delete()  # Only this newly created failed graph.
        raise


def backfill_history(source, tenant, ref=None, file_paths=None):
    """Append-only provenance enrichment. No File, rule or source revision is reset."""
    from app.services.common import tenant_exists, tenant_lock
    tenant_exists(tenant)
    with writer_locks(source, tenant):
        root, revision, origin, _ = repository_source(source,ref)
        graph = db_manager.get_graph(tenant)
        known = {r[0] for r in graph.ro_query('MATCH (f:File) RETURN f.path').result_set}
        revisions = {r[0] for r in graph.ro_query('MATCH (f:File) RETURN DISTINCT f.source_revision').result_set}
        if revision not in revisions or (file_paths and not set(file_paths)<=known):
            raise ValueError('Backfill must match this graph source revision and existing file paths')
        records = commit_history(root,revision,file_paths=file_paths)
        with tenant_lock(tenant):
            linked = append_history(graph,records,origin,known)
        return {'tenant_graph':tenant,'source_revision':revision,'history_records':len(records),
            'history_file_links':linked,'history_scope':'path_targeted' if file_paths else 'latest_40_commits',
            'file_paths':file_paths or [],'source_type':'GIT_COMMIT_HISTORY'}


def enrich_utility(source, tenant, ref=None):
    """Append exact source measurements/rules to a matching snapshot, never reset it."""
    from app.services.common import tenant_exists, tenant_lock
    tenant_exists(tenant)
    with writer_locks(source,tenant):
        root, revision, origin, _ = repository_source(source,ref)
        graph = db_manager.get_graph(tenant)
        files = graph.ro_query('MATCH (f:File) RETURN f.path,f.sha256,f.source_revision').result_set
        if not files or any(r[2]!=revision for r in files):
            raise ValueError('Utility enrichment must match every File source revision')
        items = []
        for path, sha, _ in files:
            p = root/path
            if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(root.resolve()):
                raise ValueError('Unsafe or missing snapshot file')
            item = parse_python_file(p,relative_to=root)['file']
            if item['sha256']!=sha:
                raise ValueError('Source hash mismatch; no utility metadata written')
            items.append(item)
        with tenant_lock(tenant):
            batch(graph,"""UNWIND $rows AS r MATCH (f:File {path:r.path})
                SET f.source_text=r.source_text,f.source_chars=r.source_chars,f.source_utf8_bytes=r.source_utf8_bytes""",items)
            from app.ingestion.repo_rules import enrich_repository
            count = enrich_repository(graph,root,revision,origin,[r[0] for r in files])
        return {'tenant_graph':tenant,'source_revision':revision,'measured_files':len(items),'extracted_rules':count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True)
    parser.add_argument('--tenant',required=True)
    parser.add_argument('--ref')
    parser.add_argument('--seed-demo-policies',action='store_true')
    parser.add_argument('--enrich-utility',action='store_true',help='Append exact source sizes and source-linked constraints to a matching snapshot')
    parser.add_argument('--backfill-history',action='store_true',help='Append history to an existing graph, never replace it')
    parser.add_argument('--history-path',action='append',help='Path-targeted history for explicit backfill only')
    args = parser.parse_args()
    if args.history_path and not args.backfill_history:
        parser.error('--history-path requires --backfill-history')
    if args.enrich_utility and args.backfill_history:
        parser.error('Choose one enrichment mode')
    if args.enrich_utility:
        result = enrich_utility(args.source,args.tenant,args.ref)
    elif args.backfill_history:
        result = backfill_history(args.source,args.tenant,args.ref,args.history_path)
    else:
        result = ingest_repo(args.source,args.tenant,args.ref,args.seed_demo_policies)
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
