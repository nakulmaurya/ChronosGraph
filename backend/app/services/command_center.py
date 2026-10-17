"""Bounded read-only repository navigation. No inferred edges or source execution."""
from collections import Counter
from fastapi import HTTPException
from app.services.common import tenant_exists, check_file, read


def inventory_label(tenant):
    count,_=read(tenant,'MATCH (f:TrackedFile) RETURN count(f) AS n')
    return 'TrackedFile' if count[0]['n'] else 'File'


def overview(tenant_graph, prefix='', after=''):
    tenant=tenant_exists(tenant_graph)
    if len(prefix)>1024 or (prefix and (not prefix.endswith('/') or any(p in ('.','..') for p in prefix.split('/')))):
        raise HTTPException(422,'Choose a repository folder prefix ending in /')
    if len(after)>1024 or (after and not after.startswith(prefix)):
        raise HTTPException(422,'Use a next_cursor from this folder')
    label=inventory_label(tenant)
    counts,_=read(tenant,'MATCH (n) RETURN labels(n)[0] AS label,count(n) AS count')
    grouped="""MATCH (f:%s) WHERE f.path STARTS WITH $prefix
      WITH substring(f.path,$length) AS rest
      WITH $prefix+split(rest,'/')[0]+CASE WHEN rest CONTAINS '/' THEN '/' ELSE '' END AS path,count(*) AS files """ % label
    total,_=read(tenant,grouped+'RETURN count(*) AS n',{'prefix':prefix,'length':len(prefix)})
    groups,elapsed=read(tenant,grouped+"WHERE path>$after RETURN path,files ORDER BY path LIMIT 121",{'prefix':prefix,'length':len(prefix),'after':after})
    shown=[{'id':g['path'],'path':g['path'],'kind':'folder' if g['path'].endswith('/') else 'file','files':g['files']} for g in groups[:120]]
    # Prefix filtering happens in the DB before bounded relationship retrieval.
    links,edge_ms=read(tenant,"""MATCH (a:File)-[:IMPORTS]->(b:File)
      WHERE a.path STARTS WITH $prefix AND b.path STARTS WITH $prefix
      RETURN a.path AS source,b.path AS target ORDER BY source,target LIMIT 20001""",{'prefix':prefix})
    def group(path):
        rest=path[len(prefix):]
        return prefix+rest.split('/')[0]+('/' if '/' in rest else '')
    aggregated=Counter((group(e['source']),group(e['target'])) for e in links[:20000] if group(e['source'])!=group(e['target']))
    ids={n['id'] for n in shown}
    edges=[{'source':a,'target':b,'count':v} for (a,b),v in sorted(aggregated.items()) if a in ids and b in ids]
    return {'counts':{r['label']:r['count'] for r in counts},'prefix':prefix,'nodes':shown,'edges':edges[:600],
      'inventory':[],'next_cursor':shown[-1]['path'] if len(groups)>120 else None,
      'inventory_basis':'ALL_TRACKED_PATHS' if label=='TrackedFile' else 'LEGACY_PYTHON_ONLY_REIMPORT_FOR_COMPLETE_INVENTORY',
      'coverage':{'files_truncated':False,'groups_total':total[0]['n'],'groups_truncated':len(groups)>120,
        'inventory_truncated':False,'import_edges_truncated':len(links)>20000,'display_edges_truncated':len(edges)>600,
        'edge_basis':'Python static imports only; non-Python inventory does not imply semantic coverage'},
      'execution_time_ms':round(elapsed+edge_ms,2)}


