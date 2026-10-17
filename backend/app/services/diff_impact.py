"""Full-file Python replacement in disposable graphs, separate from legacy overlays.

Rebuild static CALLS from captured source after replacements (including inbound
callers). Never execute code, apply a patch to disk, or mutate the base tenant.
"""
from __future__ import annotations
import hashlib
import shlex
import uuid
from pathlib import PurePosixPath
from fastapi import HTTPException
from app.db.client import db_manager
from app.ingestion.ast_parser import parse_python_source
from app.ingestion.ingest_repo import batch
from app.services.ast_patch import analyze_dependencies
from app.services.common import tenant_exists, tenant_lock
from app.services.unified_patch import patch_source

SOURCE = 'AST_DIFF_REPLACEMENT_SIMULATION'
MAX_SOURCE_BYTES = 16_000_000


def safe_path(value):
    if (not isinstance(value, str) or not value or len(value) > 1024
        or any(ord(c) < 32 for c in value) or '\\' in value or '"' in value
        or value.startswith('/') or ':' in value
        or any(p in ('', '.', '..', '.git') for p in value.split('/'))
        or PurePosixPath(value).suffix != '.py'):
        raise HTTPException(422, 'Expected a relative, traversal-free Python path')
    return value


def _header_path(value, prefix):
    value = value.rstrip('\r\n').split('\t', 1)[0]
    if value == '/dev/null':
        return None
    if not value.startswith(prefix):
        raise HTTPException(422, 'Unified diff requires a/ and b/ path prefixes')
    return safe_path(value[len(prefix):])


def reconstruct(patch, sources):
    """Return old/new/final source tuples; strict hunks checked by existing parser.

    Git's quoted paths/binary patches/mode-only changes are intentionally rejected.
    A pure rename must carry matching rename metadata and similarity index 100%.
    """
    if len(patch.encode('utf-8')) > 128000:
        raise HTTPException(422, 'Diff is limited to 128000 UTF-8 bytes')
    lines = patch.splitlines(keepends=True)
    starts = [i for i, line in enumerate(lines) if line.startswith('diff --git ')]
    if not starts:
        starts = [0]
    elif starts[0] != 0:
        raise HTTPException(422, 'Unexpected text before diff')
    changes = []
    for start, end in zip(starts, starts[1:] + [len(lines)]):
        section = lines[start:end]
        old = new = None
        h = next((i for i, line in enumerate(section) if line.startswith('--- ')), None)
        if h is None:
            old_line = [x[len('rename from '):].rstrip('\r\n') for x in section if x.startswith('rename from ')]
            new_line = [x[len('rename to '):].rstrip('\r\n') for x in section if x.startswith('rename to ')]
            if (len(old_line) != 1 or len(new_line) != 1
                or 'similarity index 100%\n' not in section or len(section) != 4):
                raise HTTPException(422, 'Require complete textual hunks or a 100% pure rename')
            old, new = safe_path(old_line[0]), safe_path(new_line[0])
            final = sources.get(old)
            if final is None:
                raise HTTPException(422, 'Missing captured source for rename')
        else:
            if h + 1 >= len(section) or not section[h+1].startswith('+++ '):
                raise HTTPException(422, 'Missing paired diff headers')
            old = _header_path(section[h][4:], 'a/')
            new = _header_path(section[h+1][4:], 'b/')
            allowed = ('diff --git ', 'index ', 'new file mode ', 'deleted file mode ',
                       'similarity index ', 'rename from ', 'rename to ')
            if any(x.startswith(('new file mode ', 'deleted file mode ')) and x.strip().split()[-1] not in ('100644', '100755') for x in section[:h]):
                raise HTTPException(422, 'Symlink and nonregular file modes are unsupported')
            if any(not x.startswith(allowed) for x in section[:h]):
                raise HTTPException(422, 'Unsupported diff metadata')
            if old is None and new is None:
                raise HTTPException(422, 'Diff must name a source or destination')
            if old is not None and old not in sources:
                raise HTTPException(422, 'Diff baseline is not captured in this graph')
            # Reuse exact hunk/context verification, normalizing only path headers.
            path = old or new
            normalized = f'--- a/{path}\n+++ b/{path}\n' + ''.join(section[h+2:])
            final, _ = patch_source(normalized, path, sources[old] if old else '')
            if new is None and final != '':
                raise HTTPException(422, 'Deleted file patch must remove the complete source')
        if section and section[0].startswith('diff --git '):
            # Header disagreement is rejected, including quoted paths.
            expected = f'diff --git a/{old or new} b/{new or old}'
            if section[0].rstrip('\r\n') != expected:
                raise HTTPException(422, 'Git diff paths disagree with file headers')
        changes.append((old, new, final if new else None))
    return changes


