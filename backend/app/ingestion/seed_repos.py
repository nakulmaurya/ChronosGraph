"""Ingest real source and public GitHub provenance; never invent policy history."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen
from redis.exceptions import ResponseError
from app.db.client import db_manager
from app.ingestion.ast_parser import parse_python_file, resolve_import

REPOS = {'repo_falkordb_py': 'FalkorDB/falkordb-py', 'repo_graphrag_sdk': 'FalkorDB/GraphRAG-SDK'}
PINNED_REVISIONS = {'repo_falkordb_py': '31f63f44a5745b9bec65969a1db706906718cb82',
                    'repo_graphrag_sdk': '35e67a0b27fdcc7f2c28508b09e86169851a8187'}
CACHE = Path(os.environ.get('CHRONOSGRAPH_SOURCE_CACHE', Path(__file__).resolve().parents[3] / '.source-cache'))


def api(repo, suffix):
    path = CACHE / 'metadata' / (hashlib.sha256(f'{repo}/{suffix}'.encode()).hexdigest()+'.json')
    if path.exists():
        return json.loads(path.read_text())
    request = Request(f'https://api.github.com/repos/{repo}/{suffix}', headers={
        'User-Agent': 'ChronosGraph-source-ingestion', 'Accept': 'application/vnd.github+json'})
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return data


def timestamp(value):
    return int(dt.datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()) if value else 0


def resolve_call(call, item, known, definitions):
    """Only lexical, self/cls, and unambiguous explicitly imported calls are edges."""
    path, scope = call['caller'].split(':',1)
    parts, expr = scope.split('.'), call['expression']
    candidates = []
    if expr.startswith(('self.','cls.')) and len(parts)>1:
        candidates.append(f"{path}:{'.'.join(parts[:-1])}.{expr.split('.',1)[1]}")
    elif expr.isidentifier():
        for depth in range(len(parts),-1,-1):
            candidates.append(f"{path}:{'.'.join(parts[:depth]+[expr])}")
    for imp in item['imports']:
        if imp['scope'] and not scope.startswith(imp['scope']+'.'):
            continue
        head,*rest = expr.split('.')
        if head != imp['alias'] or imp.get('name')=='*':
            continue
        for target in resolve_import(imp,path,known):
            symbol='.'.join(([imp['name']] if imp.get('name') else [])+rest)
            candidates.append(f'{target}:{symbol}')
    matches=list(dict.fromkeys(c for c in candidates if c in definitions))
    return matches[0] if len(matches)==1 else None


def pagerank(paths, edges):
    if not paths:
        return {}
    n=len(paths); outgoing={p:set() for p in paths}; ranks={p:1/n for p in paths}
    for edge in edges:
        outgoing[edge['source']].add(edge['target'])
    for _ in range(100):
        dangling=sum(ranks[p] for p in paths if not outgoing[p])
        new={p:0.15/n+0.85*dangling/n for p in paths}
        for src in paths:
            for dest in outgoing[src]:
                new[dest]+=0.85*ranks[src]/len(outgoing[src])
        if sum(abs(new[p]-ranks[p]) for p in paths)<1e-10:
            return new
        ranks=new
    return ranks


def load_policies(graph, source, revision, filename):
    """Optional curated evidence. No policy file means no fabricated decisions."""
    if not filename:
        return 0
    rows=json.loads(Path(filename).read_text()).get(graph.name,[])
    for row in rows:
        required={'id','file_path','scope_symbol','rule','rationale','source_url','source_type','status','valid_from','valid_to'}
        if not required <= row.keys():
            raise ValueError(f'Missing policy fields: {required-row.keys()}')
        if row['source_type'] not in {'VERIFIED_SOURCE','USER_POLICY','SYNTHETIC_DEMO'} or row['status'] not in {'ACTIVE','SUPERSEDED'}:
            raise ValueError('Explicit valid policy provenance and status required')
        full=(source/row['file_path']).resolve()
        if source.resolve() not in full.parents or not full.is_file():
            raise ValueError('Policy references absent/out-of-repository file')
        if row['source_type']=='VERIFIED_SOURCE':
            excerpt=row.get('evidence_excerpt','')
            if not excerpt or excerpt not in full.read_text():
                raise ValueError('Verified policy requires an actual matching source excerpt')
        params={**row,'embedding':db_manager.embed_text(row['rule']), 'recorded_at':int(time.time()), 'source_revision':revision}
        graph.query('''MATCH (f:File {path:$file_path}) MERGE (d:Decision {id:$id})
        SET d.scope_symbol=$scope_symbol,d.rule=$rule,d.rationale=$rationale,d.source_url=$source_url,
        d.source_type=$source_type,d.status=$status,d.valid_from=$valid_from,d.valid_to=$valid_to,
        d.recorded_at=$recorded_at,d.source_revision=$source_revision,d.embedding=vecf32($embedding)
        MERGE (d)-[:GOVERNS]->(f)''',params)
    for row in rows:
        if row.get('supersedes_id'):
            graph.query('MATCH (n:Decision {id:$new}),(o:Decision {id:$old}) MERGE (n)-[:SUPERSEDED]->(o)',
                        {'new':row['id'],'old':row['supersedes_id']})
    return len(rows)



def ensure_demo_policies(graph):
    """CR-001 approved fictional policies. Context PRs are NOT policy provenance."""
    paths = {
        'repo_falkordb_py': [
            ('falkordb/graph.py','Graph.query','Unbounded query execution is allowed.','Agent queries must specify a bounded timeout.'),
            ('falkordb/asyncio/graph.py','Graph.ro_query','Exploratory agent reads may mutate state.','Exploratory agent reads must use read-only queries.'),
            ('falkordb/query_result.py','module_root','Unknown result types may be silently dropped.','Unknown result types must produce an explicit diagnostic.'),
            ('falkordb/falkordb.py','module_root','A request may choose any graph name.','Application requests must use an approved tenant graph.')],
        'repo_graphrag_sdk': [
            ('graphrag_sdk/src/graphrag_sdk/core/connection.py','module_root','Connections may wait without an upper bound.','Connections must use a bounded timeout.'),
            ('graphrag_sdk/src/graphrag_sdk/storage/graph_store.py','module_root','Agent discovery may use write queries.','Agent discovery must use read-only graph queries.'),
            ('graphrag_sdk/src/graphrag_sdk/ingestion/pipeline.py','module_root','Documents may be ingested without source identifiers.','Every ingested document must retain source provenance.'),
            ('graphrag_sdk/src/graphrag_sdk/retrieval/router.py','module_root','Superseded decisions may be treated as current.','Retrieval must distinguish active and superseded decisions.')]
    }
    prs=graph.ro_query('MATCH (p:PullRequest) RETURN p.number,p.url ORDER BY p.number').result_set
    now=int(time.time())
    for index,(path,scope,old_rule,new_rule) in enumerate(paths[graph.name]):
        count=graph.ro_query('MATCH (f:File {path:$path}) RETURN count(f)',{'path':path}).result_set[0][0]
        if count!=1 or not prs:
            raise ValueError(f'Demo policy must anchor to a real File and PullRequest: {path}')
        pr_num,pr_url=prs[index%len(prs)]
        pair=f'demo_{graph.name}_{index}'
        if graph.ro_query('MATCH (d:Decision {id:$id}) RETURN count(d)',{'id':pair+'_active'}).result_set[0][0]:
            continue  # Never revert a later live override while re-seeding.
        for suffix,status,rule,valid_from,valid_to in [
            ('old','SUPERSEDED',old_rule,now-7200,now-3600),
            ('active','ACTIVE',new_rule,now-3600,0)]:
            graph.query("""MATCH (f:File {path:$path}),(p:PullRequest {number:$pr})
            CREATE (d:Decision {id:$id,scope_symbol:$scope,rule:$rule,
              rationale:'Fictional policy scenario approved by the project owner; not an upstream policy.',
              source_type:'DEMO_POLICY_SCENARIO',source_url:$source,context_pr_url:$pr_url,
              status:$status,valid_from:$vf,valid_to:$vt,recorded_at:$now,
              recorded_from:$now,recorded_to:0,time_basis:'DEMO_SCENARIO_CLOCK',
              embedding:vecf32($embedding)})
            CREATE (d)-[:GOVERNS]->(f)
            CREATE (d)-[:SCENARIO_CONTEXT {not_historical_attribution:true}]->(p)""",
            {'path':path,'pr':pr_num,'id':pair+'_'+suffix,'scope':scope,'rule':rule,
             'source':'https://github.com/nakulmaurya/ChronosGraph/blob/main/backend/app/ingestion/seed_repos.py',
             'pr_url':pr_url,'status':status,'vf':valid_from,'vt':valid_to,'now':now,
             'embedding':db_manager.embed_text(rule)})
        graph.query('MATCH (a:Decision {id:$active}),(o:Decision {id:$old}) MERGE (a)-[:SUPERSEDED]->(o)',
                    {'active':pair+'_active','old':pair+'_old'})
    return graph.ro_query("MATCH (d:Decision {source_type:'DEMO_POLICY_SCENARIO'}) RETURN count(d)").result_set[0][0]

def seed_single_repo(tenant, force_reset=False, policy_file=None):
    if tenant not in REPOS:
        raise ValueError('Unknown tenant')
    repo=REPOS[tenant]; source=CACHE/repo.split('/')[-1]
    if not (source/'.git').is_dir():
        source.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['git','clone','--quiet','--depth','1',f'https://github.com/{repo}.git',str(source)],check=True)
    revision=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    if revision != PINNED_REVISIONS[tenant]:
        subprocess.run(['git','-C',str(source),'fetch','--quiet','--depth','1','origin',PINNED_REVISIONS[tenant]],check=True)
        subprocess.run(['git','-C',str(source),'checkout','--quiet','--detach',PINNED_REVISIONS[tenant]],check=True)
        revision=PINNED_REVISIONS[tenant]
    paths=subprocess.check_output(['git','-C',str(source),'ls-files','*.py'],text=True).splitlines()
    items=[parse_python_file(source/p,relative_to=source) for p in paths]
    errors=[(item['file']['path'],item['errors']) for item in items if item['errors']]
    if errors:
        raise ValueError(f'Invalid upstream Python: {errors}')
    known=set(paths); definitions={f['qualified_name'] for item in items for f in item['functions']}
    imports=[]; calls=[]; unresolved=0
    for item in items:
        for imp in item['imports']:
            imports.extend({'source':item['file']['path'],'target':p} for p in resolve_import(imp,item['file']['path'],known))
        for call in item['calls']:
            target=resolve_call(call,item,known,definitions)
            if target:
                calls.append({'source':call['caller'],'target':target,'line':call['line']})
            else:
                unresolved+=1
    contributors=api(repo,'contributors?per_page=10')
    prs=api(repo,'pulls?state=all&per_page=5&sort=updated&direction=desc')
    issues=[i for i in api(repo,'issues?state=open&per_page=30') if 'pull_request' not in i]
    for pr in prs:
        pr['changed_files']=api(repo,f"pulls/{pr['number']}/files?per_page=100")
        pr['actual_reviews']=api(repo,f"pulls/{pr['number']}/reviews?per_page=100")
    # All external provenance is fetched before an optional reset.
    graph=db_manager.get_graph(tenant)
    if force_reset and tenant in db_manager.list_tenant_graphs():
        graph.delete(); graph=db_manager.get_graph(tenant)
    db_manager.ensure_indexes(tenant)
    start=time.perf_counter(); ranks=pagerank(paths,imports)
    files=[{**item['file'],'pagerank':ranks[item['file']['path']], 'source_revision':revision,
            'source_url':f"https://github.com/{repo}/blob/{revision}/{item['file']['path']}"} for item in items]
    graph.query('''UNWIND $rows AS r MERGE (f:File {path:r.path}) SET f.name=r.name,f.loc=r.loc,
    f.sha256=r.sha256,f.source_text=r.source_text,f.source_chars=r.source_chars,
    f.source_utf8_bytes=r.source_utf8_bytes,f.pagerank=r.pagerank,f.pagerank_method='iterative_import_pagerank',
    f.source_revision=r.source_revision,f.source_url=r.source_url''',{'rows':files})
    for label,key in [('Class','classes'),('Function','functions')]:
        # Labels are fixed internal constants. All source values are parameterized.
        graph.query(f'''UNWIND $rows AS r MATCH (f:File {{path:r.file_path}})
        MERGE (s:{label} {{qualified_name:r.qualified_name}}) SET s.name=r.name,s.file_path=r.file_path,
        s.start_line=r.start_line,s.end_line=r.end_line,s.signature=r.signature,s.is_async=r.is_async
        MERGE (f)-[:DEFINES]->(s)''',{'rows':[s for item in items for s in item[key]]})
    graph.query('''UNWIND $rows AS r MATCH (a:File {path:r.source}),(b:File {path:r.target})
    MERGE (a)-[:IMPORTS]->(b)''',{'rows':imports})
    graph.query('''UNWIND $rows AS r MATCH (a:Function {qualified_name:r.source}),(b:Function {qualified_name:r.target})
    MERGE (a)-[c:CALLS {line:r.line}]->(b) SET c.resolution='conservative_static' ''',{'rows':calls})
    rank_method='native_falkordb_pagerank'
    try:
        ranking=graph.ro_query("CALL algo.pageRank('File','IMPORTS') YIELD node,score RETURN node.path,score").result_set
        graph.query('UNWIND $rows AS r MATCH (f:File {path:r.path}) SET f.pagerank=r.score,f.pagerank_method=$method',
                    {'rows':[{'path':p,'score':score} for p,score in ranking], 'method':rank_method})
    except ResponseError as exc:
        # A documented algorithm-compatibility fallback, not a blanket failure mask.
        if not any(word in str(exc).lower() for word in ['unknown procedure','procedure not found','argument']):
            raise
        rank_method='iterative_import_pagerank'
    for user in contributors:
        graph.query('MERGE (c:Contributor {login:$login}) SET c.avatar_url=$avatar,c.source_url=$url',
                    {'login':user['login'],'avatar':user['avatar_url'],'url':user['html_url']})
    for pr in prs:
        graph.query('''MERGE (c:Contributor {login:$author}) MERGE (p:PullRequest {number:$number})
        SET p.title=$title,p.url=$url,p.state=$state,p.merged_at=$merged_at MERGE (c)-[:AUTHORED]->(p)''',
        {'author':pr['user']['login'],'number':pr['number'],'title':pr['title'],'url':pr['html_url'],
         'state':'MERGED' if pr.get('merged_at') else pr['state'].upper(),'merged_at':timestamp(pr.get('merged_at'))})
        for change in pr['changed_files']:
            graph.query('''MATCH (p:PullRequest {number:$number}),(f:File {path:$path})
            MERGE (p)-[r:MODIFIES]->(f) SET r.additions=$adds,r.deletions=$dels''',
            {'number':pr['number'],'path':change['filename'],'adds':change['additions'],'dels':change['deletions']})
        for review in pr['actual_reviews']:
            if review.get('user'):
                graph.query('''MERGE (c:Contributor {login:$login}) WITH c MATCH (p:PullRequest {number:$number})
                MERGE (c)-[r:REVIEWED {review_id:$review_id}]->(p) SET r.state=$state''',
                {'login':review['user']['login'],'number':pr['number'],'review_id':review['id'],'state':review['state']})
    for issue in issues:
        graph.query('''MERGE (i:Issue {number:$number}) SET i.title=$title,i.url=$url,i.state=$state,
        i.created_at=$created_at,i.embedding=vecf32($embedding)''',
        {'number':issue['number'],'title':issue['title'],'url':issue['html_url'],'state':issue['state'].upper(),
         'created_at':timestamp(issue['created_at']),'embedding':db_manager.embed_text(issue['title'])})
        for path in paths:
            if path in (issue.get('body') or ''):
                graph.query('''MATCH (i:Issue {number:$number}),(f:File {path:$path}) MERGE (i)-[r:AFFECTS]->(f)
                SET r.evidence='literal_path_in_issue_body',r.verified=false''',{'number':issue['number'],'path':path})
    from app.ingestion.repo_rules import enrich_repository
    enrich_repository(graph,source,revision,f'https://github.com/{repo}',paths)
    policies=load_policies(graph,source,revision,policy_file) if policy_file else ensure_demo_policies(graph)
    return {'repository':repo,'revision':revision,
            'nodes':graph.query('MATCH (n) RETURN count(n)').result_set[0][0],
            'edges':graph.query('MATCH ()-[r]->() RETURN count(r)').result_set[0][0],
            'pagerank_method':rank_method,'files':len(files),'functions':len(definitions),'resolved_calls':len(calls),
            'unresolved_calls':unresolved,'policies':policies,
            'policy_status':('CURATED_INPUT_LOADED' if policy_file else 'APPROVED_DEMO_POLICY_SCENARIOS') if policies else 'AWAITING_CURATED_POLICY_EVIDENCE',
            'graph_write_ms':round((time.perf_counter()-start)*1000,2)}


def seed_all_repos(force_reset=False, policy_file=None):
    return {tenant:seed_single_repo(tenant,force_reset,policy_file) for tenant in REPOS}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reset',action='store_true')
    parser.add_argument('--policies',help='Curated provenance-labeled policy JSON')
    args=parser.parse_args()
    print(json.dumps(seed_all_repos(args.reset,args.policies),indent=2))
