"""Explicit opt-in native AOF rewrite regression; disposable review DB ONLY.

Does not disable persistence or modify Redis configuration. Raw GRAPH.COPY must
refuse the fork while an actual rewrite is active; the bounded wrapper succeeds.
"""
import os,sys,time,uuid,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from redis import Redis
from redis.exceptions import ResponseError
from app.db.client import db_manager
from app.config import settings

if os.environ.get('CHRONOSGRAPH_DISPOSABLE_BENCHMARK')!='1':
    raise SystemExit('Require explicit disposable-database consent')
r=Redis(host=settings.falkordb_host,port=settings.falkordb_port,decode_responses=True)
assert r.info('persistence')['aof_enabled']==1,'Require actual AOF-enabled native server'
source='repo_test_fork_'+uuid.uuid4().hex;destination=source+'_copy'
graph=db_manager.get_graph(source);rows=[]
try:
    graph.query('CREATE (:CopyProbe {value:42})')
    for i in range(5):
        until=time.monotonic()+15
        while any(r.info('persistence').get(k,0) for k in ('aof_rewrite_in_progress','rdb_bgsave_in_progress')):
            if time.monotonic()>until:raise TimeoutError('Previous persistence fork did not finish')
            time.sleep(.025)
        r.bgrewriteaof()
        assert r.info('persistence')['aof_rewrite_in_progress']==1,'Rewrite finished before native overlap; inconclusive'
        try:graph.copy(destination)
        except ResponseError as exc:
            assert str(exc)=='GRAPH.COPY failed, could not fork',str(exc)
        else:raise AssertionError('Raw copy did not reproduce fork refusal; inconclusive')
        started=time.monotonic();copied=db_manager.copy_graph(source,destination)
        assert copied.ro_query('MATCH (n:CopyProbe) RETURN n.value').result_set==[[42]]
        rows.append({'raw_copy':'NATIVE_FORK_REFUSED','bounded_copy':'PASS','elapsed_ms':round((time.monotonic()-started)*1000,3)})
        copied.delete();assert destination not in db_manager.list_tenant_graphs()
    print(json.dumps({'scope':'DISPOSABLE_NATIVE_AOF_CONTENTION','runs':rows,'persistence_enabled':r.info('persistence')['aof_enabled'],'cleanup':'PASS'},indent=2))
finally:
    for name in (destination,source):
        if name in db_manager.list_tenant_graphs():db_manager.get_graph(name).delete()