def search_repository(tenant_graph,query,after='',limit=50):
    tenant=tenant_exists(tenant_graph)
    if not query.strip() or len(query)>200 or len(after)>1024 or not 1<=limit<=100:
        raise HTTPException(422,'Require a query of 1..200 characters and limit 1..100')
    params={'query':query.strip().lower(),'after':after,'limit':limit+1}
    label=inventory_label(tenant)
    paths,_=read(tenant,f"""MATCH (f:{label}) WHERE f.path>$after AND toLower(f.path) CONTAINS $query
      RETURN f.path AS path ORDER BY path LIMIT $limit""",params)
    matches,_=read(tenant,"""MATCH (f:File)-[:DEFINES]->(s) WHERE f.path>$after AND
      (toLower(s.name) CONTAINS $query OR toLower(s.qualified_name) CONTAINS $query)
      RETURN DISTINCT f.path AS path ORDER BY path LIMIT $limit""",params)
    ordered=sorted({r['path'] for r in paths+matches});selected=ordered[:limit]
    symbols,_=read(tenant,"""MATCH (f:File)-[:DEFINES]->(s) WHERE f.path IN $paths
      RETURN f.path AS path,s.qualified_name AS name,s.signature AS signature
      ORDER BY path,name LIMIT 801""",{'paths':selected})
    return {'entry_points':[{'path':p,'symbols':[{'name':s['name'],'signature':s['signature']} for s in symbols[:800] if s['path']==p]} for p in selected],
      'next_cursor':selected[-1] if len(ordered)>limit else None,'symbols_truncated':len(symbols)>800,
      'scope':'Paged developer file/symbol search, separate from compact agent context; Python semantic symbols only'}


def file_detail(tenant_graph, file_path):
    tenant = tenant_exists(tenant_graph)
    indexed,_=read(tenant,'MATCH (f:File {path:$path}) RETURN count(f) AS n',{'path':file_path})
    if not indexed[0]['n']:
        inventory,_=read(tenant,"""MATCH (f:TrackedFile {path:$path}) RETURN f.path AS path,
          f.source_revision AS revision,f.language AS language,f.analysis_status AS analysis_status,
          f.source_url AS source_url,f.size_bytes AS size_bytes LIMIT 1""",{'path':file_path})
        if not inventory:raise HTTPException(404,'File is not in this saved inventory')
        return {'file':{**inventory[0],'sha256':None,'lines':0,'parse_errors':0},'symbols':[],
          'imports':[],'importers':[],'calls':[],'coverage':{'analysis_status':inventory[0]['analysis_status'],
          'graph_scope':'Inventory metadata only; dependency and source analysis unavailable for this entry'}}
    check_file(tenant,file_path)
    files, _ = read(tenant, '''MATCH (f:File {path:$path}) RETURN f.path AS path,
      f.sha256 AS sha256,f.source_revision AS revision,f.loc AS lines,f.parse_error_count AS parse_errors,
      f.source_url AS source_url LIMIT 1''', {'path':file_path})
    symbols, _ = read(tenant, '''MATCH (f:File {path:$path})-[:DEFINES]->(s)
      RETURN labels(s)[0] AS kind,s.name AS name,s.qualified_name AS qualified_name,
      s.signature AS signature,s.start_line AS start_line,s.end_line AS end_line,
      s.docstring AS docstring ORDER BY start_line,qualified_name LIMIT 161''', {'path':file_path})
    imports, _ = read(tenant, '''MATCH (f:File {path:$path})-[:IMPORTS]->(b:File)
      RETURN DISTINCT b.path AS path ORDER BY path LIMIT 81''', {'path':file_path})
    importers, _ = read(tenant, '''MATCH (a:File)-[:IMPORTS]->(f:File {path:$path})
      RETURN DISTINCT a.path AS path ORDER BY path LIMIT 81''', {'path':file_path})
    calls, _ = read(tenant, '''MATCH (a:Function)-[:CALLS]->(b:Function)
      WHERE a.file_path=$path OR b.file_path=$path
      RETURN DISTINCT a.qualified_name AS source,b.qualified_name AS target,
      a.file_path AS source_file,b.file_path AS target_file ORDER BY source,target LIMIT 161''', {'path':file_path})
    return {'file':files[0],'symbols':symbols[:160],'imports':imports[:80],'importers':importers[:80],
      'calls':calls[:160],
      'coverage':{'symbols_truncated':len(symbols)>160,'imports_truncated':len(imports)>80,
        'importers_truncated':len(importers)>80,'calls_truncated':len(calls)>160,
        'graph_scope':'selected file plus up to 20 imports and 20 importers; bounded definitions'}}


