#!/usr/bin/env python3
"""Capture bounded live measurements; invokes clone audits and deterministic triage.

No policy override is performed. Investigation/playbook nodes are normal persisted
application state. Source AST totals and live totals are reported separately.
"""
import argparse
import datetime
import json
import statistics
import sys
import uuid
from pathlib import Path
from urllib.request import Request, urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.db.client import db_manager
from app.services.common import rows


def capture(api, tenants):
    def get(query, tenant):
        return rows(db_manager.get_graph(tenant).ro_query(query))
    def post(endpoint, body):
        request = Request(api.rstrip('/')+endpoint, data=json.dumps(body).encode(),
                          headers={'Content-Type':'application/json'}, method='POST')
        with urlopen(request, timeout=120) as response:
            return json.load(response)
    records = []
    for tenant in tenants:
        graph = db_manager.get_graph(tenant)
        labels = get('MATCH (n) RETURN labels(n)[0] AS label,count(n) AS nodes ORDER BY label',tenant)
        relations = get('MATCH ()-[r]->() RETURN type(r) AS relationship,count(r) AS edges ORDER BY relationship',tenant)
        meta = get('MATCH (m:RepoMetadata) RETURN m.source_revision AS revision,m.history_limit AS history_limit,m.history_scope AS history_scope',tenant)[0]
        files = get('MATCH (f:File) RETURN f.path AS path,f.pagerank AS pagerank',tenant)
        source_count = sum(r['nodes'] for r in labels if r['label'] in {'File','Function','Class'})
        assert source_count == graph.ro_query('MATCH (n) WHERE n:File OR n:Function OR n:Class RETURN count(n)').result_set[0][0]
        coverage = get('MATCH (:PullRequest {source_type:"GIT_COMMIT_HISTORY"})-[:MODIFIES]->(f:File) RETURN count(DISTINCT f) AS files',tenant)[0]['files']
        selected = get('MATCH (:Decision {status:"ACTIVE"})-[:GOVERNS]->(f:File) RETURN f.path AS path ORDER BY f.pagerank DESC,f.path LIMIT 1',tenant)[0]['path']
        policy = post('/track3/ask-brain', {'tenant_graph':tenant,'file_path':selected,'question':'Current demo policy and linked Git author evidence'})
        audits = [post('/track1/sandbox-audit',{'tenant_graph':tenant,'modified_files':[selected]}) for _ in range(5)]
        assert all(a['sandbox_cleaned_up'] for a in audits)
        clones = [a['sandbox_clone_time_ms'] for a in audits]
        scenario = 'T05 telemetry policy '+selected+' '+uuid.uuid4().hex
        cold = post('/track2/investigate', {'tenant_graph':tenant,'issue_description':scenario})
        warm = post('/track2/investigate', {'tenant_graph':tenant,'issue_description':scenario,'execution_mode':'compiled_playbook'})
        assert cold['total_steps_executed']==5 and warm['total_steps_executed']==3
        records.append({'tenant':tenant,**meta,'live_label_counts_before_samples':labels,
            'live_relationship_counts_before_samples':relations,'live_nodes_before_samples':sum(r['nodes'] for r in labels),
            'live_edges_before_samples':sum(r['edges'] for r in relations),
            'source_ast_nodes':source_count,'python_files':len(files),
            'functions':next(r['nodes'] for r in labels if r['label']=='Function'),
            'classes':next(r['nodes'] for r in labels if r['label']=='Class'),
            'normalized_pagerank_sum':sum(r['pagerank'] for r in files),
            'files_with_git_history_evidence':coverage,'selected_file':selected,
            'git_author_evidence':policy['top_experts'],'clone_samples_ms':clones,
            'clone_median_ms':statistics.median(clones),'clone_min_ms':min(clones),'clone_max_ms':max(clones),
            'clone_cleanup_verified':True,'impacted_files_including_labeled_synthetic':len(audits[0]['impacted_files']),
            'impacted_functions_including_labeled_synthetic':len(audits[0]['impacted_functions']),
            'cold_ms':cold['duration_ms'],'warm_ms':warm['duration_ms'],
            'cold_actions':cold['total_steps_executed'],'replayed_actions':warm['total_steps_executed'],
            'cold_dead_ends':sum(n['status']=='DEAD_END' for n in cold['subgraph']['nodes']),
            'warm_dead_ends':sum(n['status']=='DEAD_END' for n in warm['subgraph']['nodes']),
            'tokens_used':warm['tokens_used'],'ownership_limit':'Unverified Git author identity; latest 40 commits, not exhaustive or definitive maintainers.'})
    backfill = post('/track3/ask-brain',{'tenant_graph':'repo_falkordb_py','file_path':'falkordb/graph.py','question':'Git provenance backfill verification'})
    assert backfill['top_experts']
    return {'captured_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'method':'Five sequential GRAPH.COPY audits per tenant; one cold/replay pair; single VM, shared loopback Docker DB; no universal latency or LLM-token claim.',
        'repositories':records,'falkordb_graph_py_backfill_experts':backfill['top_experts']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api-base',default='http://127.0.0.1:8001/api/v1')
    parser.add_argument('--tenants',nargs='+',default=['repo_falkordb_code_graph','repo_mcp_python_sdk'])
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(capture(args.api_base,args.tenants),indent=2)+'\n')
    print('Wrote measured evidence to',args.output)
