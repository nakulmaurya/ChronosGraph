"""Paired context lookup timings on one pinned graph; historical reports untouched.

The legacy comparator is context_locator.py from the repository's dd8f44a
baseline, with current dependencies. This is NOT an agent/token-cost benchmark.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import time
import types
from app.db.client import db_manager
from app.services.context_locator import locate_context, _entry_inventory
from app.services.workflow_benchmark import percentile


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--tenant', required=True)
    p.add_argument('--query', required=True)
    p.add_argument('--expected-path', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--samples',type=int,default=20)
    args = p.parse_args()
    if not 5 <= args.samples <= 100: p.error('Require 5..100 paired samples')
    output = Path(args.output)
    if output.exists(): p.error('Refusing to overwrite existing evidence')
    source = subprocess.check_output(['git','show','dd8f44a:backend/app/services/context_locator.py'],text=True)
    legacy = types.ModuleType('chronosgraph_legacy_context')
    exec(compile(source,'dd8f44a:context_locator.py','exec'), legacy.__dict__)
    calls = {'legacy':lambda:legacy.locate_context(args.tenant,args.query,8192),
             'exact_lookup':lambda:locate_context(args.tenant,args.query,8192)}
    timings = {k:[] for k in calls}
    receipts = {}
    for name,call in calls.items(): receipts[name] = call()  # warm-up, not measured
    randomizer = random.Random(20261018)
    for _ in range(args.samples):
        order = list(calls);randomizer.shuffle(order)
        for name in order:
            started=time.perf_counter();receipts[name]=calls[name]()
            timings[name].append((time.perf_counter()-started)*1000)
    for name,data in receipts.items():
        assert args.expected_path in {r['path'] for r in data['entry_points']}, name
    # Compare routes to the intended target, not irrelevant old lexical fillers.
    route_sets = {name:{tuple(r['via']) for r in data['related_importers'] if r['via'][-1] == args.expected_path}
                  for name,data in receipts.items()}
    graph=db_manager.get_graph(args.tenant)
    query = "MATCH (s:Function {name:$query})<-[:DEFINES]-(f:File) RETURN f.path"
    plan=str(graph.explain(query,{'query':args.query}))
    report={'tenant':args.tenant,'query':args.query,'expected_path':args.expected_path,
            'baseline':'dd8f44a context_locator with current shared dependencies',
            'baseline_locator_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'order':'20 paired samples with seeded randomized within-pair order' if args.samples==20 else 'paired randomized within-pair order',
            'warmups_per_mode':1,'samples_per_mode':args.samples,
            'latency_ms':{name:{'p50':statistics.median(values),'p95':percentile(values),'samples':values} for name,values in timings.items()},
            'same_expected_entry':True,'same_target_import_routes':route_sets['legacy']==route_sets['exact_lookup'],
            'target_import_routes':{k:[list(r) for r in sorted(v)] for k,v in route_sets.items()},
            'entry_inventory_files':{k:len(_entry_inventory(args.tenant,args.query)[0]) if k=='exact_lookup' else graph.ro_query('MATCH (f:File) RETURN count(f)').result_set[0][0] for k in calls},
            'exact_symbol_plan':plan,'index_scan_confirmed':'Index Scan' in str(plan),
            'limitations':['Exact candidate mode intentionally omits incidental lexical-only entry files',
                'General prose uses the inventory fallback','Policy/memory/ownership expansion may still scan graph inventories',
                'Same-host service timing; not an independent agent benchmark or guarantee of <50ms'],
            'model_calls':0}
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['same_expected_entry','same_target_import_routes','entry_inventory_files','index_scan_confirmed']}))
    print({k:{'p50':round(v['p50'],3),'p95':round(v['p95'],3)} for k,v in report['latency_ms'].items()})


if __name__=='__main__':main()
