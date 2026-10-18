"""Opt-in, committed organizational manifest. Explicit declarations, not extraction.

Only .chronosgraph/organization.json and regular UTF-8 Git blobs at the pinned
revision are read. No network fetch, identity verification or source execution.
"""
import hashlib
import json
import re
from pathlib import PurePosixPath
from app.ingestion.codeowners import _git_bytes

MANIFEST = '.chronosgraph/organization.json'


def blob(root, revision, path, limit=262144):
    p = PurePosixPath(path)
    if not path or p.is_absolute() or '..' in p.parts or str(p) != path or '\\' in path:
        raise ValueError('Organizational source requires a normalized relative Git path')
    record = _git_bytes(root, 'ls-tree', '-z', revision, '--', path)
    if not record:
        raise ValueError('Organizational source missing at pinned revision: '+path)
    header, actual = record.rstrip(b'\0').split(b'\t', 1)
    mode, kind, oid = header.split()
    if actual.decode() != path or kind != b'blob' or mode not in (b'100644', b'100755'):
        raise ValueError('Organizational source must be a regular committed file')
    if int(_git_bytes(root, 'cat-file', '-s', oid.decode())) > limit:
        raise ValueError('Organizational source exceeds size bound')
    data = _git_bytes(root, 'cat-file', 'blob', oid.decode())
    text = data.decode('utf-8')
    if '\0' in text:
        raise ValueError('Organizational source must be UTF-8 text')
    return text, hashlib.sha256(data).hexdigest()