def _validate_changes(changes, sources):
    if not 1 <= len(changes) <= 20:
        raise HTTPException(422, 'Require 1..20 changed Python files')
    old_paths = [old for old, _, _ in changes if old is not None]
    new_paths = [new for _, new, _ in changes if new is not None]
    if len(set(old_paths)) != len(old_paths) or len(set(new_paths)) != len(new_paths):
        raise HTTPException(422, 'Duplicate source or destination path')
    # Rename chains/swaps are deliberately unsupported: do not guess their order.
    for old, new, final in changes:
        if old is not None and old not in sources:
            raise HTTPException(422, 'Cannot delete or replace an absent captured file')
        if new is not None and new != old and new in sources:
            raise HTTPException(422, 'Added/renamed destination already exists')
        if new is not None:
            safe_path(new)
            if len(final.encode('utf-8')) > 1_000_000:
                raise HTTPException(422, 'Final file exceeds 1 MB')
            parsed = parse_python_source(final, new)
            if sum(len(parsed[key]) for key in ('functions', 'classes', 'imports', 'calls')) > 10000:
                raise HTTPException(422, 'Final file exceeds 10000 AST observations')
            if parsed['errors']:
                raise HTTPException(422, {'message': 'Invalid final Python source', 'path': new, 'errors': parsed['errors']})
    return changes


def _blast(graph, paths):
    impacted = set(paths)
    for query in [
        '''MATCH (f:File) WHERE f.path IN $paths OPTIONAL MATCH (d:File)-[:IMPORTS*1..3]->(f)
           RETURN DISTINCT d.path''',
        '''MATCH (f:File)-[:DEFINES]->(target:Function) WHERE f.path IN $paths
           MATCH (caller:Function)-[:CALLS*1..3]->(target) RETURN DISTINCT caller.file_path''',
    ]:
        impacted.update(row[0] for row in graph.ro_query(query, {'paths': paths}).result_set if row[0])
    return impacted


def _semantic_dependencies(items):
    known = set(items)
    definitions = {f['qualified_name'] for item in items.values() for f in item['functions']}
    resolved = {path: analyze_dependencies(item, known, definitions) for path, item in items.items()}
    edges = {('IMPORTS', path, target) for path, (imports, _, _) in resolved.items() for target in imports}
    edges.update(('CALLS', call['caller'], target) for _, calls, _ in resolved.values() for call, target in calls)
    return resolved, edges


def _source_impact(edges, paths):
    """Pre-state reachability from captured syntax, including old index gaps."""
    impacted = set(paths)
    for kind in ('IMPORTS', 'CALLS'):
        frontier = set(paths) if kind == 'IMPORTS' else {b for k, _, b in edges if k == kind and b.split(':', 1)[0] in paths}
        for _ in range(3):
            frontier = {a for k, a, b in edges if k == kind and b in frontier}
            impacted.update(name.split(':', 1)[0] for name in frontier)
    return impacted


def dependency_view(dependencies, impacted, present, changed):
    """Only evidenced File IMPORTS edges inside the candidate impact set."""
    candidates = sorted(set(impacted) & set(present), key=lambda p: (p not in changed, p))
    paths = candidates[:30]
    ids = set(paths)
    links = sorted((a, b) for kind, a, b in dependencies if kind == 'IMPORTS' and a in ids and b in ids)
    return {'paths': paths, 'edges': [{'source': a, 'target': b} for a, b in links[:120]],
            'nodes_total': len(candidates), 'nodes_truncated': len(candidates) > 30,
            'edges_truncated': len(links) > 120,
            'scope': 'Captured-source static IMPORTS within candidate impacted files; no runtime or invented adjacency'}


