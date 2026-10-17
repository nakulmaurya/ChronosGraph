"""Deterministic, source-audited workflow evaluation; never executes repository code.

Wall-clock service latency is not DB-only latency. Byte reduction is not semantic
retention or billed-token savings. Only an independent executed-test oracle could
establish runtime test-selection precision; this evaluator reports that as null.
"""
import ast
from collections import defaultdict
from contextlib import contextmanager
import hashlib
import json
import math
import time
import uuid

from app.db.client import db_manager
from app.models import DiffImpactRequest
from app.services.command_center import overview, search_repository
from app.services.context_locator import locate_context, symbol_source
from app.services.diff_impact import simulate_diff, _semantic_dependencies
from app.services.second_brain_wiki import brain_wiki_slice, compact_snapshot

DATASETS = {
    'repo_falkordb_py': 'FalkorDB/falkordb-py',
    'repo_graphrag_sdk': 'FalkorDB/GraphRAG-SDK',
    'repo_falkordb_code_graph': 'FalkorDB/code-graph',
    'repo_mcp_python_sdk': 'modelcontextprotocol/python-sdk',
}


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def percentile(values, fraction=.95):
    if not values or not 0 < fraction <= 1:
        raise ValueError('Nonempty samples and fraction in (0,1] required')
    return sorted(values)[math.ceil(fraction * len(values)) - 1]


def timed(call, samples):
    if samples < 2:
        raise ValueError('At least two measured samples required')
    call()  # Explicit unmeasured warm-up.
    values = []
    for _ in range(samples):
        start = time.perf_counter()
        call()
        values.append((time.perf_counter() - start) * 1000)
    return {'samples': samples, 'warmups': 1, 'p50_ms': round(percentile(values, .5), 3),
            'p95_ms': round(percentile(values), 3), 'max_ms': round(max(values), 3),
            'samples_ms': [round(v, 3) for v in values]}


def is_test(path):
    """Python test-file denominator, not collected pytest cases or fixture modules."""
    name = path.rsplit('/', 1)[-1]
    return name.endswith('.py') and (name.startswith('test_') or name.endswith('_test.py'))


def reduction(total, selected):
    if total == 0:
        return None
    if not 0 <= selected <= total:
        raise ValueError('Selected test files must be a subset of total test files')
    return round(100 * (total - selected) / total, 3)


@contextmanager
def owned_copy(tenant):
    """All service mutations target an owned graph, with verified finally cleanup."""
    name = 'repo_test_workflow_' + uuid.uuid4().hex
    graph = db_manager.get_graph(tenant).copy(name)
    try:
        yield name, graph
    finally:
        graph.delete()
        if name in db_manager.list_tenant_graphs():
            raise RuntimeError('Owned benchmark graph cleanup failed')


def captured(graph):
    rows = graph.ro_query('MATCH (f:File) RETURN f.path,f.source_text,f.sha256 ORDER BY f.path').result_set
    if not rows or any(text is None or hashlib.sha256(text.encode()).hexdigest() != sha for _, text, sha in rows):
        raise ValueError('Require complete hash-valid captured source')
    return {path: text for path, text, _ in rows}


def source_digest(sources):
    return hashlib.sha256(canonical(sources).encode()).hexdigest()