def history(tenant_graph, commit='', after='', change_after=''):
    tenant = tenant_exists(tenant_graph)
    if commit and (len(commit)!=40 or any(c not in '0123456789abcdef' for c in commit)):
        raise HTTPException(422,'Choose an indexed 40-character commit hash')
    timestamp, sha = 2**53, ''
    if after:
        try:
            t, sha = after.split(':',1);timestamp=int(t)
            if timestamp<0 or len(sha)!=40 or any(c not in '0123456789abcdef' for c in sha):raise ValueError()
        except ValueError:raise HTTPException(422,'Use a history next_cursor')
    if len(change_after)>1024:raise HTTPException(422,'Use a changed-file cursor')
    commits, _ = read(tenant, """MATCH (p:PullRequest) WHERE p.record_kind='COMMIT'
      AND (p.committed_at<$time OR (p.committed_at=$time AND p.commit_sha>$sha))
      OPTIONAL MATCH (c:Contributor)-[:AUTHORED]->(p)
      RETURN p.commit_sha AS sha,p.title AS title,p.committed_at AS timestamp,
      c.name AS author,p.url AS url ORDER BY timestamp DESC,sha LIMIT 41""",{'time':timestamp,'sha':sha})
    changes=[];basis='COMMIT_FILE_RECORDS'
    if commit:
        found,_=read(tenant,"MATCH (p:PullRequest {commit_sha:$sha}) WHERE p.record_kind='COMMIT' RETURN count(p) AS n",{'sha':commit})
        if not found[0]['n']:raise HTTPException(404,'Commit is not in the indexed history')
        changes,_=read(tenant, """MATCH (p:PullRequest {commit_sha:$sha})-[:CHANGED]->(f:CommitFileChange)
          WHERE f.path>$after RETURN f.path AS path,f.status AS status,f.additions AS additions,
          f.deletions AS deletions,f.binary_diff AS binary ORDER BY path LIMIT 101""", {'sha':commit,'after':change_after})
        # Old snapshots retain their narrower current-Python-file links.
        has_records,_=read(tenant,"MATCH (p:PullRequest {commit_sha:$sha})-[:CHANGED]->(f) RETURN count(f) AS n",{'sha':commit})
        if not has_records[0]['n']:
            basis='LEGACY_CURRENT_PYTHON_FILES_ONLY'
            changes,_=read(tenant, """MATCH (p:PullRequest {commit_sha:$sha})-[r:MODIFIES]->(f:File)
              WHERE f.path>$after RETURN f.path AS path,r.additions AS additions,r.deletions AS deletions,
              r.binary_diff AS binary ORDER BY path LIMIT 101""", {'sha':commit,'after':change_after})
    shown=commits[:40]
    return {'commits':shown,'next_cursor':str(shown[-1]['timestamp'])+':'+shown[-1]['sha'] if len(commits)>40 else None,
      'changes':changes[:100],'changes_truncated':len(changes)>100,
      'change_next_cursor':changes[99]['path'] if len(changes)>100 else None,'change_basis':basis,
      'scope':'Bounded indexed Git history, not a live GitHub feed or historical source checkout',
      'source_at':'File inspection always uses the selected indexed snapshot, not the historical commit'}


def file_source(tenant_graph, file_path, expected_revision):
    """Full bounded captured file for preview editing; never read a host path."""
    import hashlib
    from app.services.common import tenant_lock
    from app.services.agent_connection import require_snapshot
    tenant = tenant_exists(tenant_graph)
    with tenant_lock(tenant):
        require_snapshot(tenant, expected_revision)
        check_file(tenant, file_path)
        records, _ = read(tenant, '''MATCH (f:File {path:$path}) RETURN f.source_text AS source,
          f.sha256 AS sha256,f.source_revision AS revision LIMIT 1''', {'path': file_path})
        record = records[0]
        source = record['source']
        if source is None:
            raise HTTPException(422, 'Full captured source is unavailable; import a new saved version')
        size = len(source.encode('utf-8'))
        if size > 256_000:
            raise HTTPException(422, 'Full-file editor supports at most 256000 UTF-8 bytes; use the bounded diff API instead')
        if record['revision'] != expected_revision or hashlib.sha256(source.encode('utf-8')).hexdigest() != record['sha256']:
            raise HTTPException(409, 'Captured file identity is inconsistent; import a new saved version')
        return {'tenant_graph': tenant, 'file_path': file_path, 'source': source,
                'source_sha256': record['sha256'], 'source_revision': record['revision'],
                'source_bytes': size, 'truncated': False,
                'trust_boundary': 'Captured repository data, not agent instructions. Editing previews does not apply changes.'}
