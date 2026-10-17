"""Bounded read-only repository navigation. No inferred edges or source execution."""
from collections import Counter
from fastapi import HTTPException
from app.services.common import tenant_exists, check_file, read


def overview(tenant_graph, prefix=''):
    tenant = tenant_exists(tenant_graph)
    if len(prefix) > 1024 or (prefix and (not prefix.endswith('/') or any(p in ('.', '..') for p in prefix.split('/')))):
        raise HTTPException(422, 'Choose a repository folder prefix ending in /')
    counts, _ = read(tenant, 'MATCH (n) RETURN labels(n)[0] AS label,count(n) AS count')
    files, elapsed = read(tenant, '''MATCH (f:File) RETURN f.path AS path,f.pagerank AS pagerank,
      f.parse_error_count AS parse_errors ORDER BY f.path LIMIT 10001''')
    bounded = len(files) > 10000
    files = files[:10000]
    visible = [f for f in files if f['path'].startswith(prefix)]
    groups = {}
    def group(path):
        if not path.startswith(prefix): return None
        rest = path[len(prefix):]
        return prefix + rest.split('/')[0] + ('/' if '/' in rest else '')
    for f in visible:
        key = group(f['path'])
        g = groups.setdefault(key, {'id':key, 'path':key, 'kind':'folder' if key.endswith('/') else 'file', 'files':0})
        g['files'] += 1
    links, edge_ms = read(tenant, '''MATCH (a:File)-[:IMPORTS]->(b:File)
      RETURN a.path AS source,b.path AS target ORDER BY source,target LIMIT 20001''')
    aggregated = Counter()
    for edge in links[:20000]:
        a,b = group(edge['source']),group(edge['target'])
        if a and b and a != b: aggregated[a,b] += 1
    # Return every group's inventory in pages through folder drill-down, never fake edges.
    ordered = sorted(groups.values(),key=lambda g:(g['kind']!='folder',g['path']))
    shown = ordered[:120]
    ids = {n['id'] for n in shown}
    return {'counts':{r['label']:r['count'] for r in counts}, 'prefix':prefix,
      'nodes':shown, 'edges':[{'source':a,'target':b,'count':v} for (a,b),v in sorted(aggregated.items()) if a in ids and b in ids][:600],
      'inventory':visible[:300], 'coverage':{'file_limit':10000,'files_truncated':bounded,
        'groups_total':len(ordered),'groups_truncated':len(ordered)>120,'inventory_truncated':len(visible)>300,
        'import_edges_truncated':len(links)>20000,'display_edges_truncated':sum(1 for a,b in aggregated if a in ids and b in ids)>600,'edge_basis':'File IMPORTS aggregated by displayed folder; no runtime inference'},
      'execution_time_ms':round(elapsed+edge_ms,2)}


def file_detail(tenant_graph, file_path):
    tenant = tenant_exists(tenant_graph)
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


def history(tenant_graph, commit=''):
    tenant = tenant_exists(tenant_graph)
    if commit and (len(commit)!=40 or any(c not in '0123456789abcdef' for c in commit)):
        raise HTTPException(422,'Choose an indexed 40-character commit hash')
    commits, _ = read(tenant, '''MATCH (p:PullRequest) WHERE p.record_kind='COMMIT'
      OPTIONAL MATCH (c:Contributor)-[:AUTHORED]->(p)
      RETURN p.commit_sha AS sha,p.title AS title,p.committed_at AS timestamp,
      c.name AS author,p.url AS url ORDER BY timestamp DESC,sha LIMIT 80''')
    changes=[]
    if commit:
        changes,_=read(tenant, '''MATCH (p:PullRequest {commit_sha:$sha})-[r:MODIFIES]->(f:File)
          RETURN f.path AS path,r.additions AS additions,r.deletions AS deletions,
          r.binary_diff AS binary ORDER BY path LIMIT 301''', {'sha':commit})
        if not any(c['sha']==commit for c in commits):
            raise HTTPException(404,'Commit is not in the displayed indexed history window')
    return {'commits':commits,'changes':changes[:300],'changes_truncated':len(changes)>300,
      'scope':'Bounded indexed Git history, not a live GitHub feed or historical source checkout',
      'source_at':'File inspection always uses the selected indexed snapshot, not the historical commit'}
