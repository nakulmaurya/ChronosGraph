"""Synthetic native navigation baseline; only writes/deletes a unique fixture graph.
Run against a disposable DB, not the live service. Not a real-repository scalability guarantee.
"""
import json,os,statistics,time,uuid
from pathlib import Path
from app.db.client import db_manager
from app.services.command_center import overview,search_repository,file_detail
assert os.environ.get('CHRONOSGRAPH_DISPOSABLE_BENCHMARK')=='1','Require an explicitly isolated benchmark database'
name='repo_test_benchmark_'+uuid.uuid4().hex;g=db_manager.get_graph(name)
try:
    g.query("CREATE (:RepoMetadata {status:'READY',repository:'synthetic/5000-files'})")
    db_manager.ensure_indexes(name)
    paths=[f'pkg{i//100:02}/file{i:04}'+('.py' if i<1000 else '.ts') for i in range(5000)]
    for offset in range(0,len(paths),250):
        g.query("UNWIND $paths AS path CREATE (:TrackedFile {path:path,analysis_status:'FIXTURE'})",{'paths':paths[offset:offset+250]})
    for offset in range(0,1000,250):
        g.query("UNWIND $paths AS path CREATE (f:File {path:path,loc:3}), (s:Function {name:'run',qualified_name:path+':run',file_path:path,start_line:1,end_line:3}), (f)-[:DEFINES]->(s)",{'paths':paths[offset:offset+250]})
    pairs=[{'a':paths[i],'b':paths[(i+1)%1000]} for i in range(1000)]
    for offset in range(0,len(pairs),250):
        g.query('UNWIND $pairs AS r MATCH (a:File {path:r.a}),(b:File {path:r.b}) CREATE (a)-[:IMPORTS]->(b)',{'pairs':pairs[offset:offset+250]})
    calls={'root_map':lambda:overview(name),'folder_map':lambda:overview(name,'pkg09/'),
           'tail_exact_path_search':lambda:search_repository(name,'file4999'),
           'symbol_search_page':lambda:search_repository(name,'run'),
           'file_inspector':lambda:file_detail(name,paths[999])}
    results={}
    for key,call in calls.items():
        values=[]
        for _ in range(12):
            start=time.perf_counter();data=call();values.append((time.perf_counter()-start)*1000)
        results[key]={'p50_ms':round(statistics.median(values),2),'p95_ms':round(sorted(values)[-2],2),'max_ms':round(max(values),2)}
        assert results[key]['p95_ms']<2000,(key,results[key])
    assert search_repository(name,'file4999')['entry_points'][0]['path']==paths[-1]
    out={'fixture':{'tracked_files':5000,'python_files':1000,'functions':1000,'imports':1000},
         'scope':'Synthetic single-client native DB reads; not import throughput, maximum size, runtime dispatch or production capacity',
         'budget_p95_ms':2000,'samples_per_operation':12,'results':results}
    print(json.dumps(out,indent=2))
    if os.environ.get('EVIDENCE_DIR'):
        dest=Path(os.environ['EVIDENCE_DIR']);dest.mkdir(parents=True,exist_ok=True)
        (dest/'navigation-benchmark.json').write_text(json.dumps(out,indent=2))
finally:g.delete()
