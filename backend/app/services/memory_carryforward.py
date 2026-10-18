"""Read-only, bounded predecessor evidence validation. Never migrate executions."""
import hashlib
import json
from app.services.common import read
from app.db.client import db_manager


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def metadata(tenant):
    rows,_=read(tenant,'''MATCH (m:RepoMetadata) RETURN m.connection_id AS connection_id,
      m.parent_snapshot AS parent_snapshot,m.source_revision AS revision,m.repository AS repository,
      m.status AS status LIMIT 2''')
    return rows[0] if len(rows)==1 else {}


def scope_receipt(tenant, paths, scope):
    # Exclude generated IDs and snapshot revisions: compare actual rule content
    # and source evidence across revisions, not revision-dependent row identities.
    governed,_=read(tenant,'''MATCH (d:Decision)-[:GOVERNS]->(f:File)
      WHERE f.path IN $paths AND d.status='ACTIVE'
      OPTIONAL MATCH (d)-[:SUPPORTED_BY]->(doc:OrganizationalExcerpt)
      OPTIONAL MATCH (d)-[:MOTIVATED_BY]->(incident:OrganizationalExcerpt)
      RETURN DISTINCT d.rule AS rule,d.status AS status,d.scope_symbol AS symbol,
        d.rationale AS rationale,d.required_action AS required_action,d.source_type AS source_type,
        d.source_path AS source_path,d.source_line AS source_line,d.manifest_sha256 AS manifest_sha256,
        doc.sha256 AS document_sha256,incident.sha256 AS incident_sha256
      ORDER BY rule,status,symbol,rationale,required_action,source_type,source_path,source_line,manifest_sha256,document_sha256,incident_sha256 LIMIT 501''',{'paths':paths})
    constraints,_=read(tenant,'''MATCH (d:Decision {source_type:'REPO_EXTRACTED_RULE'})
      WHERE d.scope='repository' OR d.target_path IN $paths
      RETURN DISTINCT d.rule AS rule,d.scope AS scope,d.target_path AS target,d.source_path AS source_path,d.source_line AS source_line
      ORDER BY rule,scope,target,source_path,source_line LIMIT 501''',{'paths':paths})
    deps=[]
    if scope=='STATIC_NEIGHBORHOOD':
        imports,_=read(tenant,'''MATCH (a:File)-[:IMPORTS]->(b:File)
          WHERE a.path IN $paths OR b.path IN $paths
          RETURN a.path AS source,b.path AS target,a.sha256 AS source_sha,b.sha256 AS target_sha
          ORDER BY source,target LIMIT 2001''',{'paths':paths})
        calls,_=read(tenant,'''MATCH (fa:File)-[:DEFINES]->(a:Function)-[r:CALLS]->(b:Function)<-[:DEFINES]-(fb:File)
          WHERE fa.path IN $paths OR fb.path IN $paths
          RETURN a.qualified_name AS source,b.qualified_name AS target,r.line AS line,fa.sha256 AS source_sha,fb.sha256 AS target_sha
          ORDER BY source,target,line LIMIT 2001''',{'paths':paths})
        deps={'imports':imports[:2000],'calls':calls[:2000]}
        complete=len(imports)<=2000 and len(calls)<=2000
    else: complete=True
    return {'scope':scope,'policy_digest':digest({'governed':governed[:500],'constraints':constraints[:500]}),
            'dependency_digest':digest(deps),'bounded_scope_complete':complete and len(governed)<=500 and len(constraints)<=500,
            'basis':'DECLARED_FILE_LOCAL_OR_ONE_HOP_STATIC_NEIGHBORHOOD_NOT_DYNAMIC_COMPLETENESS'}


def predecessor_candidates(tenant, terms, limit):
    meta=metadata(tenant);parent=meta.get('parent_snapshot')
    base={'predecessor':parent or None,'findings':[],'has_more':False,
          'mode':'READ_ONLY_REVALIDATION_ORIGINAL_FINDING_UNCHANGED',
          'test_execution_on_new_revision':False}
    if not parent: return {**base,'status':'NO_DECLARED_PREDECESSOR'}
    if parent==tenant or parent not in db_manager.list_tenant_graphs():
        return {**base,'status':'PREDECESSOR_UNAVAILABLE_OR_INVALID'}
    old=metadata(parent)
    if not meta.get('connection_id') or old.get('connection_id') != meta['connection_id'] or old.get('repository') != meta.get('repository') or old.get('status')!='READY':
        return {**base,'status':'CROSS_CONNECTION_REUSE_REFUSED'}
    rows,_=read(parent,'''MATCH (m:VerifiedFinding)
      WHERE size($terms)=0 OR any(t IN $terms WHERE toLower(m.summary) CONTAINS t OR toLower(m.evidence_note) CONTAINS t)
      RETURN m.id AS id,m.summary AS summary,m.evidence_note AS evidence_note,m.file_shas_json AS hashes,
        m.reuse_validation_json AS reuse,m.created_at AS created_at,m.verification_command AS verification_command,
        m.verification_basis AS verification_basis,m.execution_id AS execution_id,m.proposal_id AS proposal_id,
        m.base_revision AS base_revision
      ORDER BY created_at DESC,id LIMIT 101''',{'terms':terms})
    result=[]
    for row in rows[:100]:
        hashes=json.loads(row.pop('hashes'));saved=json.loads(row.pop('reuse') or '{}')
        current,_=read(tenant,'MATCH (f:File) WHERE f.path IN $paths RETURN f.path AS path,f.sha256 AS sha',{'paths':list(hashes)})
        stale=[];unknown=[]
        if hashes != {f['path']:f['sha'] for f in current}:stale.append('SUPPORTING_FILE_CHANGED_OR_MISSING')
        if not saved or saved.get('scope')=='UNSPECIFIED':unknown.append('REUSE_SCOPE_NOT_DECLARED')
        else:
            now=scope_receipt(tenant,list(hashes),saved['scope'])
            if saved['policy_digest'] != now['policy_digest']:stale.append('GOVERNING_POLICY_CHANGED')
            if saved['dependency_digest'] != now['dependency_digest']:stale.append('RECORDED_DEPENDENCY_NEIGHBORHOOD_CHANGED')
            if not saved.get('bounded_scope_complete') or not now['bounded_scope_complete']:unknown.append('RECORDED_SCOPE_EXCEEDS_BOUND')
        if row.get('execution_id') or row.get('proposal_id') or row.get('base_revision'):
            unknown.append('PREVIOUS_EXECUTION_OR_PROPOSAL_REQUIRES_NEW_REVISION_VERIFICATION')
        result.append({**row,'supporting_file_shas':hashes,'origin_tenant':parent,'origin_revision':old.get('revision'),
          'validated_for_revision':meta.get('revision'),'reuse_scope':saved.get('scope','UNSPECIFIED'),
          'status':'STALE' if stale else 'NEEDS_REVALIDATION' if unknown else 'VALID_FOR_THIS_SNAPSHOT',
          'stale_reasons':stale,'revalidation_reasons':unknown,
          'test_execution_on_new_revision':False,
          'verification_command_basis':'HISTORICAL_COMMAND_ONLY_NOT_EXECUTED_ON_NEW_REVISION'})
    return {**base,'status':'PREDECESSOR_CANDIDATES_VALIDATED','findings':result[:limit],
            'has_more':len(rows)>100 or len(result)>limit,'scan_limit':100}
