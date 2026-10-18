"""Rebuild a pinned repository into a NEW graph and run the independent import audit.

Never overwrites a tenant or the historical report. Repository source is parsed,
not executed. The created audit graph is deleted unless --keep-graph is explicit.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import uuid
from app.db.client import db_manager
from app.ingestion.ingest_repo import ingest_repo
from app.services.workflow_benchmark import audit_absolute_imports, captured, source_digest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    p.add_argument('--revision', required=True)
    p.add_argument('--historical-report', required=True)
    p.add_argument('--dataset', default='FalkorDB/GraphRAG-SDK')
    p.add_argument('--output', required=True)
    p.add_argument('--keep-graph', action='store_true')
    args = p.parse_args()
    output = Path(args.output)
    if output.exists():
        p.error('Refusing to overwrite an existing report')
    if len(args.revision) != 40 or any(c not in '0123456789abcdef' for c in args.revision):
        p.error('Require exact lowercase 40-character commit')
    historical_bytes = Path(args.historical_report).read_bytes()
    historical = next(r for r in json.loads(historical_bytes)['repositories'] if r['dataset'] == args.dataset)
    if historical['source_revisions'] != [args.revision]:
        p.error('Historical comparison must use the same source revision')
    tenant = 'repo_test_fresh_audit_' + uuid.uuid4().hex
    report = {'dataset':args.dataset,'source_revision':args.revision,'tenant_graph':tenant,
              'historical_report_sha256':hashlib.sha256(historical_bytes).hexdigest(),
              'application_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
              'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],text=True).strip()),
              'source_code_executed':False,'model_calls':0}
    started = time.perf_counter()
    try:
        stats = ingest_repo(args.source, tenant, ref=args.revision)
        graph = db_manager.get_graph(tenant)
        sources = captured(graph)
        assert stats['source_revision'] == args.revision
        report.update(ingestion_seconds=round(time.perf_counter()-started,3),
                      source_digest=source_digest(sources),python_files=len(sources),
                      historical_python_files=historical['initial_counts']['python_files'],
                      historical_audit=historical['import_accuracy'],fresh_audit=audit_absolute_imports(sources,graph))
        old_missing = {tuple(edge) for edge in historical['import_accuracy']['missing_edges']}
        actual = {tuple(edge) for edge in graph.ro_query('MATCH (a:File)-[:IMPORTS]->(b:File) RETURN a.path,b.path').result_set}
        report['historical_missing_recovered'] = len(old_missing & actual)
        report['historical_missing_still_absent'] = [list(edge) for edge in sorted(old_missing - actual)]
        report['captured_source_digest_matches'] = report['source_digest'] == historical['captured_source_digest']
        report['corpus_file_count_matches'] = report['python_files'] == report['historical_python_files']
        report['acceptance'] = ('PASS_SCOPED_ABSOLUTE_IMPORT_AUDIT' if report['corpus_file_count_matches'] and report['captured_source_digest_matches'] and
            not report['fresh_audit']['missing_edges'] and not report['fresh_audit']['extra_edges'] and
            not report['historical_missing_still_absent'] else 'DISCREPANCIES_REQUIRE_ACCOUNTING')
    finally:
        if not args.keep_graph and tenant in db_manager.list_tenant_graphs():
            db_manager.get_graph(tenant).delete()
        report['audit_graph_retained'] = tenant in db_manager.list_tenant_graphs()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['dataset','source_revision','python_files','historical_missing_recovered','acceptance','audit_graph_retained']}))


if __name__ == '__main__':
    main()