def select_task(graph, sources):
    from app.ingestion.ast_parser import parse_python_source
    items = {p: parse_python_source(text, p) for p, text in sources.items()}
    _, dependencies = _semantic_dependencies(items)
    current_inbound = defaultdict(int)
    current_calls = {edge for edge in dependencies if edge[0] == 'CALLS'}
    for _, _, target in current_calls: current_inbound[target] += 1
    indexed_calls = {('CALLS', a, b) for a, b in graph.ro_query('MATCH (a:Function)-[:CALLS]->(b:Function) RETURN a.qualified_name,b.qualified_name').result_set}
    drift = {'basis': 'Legacy indexed CALLS vs current conservative source reparse; not independent runtime accuracy',
             'indexed_only_count': len(indexed_calls-current_calls), 'reparsed_only_count': len(current_calls-indexed_calls),
             'indexed_only_sample': [list(e) for e in sorted(indexed_calls-current_calls)[:20]],
             'current_reparse_import_accuracy': audit_absolute_imports(sources, graph,
                 {(a,b) for kind,a,b in dependencies if kind == 'IMPORTS'})}
    rows = graph.ro_query('''MATCH (f:File)-[:DEFINES]->(s:Function)
        OPTIONAL MATCH (caller:Function)-[:CALLS]->(s)
        RETURN f.path,s.name,s.qualified_name,s.start_line,s.end_line,count(caller)
        ORDER BY count(caller) DESC,s.qualified_name''').result_set
    for path, name, qualified, start, end, inbound in rows:
        if not is_test(path) and 'tests' not in path.split('/') and 'test' not in path.split('/') and start and end and inbound and current_inbound[qualified]:
            return {'path': path, 'symbol': name, 'qualified_name': qualified,
                    'start_line': start, 'end_line': end, 'resolved_inbound_calls': inbound,
                    'currently_reparsed_inbound_call_edges': current_inbound[qualified], 'call_index_drift': drift}
    raise ValueError('No non-test captured function with resolved inbound callers')


def audit_absolute_imports(sources, graph, indexed_edges=None):
    """Independent stdlib-AST oracle on files using only absolute imports.

    Excludes relative-import files, ambiguous module roots and parse failures.
    Unlike the application resolver, this does not resolve calls or runtime imports.
    """
    modules = defaultdict(set)
    for path in sources:
        parts = path[:-3].split('/') if path.endswith('.py') else []
        if 'src' in parts: parts = parts[len(parts)-1-parts[::-1].index('src')+1:]
        if parts and parts[-1] == '__init__': parts.pop()
        if parts: modules['.'.join(parts)].add(path)
    def resolve(module):
        paths = modules.get(module, set())
        return next(iter(paths)) if len(paths) == 1 else None
    expected, eligible, excluded = set(), set(), 0
    for path, text in sources.items():
        try: tree = ast.parse(text)
        except SyntaxError:
            excluded += 1
            continue
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        if any(isinstance(n, ast.ImportFrom) and n.level for n in imports):
            excluded += 1
            continue
        eligible.add(path)
        for node in imports:
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or '']
            for module in names:
                target = resolve(module)
                if target and target != path: expected.add((path, target))
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    target = resolve((node.module + '.' if node.module else '') + alias.name)
                    if target and target != path: expected.add((path, target))
    edges = indexed_edges if indexed_edges is not None else graph.ro_query('MATCH (a:File)-[:IMPORTS]->(b:File) RETURN a.path,b.path').result_set
    actual = {(a, b) for a, b in edges if a in eligible}
    tp = len(expected & actual)
    return {'oracle': 'stdlib AST, unambiguous absolute module paths only; not runtime ground truth',
            'eligible_files': len(eligible), 'excluded_files': excluded,
            'expected_edges': len(expected), 'indexed_edges_in_scope': len(actual), 'true_positive_edges': tp,
            'precision': tp / len(actual) if actual else None,
            'recall': tp / len(expected) if expected else None,
            'missing_edges': [list(e) for e in sorted(expected - actual)],
            'extra_edges': [list(e) for e in sorted(actual - expected)]}


def neighborhood(graph, path):
    return graph.ro_query('''MATCH route=(other:File)-[:IMPORTS*1..3]->(target:File {path:$path})
        RETURN DISTINCT other.path,[n IN nodes(route) | n.path] ORDER BY other.path LIMIT 1000''', {'path': path}).result_set