def bounded(value, name, maximum=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError('Invalid organizational '+name)
    return value


def prepare(root, revision, origin, known):
    if not _git_bytes(root, 'ls-tree', '-z', revision, '--', MANIFEST):
        return None
    text, digest = blob(root, revision, MANIFEST, 65536)
    data = json.loads(text)
    if data.get('version') != 1 or data.get('data_kind') not in ('OWNED_SYNTHETIC', 'REPOSITORY_SOURCES'):
        raise ValueError('Organizational manifest requires version 1 and explicit data_kind')
    decisions, teams = data.get('decisions', []), data.get('teams', [])
    if not isinstance(decisions, list) or len(decisions) > 100 or not isinstance(teams, list) or len(teams) > 50:
        raise ValueError('Organizational manifest exceeds record bounds')
    ids = [bounded(d.get('id'), 'id', 100) for d in decisions]
    if len(set(ids)) != len(ids):
        raise ValueError('Duplicate organizational decision id')
    prefix = 'org_'+digest[:24]+'_'
    docs = {}
    def excerpt(ref, role):
        path = bounded(ref.get('path'), 'source path', 1024)
        if path not in docs:
            docs[path] = blob(root, revision, path)
        source, sha = docs[path]
        lo, hi = ref.get('start_line'), ref.get('end_line')
        lines = source.splitlines()
        if type(lo) is not int or type(hi) is not int or not 1 <= lo <= hi <= len(lines) or hi-lo >= 40:
            raise ValueError('Invalid organizational excerpt range')
        content = '\n'.join(lines[lo-1:hi])
        if len(content) > 8000:
            raise ValueError('Organizational excerpt too large')
        return {'id': hashlib.sha256((sha+':'+str(lo)+':'+str(hi)+':'+role).encode()).hexdigest(),
            'path':path,'sha256':sha,'start_line':lo,'end_line':hi,'excerpt':content,
            'source_revision':revision,'role':role,'source_url':origin+'/blob/'+revision+'/'+path+'#L'+str(lo) if origin else ''}
    rows = []
    for d in decisions:
        paths = d.get('governs')
        if not isinstance(paths,list) or not 1 <= len(paths) <= 10 or any(p not in known for p in paths):
            raise ValueError('Organizational decision must govern captured files')
        if d.get('status') not in ('ACTIVE','SUPERSEDED'):
            raise ValueError('Invalid organizational decision status')
        old = d.get('supersedes')
        if old:
            prior = next((p for p in decisions if p['id'] == old), None)
            if not prior or prior['status'] != 'SUPERSEDED' or prior.get('conflict_group') != d.get('conflict_group'):
                raise ValueError('Supersession requires an explicit superseded decision in the same conflict group')
        rows.append({'id':prefix+d['id'],'rule':bounded(d.get('rule'),'rule',1000),
            'rationale':bounded(d.get('rationale'),'rationale'),'required_action':bounded(d.get('required_action'),'required action'),
            'conflict_group':bounded(d.get('conflict_group'),'conflict group',100),
            'status':d['status'],'paths':sorted(set(paths)), 'old':prefix+old if old else None,
            'document':excerpt(d['document'],'DECISION_DOCUMENT'), 'incident':excerpt(d['incident'],'MOTIVATING_INCIDENT')})
    names = set()
    for t in teams:
        owner = bounded(t.get('owner'),'team owner',150)
        if not re.fullmatch(r'@[A-Za-z0-9-]+/[A-Za-z0-9_.-]+',owner) or owner in names:
            raise ValueError('Team mapping requires a unique CODEOWNERS team handle')
        names.add(owner)
        bounded(t.get('name'),'team name',200)
    return {'sha256':digest,'source_revision':revision,'data_kind':data['data_kind'],
        'source_path':MANIFEST,'source_url':origin+'/blob/'+revision+'/'+MANIFEST if origin else '',
        'decisions':rows,'teams':teams}


def index_organization(graph, root, revision, origin, known):
    data = prepare(root, revision, origin, known)
    if data is None:
        return {'status':'NO_EXPLICIT_MANIFEST','decisions':0}
    # Called only within new-snapshot ingestion: its existing failure cleanup
    # deletes this owned graph if any write fails. Never enrich a saved graph.
    for row in data['decisions']:
        props = {k:row[k] for k in ('id','rule','rationale','required_action','conflict_group','status')}
        props.update(source_type='ORGANIZATIONAL_MANIFEST',data_kind=data['data_kind'],
            source_revision=revision,manifest_sha256=data['sha256'],source_path=MANIFEST,
            source_url=data['source_url'],scope_symbol='module_root',valid_from=0,valid_to=0,
            validity_basis='EXPLICIT_MANIFEST_AT_PINNED_REVISION_NOT_CALENDAR_VALIDITY')
        from app.db.client import db_manager
        graph.query('CREATE (d:Decision) SET d=$props SET d.embedding=vecf32($embedding)',
                    {'props':props,'embedding':db_manager.embed_text(row['rule'])})
        graph.query('MATCH (d:Decision {id:$id}) UNWIND $paths AS path MATCH (f:File {path:path}) MERGE (d)-[:GOVERNS]->(f)',row)
        for role, relationship in [('document','SUPPORTED_BY'),('incident','MOTIVATED_BY')]:
            graph.query(f'''MATCH (d:Decision {{id:$id}}) MERGE (e:OrganizationalExcerpt {{id:$excerpt_id}})
                SET e=$props MERGE (d)-[:{relationship}]->(e)''',
                {'id':row['id'],'excerpt_id':row[role]['id'],'props':row[role]})
    for row in data['decisions']:
        if row['old']:
            graph.query('MATCH (d:Decision {id:$id}),(o:Decision {id:$old}) MERGE (d)-[:SUPERSEDED]->(o)',row)
    for team in data['teams']:
        graph.query('''CREATE (t:OrganizationTeam {owner:$owner,name:$name,manifest_sha256:$sha,source_revision:$revision})
          WITH t MATCH (r:OwnershipRule)-[:DECLARES_OWNER]->(o:DeclaredOwner {name:$owner,kind:'TEAM'}),
          (r)-[:APPLIES_TO]->(f:File) MERGE (t)-[:OWNS]->(f) MERGE (t)-[:MAPPED_FROM]->(o)''',
          {'owner':team['owner'],'name':team['name'],'sha':data['sha256'],'revision':revision})
    graph.query('MATCH (m:RepoMetadata) SET m.organization_manifest_sha256=$sha,m.organization_data_kind=$kind,m.organization_status=$status',
                {'sha':data['sha256'],'kind':data['data_kind'],'status':'INDEXED'})
    return {'status':'INDEXED','decisions':len(data['decisions']),'teams':len(data['teams']),
            'data_kind':data['data_kind'],'manifest_sha256':data['sha256']}