def simulate_diff(req):
    tenant = tenant_exists(req.tenant_graph)
    with tenant_lock(tenant):
        if req.expected_revision is not None:
            from app.services.agent_connection import require_snapshot
            require_snapshot(tenant, req.expected_revision)
        base = db_manager.get_graph(tenant)
        captured = base.ro_query('MATCH (f:File) RETURN f.path,f.source_text,f.sha256,f.source_revision LIMIT 10001').result_set
        if not captured or len(captured) > 10000 or any(r[1] is None for r in captured):
            raise HTTPException(422, 'Replacement requires 1..10000 files with captured source; enrich first')
        if any(sha != hashlib.sha256(text.encode('utf-8')).hexdigest() for _, text, sha, _ in captured):
            raise HTTPException(409, 'Captured source hash mismatch; refresh the snapshot before diffing')
        sources = {p: text for p, text, _, _ in captured}
        if sum(len(t.encode('utf-8')) for t in sources.values()) > MAX_SOURCE_BYTES:
            raise HTTPException(422, 'Captured source exceeds the 16 MB replacement-analysis budget')
        if req.unified_diff is not None:
            changes = reconstruct(req.unified_diff, sources)
        else:
            changes = [(p if p in sources else None, p if text is not None else None, text)
                       for p, text in req.file_bodies.items()]
            # Keep deleted paths even for invalid deletion of an unknown file.
            for p, text in req.file_bodies.items():
                safe_path(p)
                if text is None and p not in sources:
                    raise HTTPException(422, 'Cannot delete an absent file')
        _validate_changes(changes, sources)
        changed_paths = sorted({p for old, new, _ in changes for p in (old, new) if p})
        old_items = {p: parse_python_source(text, p) for p, text in sources.items()}
        _, before_dependencies = _semantic_dependencies(old_items)
        before_impact = _blast(base, changed_paths) | _source_impact(before_dependencies, changed_paths)
        final_sources = dict(sources)
        for old, new, text in changes:
            if old:
                del final_sources[old]
            if new:
                final_sources[new] = text
        if sum(len(t.encode('utf-8')) for t in final_sources.values()) > MAX_SOURCE_BYTES:
            raise HTTPException(422, 'Final source exceeds the 16 MB analysis budget')
        items = {p: parse_python_source(s, p) for p, s in final_sources.items()}
        old_symbols = {f['qualified_name']: (f['signature'], f['is_async']) for p, i in old_items.items() if p in changed_paths for f in i['functions']}
        new_symbols = {f['qualified_name']: (f['signature'], f['is_async']) for p, i in items.items() if p in changed_paths for f in i['functions']}
        broken_symbols = {name for name, sig in old_symbols.items() if new_symbols.get(name) != sig}
        broken_callers = sorted({a for kind, a, b in before_dependencies if kind == 'CALLS' and b in broken_symbols})
        resolved, after_dependencies = _semantic_dependencies(items)
        simulation = 'diff_' + uuid.uuid4().hex
        with db_manager.ephemeral_sandbox(tenant) as (graph, name, clone_ms):
            # Reparse callers too, so removing/renaming a definition cannot preserve
            # an invalid inbound edge and newly introduced symbols become resolvable.
            graph.query('MATCH ()-[r:CALLS]->() DELETE r')
            graph.query('''MATCH (f:File)-[:DEFINES]->(n) WHERE f.path IN $paths AND (n:Function OR n:Class)
                DETACH DELETE n''', {'paths': changed_paths})
            graph.query('MATCH (:File)-[r:IMPORTS]->(:File) DELETE r')
            deleted = [old for old, new, _ in changes if old and old != new]
            graph.query('MATCH (f:File) WHERE f.path IN $paths DETACH DELETE f', {'paths': deleted})
            for path in changed_paths:
                if path not in items:
                    continue
                item = items[path]
                graph.query('MERGE (f:File {path:$path}) SET f+=$props', {'path': path, 'props': {
                    **item['file'], 'source_type': SOURCE, 'simulation_id': simulation}})
                for label, key in [('Class', 'classes'), ('Function', 'functions')]:
                    batch(graph, f'''UNWIND $rows AS r MATCH (f:File {{path:r.file_path}})
                        MERGE (n:{label} {{qualified_name:r.qualified_name}}) SET n+=r,n.source_type='AST_DIFF_REPLACEMENT_SIMULATION'
                        MERGE (f)-[:DEFINES]->(n)''', item[key])
            batch(graph, """UNWIND $rows AS r MATCH (a:File {path:r.source}),(b:File {path:r.target})
                MERGE (a)-[e:IMPORTS]->(b) SET e.source_type='AST_DIFF_REPLACEMENT_SIMULATION' """,
                [{'source': path, 'target': target} for path, (imports, _, _) in resolved.items() for target in sorted(imports)])
            batch(graph, '''UNWIND $rows AS r MATCH (a:Function {qualified_name:r.source}),(b:Function {qualified_name:r.target})
                MERGE (a)-[e:CALLS {line:r.line}]->(b)
                SET e.source_type='AST_DIFF_REPLACEMENT_SIMULATION',e.resolution='conservative_static' ''',
                [{'source': c['caller'], 'target': t, 'line': c['line']} for _, calls, _ in resolved.values() for c, t in calls])
            after_impact = _blast(graph, changed_paths)
            impacted = sorted(before_impact | after_impact)
            tests = sorted(p for p in impacted if p in sources or p in final_sources
                           if PurePosixPath(p).name.startswith('test_') or p.startswith('tests/'))
            # Deleted tests are evidence, never suggested as runnable pytest arguments.
            runnable = [p for p in tests if p in final_sources]
            def dep_rows(entries):
                return [{'relationship': k, 'source': a, 'target': b} for k, a, b in sorted(entries)]
            payload = {
                'tenant_graph': tenant, 'semantics': 'FULL_FILE_REPLACEMENT', 'source_type': SOURCE,
                'sandbox_graph_name': name, 'sandbox_clone_time_ms': clone_ms,
                'changed_files': changed_paths,
                'dependency_graphs': {
                    'before': dependency_view(before_dependencies, impacted, sources, changed_paths),
                    'after': dependency_view(after_dependencies, impacted, final_sources, changed_paths),
                }, 'added_dependencies': dep_rows(after_dependencies - before_dependencies),
                'removed_dependencies': dep_rows(before_dependencies - after_dependencies),
                'removed_or_signature_changed_symbols': sorted(broken_symbols), 'potentially_broken_callers': broken_callers,
                'impacted_files': impacted, 'pre_patch_impacted_files': sorted(before_impact),
                'post_patch_impacted_files': sorted(after_impact), 'impacted_test_files': tests,
                'recommended_pytest_command': 'pytest -- ' + ' '.join(shlex.quote(p) for p in runnable) if runnable else '',
                'test_selection_basis': 'PRE_POST_UNION_STATIC_CANDIDATES_NOT_SAFE_SKIP_PROOF',
                'final_file_hashes': {p: items[p]['file']['sha256'] for p in changed_paths if p in items},
                'source_revisions': sorted({r[3] for r in captured if r[3]}),
                'unresolved_calls': sum(len(unresolved) for _, _, unresolved in resolved.values()),
                'dependency_comparison_basis': 'REPARSED_CAPTURED_SOURCE_BEFORE_VS_FINAL_SOURCE',
                'parse_coverage': {
                    'before_failed_files': sorted(p for p, item in old_items.items() if item['errors']),
                    'after_failed_files': sorted(p for p, item in items.items() if item['errors']),
                    'basis': 'PARSE_FAILURES_HAVE_NO_STATIC_DEPENDENCIES_NOT_NO_IMPACT',
                },
                'analysis_limits': {'captured_file_limit': 10000, 'source_byte_limit': MAX_SOURCE_BYTES,
                    'call_resolution': 'conservative Python static expressions; dynamic dispatch unresolved'},
                'model_calls': 0,
            }
        payload['sandbox_cleaned_up'] = name not in db_manager.list_tenant_graphs()
        if not payload['sandbox_cleaned_up']:
            raise HTTPException(503, 'Sandbox cleanup could not be verified')
        return payload
