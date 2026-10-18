"""Validate bounded explicit citations, not free-text rationale or inferred authority."""
from fastapi import HTTPException
from app.services.organization import organizational_context


def validate_references(tenant,revision,paths,refs):
    from app.services.change_lifecycle import _hashes
    if not refs:
        return {'status':'NO_VALIDATED_CITATIONS_SUPPLIED','references':[],
                'caution':'Rationale remains declared. This does not establish that no governing policy exists.'}
    evidence=organizational_context(tenant,list(paths),limit=100)
    if evidence['truncated']:
        raise HTTPException(409,'Evidence exceeds validation bound; narrow proposed scope')
    validated=[]
    for ref in refs:
        matches=[c for c in evidence['chains'] if c['decision']['id']==ref.decision_id and c['decision']['status']=='ACTIVE']
        if not matches:
            raise HTTPException(422,'Citation unknown, superseded, or unrelated to proposed paths: '+ref.decision_id)
        supporting=[]
        for chain in matches:
            d=chain['decision'];sources=[chain['document'],chain['motivating_incident']]
            if d.get('source_revision')!=revision or any(e is None for e in sources):
                raise HTTPException(409,'Citation lacks a complete pinned source chain')
            hashes=_hashes(tenant,[e['path'] for e in sources]+[d['source_path']])
            if hashes.get(d['source_path'])!=d['manifest_sha256'] or any(e['source_revision']!=revision or hashes.get(e['path'])!=e['sha256'] for e in sources):
                raise HTTPException(409,'Citation source hash/revision changed')
            if not any(e['id']==ref.excerpt_id and e['sha256']==ref.source_sha256 for e in sources):
                raise HTTPException(422,'Citation excerpt/hash does not match the selected decision chain')
            supporting.append(chain)
        validated.append({'decision_id':ref.decision_id,'excerpt_id':ref.excerpt_id,'source_sha256':ref.source_sha256,
                          'status':'VALIDATED_PINNED_SOURCE_CHAIN_NOT_APPROVAL','chains':supporting})
    return {'status':'EXPLICIT_CITATIONS_VALIDATED','references':validated,
            'gaps':evidence['gaps'],'caution':'Current source-backed applicability, not policy adjudication or approval'}
