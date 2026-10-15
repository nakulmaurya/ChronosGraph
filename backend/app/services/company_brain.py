"""Status-aware retrieval and atomic file-policy overrides; no model claims."""
import time
import uuid
from fastapi import HTTPException
from app.db.client import db_manager
from app.db.queries import (CYPHER_HYBRID_VECTOR_DECISION_SEARCH,
    CYPHER_FILE_OWNERSHIP_AND_LINEAGE, CYPHER_SUPERSEDE_DECISION)
from app.models import (BrainQueryRequest, PolicyOverrideRequest, PolicyLineageResponse, BlindAgentComparison)
from app.services.common import (tenant_exists, check_file, bounded_text, read, graph_payload, LOCKS)


def find_true_code_owners(tenant_graph: str, file_path: str):
    tenant_exists(tenant_graph); check_file(tenant_graph,file_path)
    result, _ = read(tenant_graph, CYPHER_FILE_OWNERSHIP_AND_LINEAGE, {'file_path': file_path})
    return [expert for item in result for expert in item['top_experts'] if expert.get('login')]


def ask_brain(req: BrainQueryRequest) -> PolicyLineageResponse:
    tenant = tenant_exists(req.tenant_graph)
    question = bounded_text(req.question,'question')
    with LOCKS[tenant]:
        hybrid, hybrid_ms = read(tenant, CYPHER_HYBRID_VECTOR_DECISION_SEARCH,
            {'query_embedding':db_manager.embed_text(question)})
        if req.file_path:
            path = check_file(tenant, req.file_path)
        elif hybrid:
            path = hybrid[0]['governed_file']
        else:
            return PolicyLineageResponse(file_path='',active_decisions=[],superseded_decisions=[],top_experts=[],
                blind_agent_comparison=BlindAgentComparison(verdict='NO_MATCH',
                    mistake_summary='No active rule matched the lexical vector search. Specify a file path.'),
                subgraph=graph_payload(tenant,cypher=CYPHER_HYBRID_VECTOR_DECISION_SEARCH,elapsed=hybrid_ms))
        lineage, lineage_ms = read(tenant,CYPHER_FILE_OWNERSHIP_AND_LINEAGE,{'file_path':path})
        policies, policy_ms = read(tenant,'''MATCH (d:Decision)-[:GOVERNS]->(:File {path:$file_path})
        RETURN d ORDER BY d.valid_from,d.id''',{'file_path':path})
        active, old = [], []
        for item in policies:
            p = dict(item['d'].properties); p.pop('embedding',None)
            (active if p['status']=='ACTIVE' else old).append(p)
        baseline, base_ms = read(tenant,'''MATCH (d:Decision)-[:GOVERNS]->(:File {path:$file_path})
        RETURN d.rule AS rule,d.status AS status ORDER BY d.valid_from,d.id LIMIT 1''',{'file_path':path})
        obsolete = baseline[0]['rule'] if baseline and baseline[0]['status']=='SUPERSEDED' else None
        baseline_note = ('Controlled oldest-document baseline selected an obsolete rule.' if obsolete else
                         'Controlled oldest-document baseline did not select a superseded rule.')
        baseline_note += ' This is a deterministic comparison, not a measured LLM/RAG result. Demo policies are labeled; vectors are lexical hashes, not semantic embeddings.'
        experts = [e for item in lineage for e in item['top_experts'] if e.get('login')]
        return PolicyLineageResponse(file_path=path,active_decisions=active,superseded_decisions=old,
            top_experts=experts,blind_agent_comparison=BlindAgentComparison(
                verdict='CONTROLLED_STALE_RULE' if obsolete else 'CONTROLLED_BASELINE_NO_ERROR',
                mistake_summary=baseline_note,obsolete_rule_followed=obsolete,steps_taken=1,duration_ms=base_ms),
            subgraph=graph_payload(tenant,[path],cypher=CYPHER_HYBRID_VECTOR_DECISION_SEARCH+'\n'+CYPHER_FILE_OWNERSHIP_AND_LINEAGE,
                elapsed=hybrid_ms+lineage_ms+policy_ms))


def override_policy(req: PolicyOverrideRequest) -> PolicyLineageResponse:
    tenant = tenant_exists(req.tenant_graph)
    check_file(tenant,req.target_file_path)
    bounded_text(req.new_rule_text,'new_rule_text'); bounded_text(req.rationale,'rationale')
    bounded_text(req.scope_symbol,'scope_symbol',256); bounded_text(req.author_handle,'author_handle',128)
    with LOCKS[tenant]:
        active,_=read(tenant,'''MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(:File {path:$path})
        RETURN d.scope_symbol AS scope''',{'path':req.target_file_path})
        # The locked canonical query supersedes ALL active decisions on a file.
        # Refuse ambiguous scopes rather than silently retire unrelated rules.
        if any(item['scope'] != req.scope_symbol for item in active):
            raise HTTPException(409,'Canonical override is file-wide. Match the existing scope; mixed-scope overrides require a contract change.')
        timestamp=int(time.time())
        ident='override_'+uuid.uuid4().hex
        db_manager.query(tenant,CYPHER_SUPERSEDE_DECISION,{
            'file_path':req.target_file_path,'scope_symbol':req.scope_symbol,
            'timestamp':timestamp,'new_id':ident,'new_rule':req.new_rule_text,
            'rationale':req.rationale,'source_url':'chronosgraph://local-policy/'+ident,
            'embedding':db_manager.embed_text(req.new_rule_text)})
        # Author and transaction-time provenance are written in the same in-process lock.
        # Supersession itself above is one atomic Cypher query.
        db_manager.query(tenant,'''MATCH (d:Decision {id:$id}) SET d.author_handle=$author,
        d.recorded_from=$timestamp,d.recorded_to=0,d.time_basis='UNIX_EPOCH_SECONDS'
        WITH d OPTIONAL MATCH (d)-[:SUPERSEDED]->(old:Decision) SET old.recorded_to=$timestamp''',
            {'id':ident,'author':req.author_handle,'timestamp':timestamp})
        return ask_brain(BrainQueryRequest(tenant_graph=tenant,question=req.new_rule_text,file_path=req.target_file_path))
