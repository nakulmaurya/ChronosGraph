"""Capture real localhost API responses; clean up only policies created here.
Run from backend with the API listening on 127.0.0.1:8000:
    python ../scripts/capture_t02_evidence.py
"""
import json
import statistics
import time
import uuid
from pathlib import Path
import httpx
from app.services.common import read
from app.db.client import db_manager

DEST=Path(__file__).resolve().parents[1]/'tasks'/'reports'/'T-02-samples'
DEST.mkdir(parents=True,exist_ok=True)


def save(name,value):
    (DEST/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')


def post(client,route,payload):
    response=client.post('/api/v1/'+route,json=payload)
    response.raise_for_status()
    return response.json()


with httpx.Client(base_url='http://127.0.0.1:8000',timeout=120) as client:
    save('tenants',client.get('/api/v1/tenants').json())
    audit=post(client,'track1/sandbox-audit',{'modified_files':['falkordb/graph.py'],
               'proposed_description':'Evidence capture: explicitly simulated dependency, no source patch supplied.'})
    save('sandbox-audit',audit)
    save('ask-brain',post(client,'track3/ask-brain',{'question':'bounded query timeout','file_path':'falkordb/graph.py'}))
    ids=[]
    path='falkordb/node.py'
    existing,_=read('repo_falkordb_py','MATCH (d:Decision)-[:GOVERNS]->(:File {path:$path}) RETURN d.id AS id',{'path':path})
    if existing:
        raise RuntimeError('Evidence target already has policies; refuse to alter existing history')
    try:
        first=post(client,'track3/override-policy',{'target_file_path':path,
            'new_rule_text':'Evidence-only validation rule: preserve node property types.',
            'rationale':'Temporary test policy, not an upstream rule. Removed after capture.'})
        ids.extend(d['id'] for d in first['active_decisions'])
        second=post(client,'track3/override-policy',{'target_file_path':path,
            'new_rule_text':'Evidence-only revision: validate node property types before writes.',
            'rationale':'Temporary test supersession, not an upstream rule. Removed after capture.'})
        ids.extend(d['id'] for d in second['active_decisions'])
        save('override-policy',second)
    finally:
        if ids:
            db_manager.query('repo_falkordb_py','MATCH (d:Decision) WHERE d.id IN $ids DETACH DELETE d',{'ids':ids})
    issue='HTTP evidence policy triage falkordb/graph.py '+uuid.uuid4().hex
    cold=post(client,'track2/investigate',{'issue_description':issue})
    warm=post(client,'track2/investigate',{'issue_description':issue,'execution_mode':'compiled_playbook'})
    save('investigate-cold',cold); save('investigate-compiled',warm)
    repeats=[]
    for _ in range(5):
        label='Benchmark policy triage falkordb/graph.py '+uuid.uuid4().hex
        a=post(client,'track2/investigate',{'issue_description':label})
        b=post(client,'track2/investigate',{'issue_description':label,'execution_mode':'compiled_playbook'})
        repeats.append({'cold_ms':a['duration_ms'],'warm_ms':b['duration_ms'],
                        'speedup':b['latency_speedup_factor']})
    clones=[]
    for tenant in ['repo_falkordb_py','repo_graphrag_sdk']:
        for _ in range(3):
            with db_manager.ephemeral_sandbox(tenant) as (_,name,elapsed):
                clones.append({'tenant':tenant,'clone_ms':elapsed})
            assert name not in db_manager.list_tenant_graphs()
    save('benchmark',{'method':'5 sequential localhost HTTP cold/warm pairs; no artificial sleeps or model calls',
         'runs':repeats,'median_speedup':statistics.median(r['speedup'] for r in repeats),
         'model_calls':0,'token_savings_status':'UNMEASURED','required_token_savings_pct':75,
         'required_speedup':4,'clone_measurements':clones,'sandbox_orphans':[
             n for n in db_manager.list_tenant_graphs() if n.startswith('sandbox_pr_')]})
    print(json.dumps({'saved':str(DEST),'median_speedup':statistics.median(r['speedup'] for r in repeats),
                      'http_cold_ms':cold['duration_ms'],'http_warm_ms':warm['duration_ms'],
                      'http_speedup':warm['latency_speedup_factor'],'clone_ms':audit['sandbox_clone_time_ms']}))