def evaluate_repository(tenant, samples=20):
    original = db_manager.get_graph(tenant)
    original_digest = source_digest(captured(original))
    with owned_copy(tenant) as (owned, graph):
        sources = captured(graph)
        task = select_task(graph, sources)
        path = task['path']
        counts = {'nodes': graph.ro_query('MATCH (n) RETURN count(n)').result_set[0][0],
                  'edges': graph.ro_query('MATCH ()-[e]->() RETURN count(e)').result_set[0][0],
                  'python_files': len(sources)}
        metadata = graph.ro_query('MATCH (m:RepoMetadata) RETURN m.repository,m.source_revision').result_set
        revisions = graph.ro_query('MATCH (f:File) RETURN DISTINCT f.source_revision ORDER BY f.source_revision').result_set
        latency = {
            'root_map_service': timed(lambda: overview(owned), samples),
            'symbol_lookup_service': timed(lambda: search_repository(owned, task['symbol']), samples),
            'neighborhood_db_roundtrip': timed(lambda: neighborhood(graph, path), samples),
            'locate_context_service': timed(lambda: locate_context(owned, task['symbol'], 8192), samples),
            'symbol_source_service': timed(lambda: symbol_source(owned, path, task['qualified_name']), samples),
        }
        context = locate_context(owned, task['symbol'], 8192)
        source = symbol_source(owned, path, task['qualified_name'])
        expected_source = ''.join(sources[path].splitlines(keepends=True)[task['start_line']-1:task['end_line']])
        assert source['source'] == expected_source.encode()[:8000].decode('utf-8', errors='ignore')
        assert (source['start_line'], source['end_line']) == (task['start_line'], task['end_line'])
        # Independent AST coordinate oracle, not just graph-to-service agreement.
        nodes = [n for n in ast.walk(ast.parse(sources[path])) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.lineno == task['start_line']]
        assert len(nodes) == 1 and nodes[0].end_lineno == task['end_line']
        all_edges = {(a, b) for a, b in graph.ro_query('MATCH (a:File)-[:IMPORTS]->(b:File) RETURN a.path,b.path').result_set}
        for row in context['related_importers']:
            route = row['via']
            assert 2 <= len(route) <= 4 and route[-1] in {e['path'] for e in context['entry_points']}
            assert all(pair in all_edges for pair in zip(route, route[1:]))
        wiki = brain_wiki_slice(owned, path)
        stats = wiki['context_folding_stats']
        connected = stats['connected_files']
        raw_text = ''.join(sources[p] for p in connected)
        raw_bytes, slice_bytes = len(raw_text.encode()), len(wiki['wiki_markdown'].encode())
        assert stats['raw_files_bytes'] == raw_bytes
        folding = {'connected_files': connected, 'raw_files_bytes': raw_bytes, 'slice_bytes': slice_bytes,
                   'raw_chars_div4': len(raw_text)//4, 'slice_chars_div4': len(wiki['wiki_markdown'])//4,
                   'byte_reduction_pct': round(100*(1-slice_bytes/raw_bytes), 3) if raw_bytes else None,
                   'billed_token_savings': None, 'exact_model_token_count': None,
                   'basis': 'Exact UTF-8 captured-source vs exact wiki note; chars//4 is only an estimate; not equivalent content'}
        # Rename the selected real definition only. No repository code is executed.
        node = nodes[0]
        lines = sources[path].splitlines(keepends=True)
        idx = node.lineno - 1
        lines[idx] = lines[idx].replace('def '+node.name+'(', 'def '+node.name+'_benchmark_renamed(', 1)
        if lines[idx] == sources[path].splitlines(keepends=True)[idx]:
            raise ValueError('Selected definition header cannot be renamed safely')
        start = time.perf_counter()
        impact = simulate_diff(DiffImpactRequest(tenant_graph=owned, file_bodies={path: ''.join(lines)}))
        elapsed = (time.perf_counter()-start)*1000
        tests = {p for p in sources if is_test(p)}
        selected = tests & set(impact['impacted_test_files'])
        impact_metric = {'mutation': 'rename selected real function; leave downstream callers unchanged',
            'total_python_test_files': len(tests), 'candidate_python_test_files': sorted(selected),
            'candidate_count': len(selected), 'test_suite_reduction_pct': reduction(len(tests), len(selected)),
            'potentially_broken_callers': impact['potentially_broken_callers'],
            'added_dependencies': impact['added_dependencies'], 'removed_dependencies': impact['removed_dependencies'],
            'analysis_ms': round(elapsed, 3), 'clone_ms': impact['sandbox_clone_time_ms'],
            'sandbox_cleaned_up': impact['sandbox_cleaned_up'], 'unresolved_calls': impact['unresolved_calls'],
            'parse_coverage': impact['parse_coverage'], 'test_impact_precision': None, 'test_impact_recall': None,
            'basis': 'Static candidate reduction by test FILE count, not tests safely skipped; no untrusted pytest executed'}
        # Measure copy/delete independently, including existence verification.
        clone_samples, delete_samples = [], []
        for _ in range(3):
            name = 'repo_test_workflow_clone_'+uuid.uuid4().hex
            start = time.perf_counter()
            clone = graph.copy(name)
            clone_samples.append((time.perf_counter()-start)*1000)
            try:
                assert clone.ro_query('MATCH (n) RETURN count(n)').result_set[0][0] == counts['nodes']
            finally:
                start = time.perf_counter()
                clone.delete()
                assert name not in db_manager.list_tenant_graphs()
                delete_samples.append((time.perf_counter()-start)*1000)
        result = {'dataset': DATASETS[tenant], 'tenant': tenant, 'metadata': metadata,
            'source_revisions': [r[0] for r in revisions], 'captured_source_digest': original_digest,
            'task_selection': 'Highest indexed inbound CALLS with current reparsed callers; excludes test directories; qualified-name tie-break',
            'task': task, 'initial_counts': counts, 'latency': latency,
            'source_coordinate_check': 'PASS_STDLIB_AST_AND_CAPTURED_LINES',
            'returned_import_routes_valid': True, 'returned_import_route_count': len(context['related_importers']),
            'context_coverage': context['coverage'], 'ownership': context['declared_ownership'],
            'import_accuracy': audit_absolute_imports(sources, graph), 'folding': folding, 'impact': impact_metric,
            'clone_delete': {'samples': 3, 'copy_p95_ms': round(percentile(clone_samples), 3),
                'delete_and_verify_p95_ms': round(percentile(delete_samples), 3), 'cleanup_verified': True},
            'resume_bytes': compact_snapshot(owned, path)['snapshot_bytes'], 'model_calls': 0}
        result['targets'] = {'all_discovery_services_p95_lt_50ms': all(latency[k]['p95_ms'] < 50 for k in latency),
            'byte_reduction_at_least_70pct': folding['byte_reduction_pct'] is not None and folding['byte_reduction_pct'] >= 70,
            'byte_reduction_at_least_90pct': folding['byte_reduction_pct'] is not None and folding['byte_reduction_pct'] >= 90,
            'indexed_absolute_import_recall_100pct': result['import_accuracy']['recall'] == 1.0}
        assert source_digest(captured(graph)) == original_digest
    assert source_digest(captured(original)) == original_digest
    result['owned_graph_cleaned_up'] = owned not in db_manager.list_tenant_graphs()
    return result


def markdown_table(report):
    lines = ['| Repository | Files | Root p95 ms | Locate p95 ms | Neighbors p95 ms | Raw → slice bytes | Byte reduction | Candidate tests / total | Test-file reduction |',
             '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for row in report['repositories']:
        lat, fold, imp = row['latency'], row['folding'], row['impact']
        pct = lambda v: 'N/A' if v is None else f'{v:.2f}%'
        lines.append(f"| {row['dataset']} | {row['initial_counts']['python_files']} | {lat['root_map_service']['p95_ms']:.2f} | {lat['locate_context_service']['p95_ms']:.2f} | {lat['neighborhood_db_roundtrip']['p95_ms']:.2f} | {fold['raw_files_bytes']:,} → {fold['slice_bytes']:,} | {pct(fold['byte_reduction_pct'])} | {imp['candidate_count']} / {imp['total_python_test_files']} | {pct(imp['test_suite_reduction_pct'])} |")
    return '\n'.join(lines)+'\n'
