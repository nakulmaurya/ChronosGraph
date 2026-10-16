"""Reproducible native ownership-index experiment on an owned disposable graph.

Run from repo root with PYTHONPATH=backend and the installed backend interpreter.
Does not alter existing graphs or server configuration. No model/network calls.
"""
import argparse
import json
from pathlib import Path
import statistics
import time
import uuid
from app.db.client import db_manager
from app.db.ownership_indexes import ensure_ownership_indexes


def measure(graph, query, params, repeats):
    expected = graph.ro_query(query, params).result_set
    graph.ro_query(query, params)  # Warm plan/cache, not the first-query latency.
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        actual = graph.ro_query(query, params).result_set
        timings.append((time.perf_counter() - start) * 1000)
        if actual != expected:
            raise RuntimeError('Lookup changed during experiment')
    return {'median_client_ms': round(statistics.median(timings), 4),
            'plan': str(graph.explain(query, params)),
            'profile': graph.profile(query, params).plan, 'result': expected}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--nodes-per-label', type=int, default=2000, choices=range(100,10001))
    parser.add_argument('--repeats', type=int, default=41, choices=range(3,102))
    args = parser.parse_args()
    name = 'repo_test_' + uuid.uuid4().hex
    if name in db_manager.list_tenant_graphs():
        raise RuntimeError('Refuse to reuse an existing graph')
    graph = db_manager.get_graph(name)
    receipt = {'graph':name, 'nodes_per_label':args.nodes_per_label,
               'repeats':args.repeats, 'model_calls':0, 'checks':[],
               'scope':'Synthetic warm point lookups; not an end-to-end or agent benchmark'}
    try:
        graph.query('''UNWIND range(0,$last) AS i CREATE
          (:OwnershipSource {id:'source_'+toString(i)}),
          (:OwnershipRule {id:'rule_'+toString(i)}),
          (:DeclaredOwner {name:'@owner_'+toString(i),kind:'USERNAME'})''', {'last':args.nodes_per_label-1})
        cases = [('OwnershipSource','id','source_'),('OwnershipRule','id','rule_'),('DeclaredOwner','name','@owner_')]
        for label,prop,prefix in cases:
            query=f'MATCH (n:{label} {{{prop}:$value}}) RETURN n.{prop}'
            params={'value':prefix+str(args.nodes_per_label-1)}
            receipt['checks'].append({'label':label,'query':query,'params':params,
                'before':measure(graph,query,params,args.repeats)})
        ensure_ownership_indexes(graph)
        for item in receipt['checks']:
            item['after']=measure(graph,item['query'],item['params'],args.repeats)
            assert item['before']['result']==item['after']['result']
            assert 'Index Scan' not in item['before']['plan']
            assert 'Index Scan' in item['after']['plan']
            item['median_speedup_ratio']=round(item['before']['median_client_ms']/item['after']['median_client_ms'],3)
        receipt['status']='PASS'
    finally:
        if name in db_manager.list_tenant_graphs(): graph.delete()
        receipt['fixture_graph_removed']=name not in db_manager.list_tenant_graphs()
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(receipt,indent=2))
    print(json.dumps({**receipt,'checks':[{k:v for k,v in c.items() if k not in ('before','after','query','params')} for c in receipt['checks']]},indent=2))


if __name__=='__main__': main()
