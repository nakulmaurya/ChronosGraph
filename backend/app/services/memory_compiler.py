"""Persistent deterministic role workflow and guarded playbook replay.

No model is called. tokens_used is zero; token_savings_pct is undefined and
represented by 0.0 in the locked numeric contract, with an explicit explanation.
This verifies policy-triage mechanics, not autonomous debugging or a repair.
"""
from __future__ import annotations
import json
import time
import uuid
from fastapi import HTTPException
from app.db.client import db_manager
from app.db.queries import CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH
from app.models import InvestigationRunRequest, InvestigationRunResponse, BlindAgentComparison
from app.services.context_slice import measure_context
from app.services.common import (tenant_exists, bounded_text, read, rows, fingerprint,
                                 graph_payload, LOCKS)

# Only these fixed read-only tools can be replayed; no arbitrary stored Cypher executes.
TOOLS = {
 'inspect_candidate': '''MATCH (f:File {path:$path}) OPTIONAL MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(f)
    RETURN f.path AS path,collect(d.id) AS policies''',
 'inspect_target': '''MATCH (f:File {path:$path}) OPTIONAL MATCH (f)-[:DEFINES]->(fn:Function)
    RETURN f.path AS path,count(fn) AS functions''',
 'inspect_policies': '''MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(:File {path:$path})
    OPTIONAL MATCH (d)-[:SUPERSEDED]->(old:Decision)
    RETURN d.id AS id,d.rule AS rule,d.source_type AS source_type,collect(old.rule) AS replaced_rules''',
 'verify_policy': '''MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(:File {path:$path})
    RETURN count(d) AS active_count''',
}


def _execute(tenant, step):
    tool = step['tool']
    if tool not in TOOLS or set(step['params']) != {'path'}:
        raise HTTPException(409,'Stored playbook has an unapproved tool contract')
    data,elapsed=read(tenant,TOOLS[tool],step['params'])
    if tool=='inspect_target' and not data:
        raise HTTPException(409,'Target file no longer exists')
    if tool=='inspect_policies' and not data:
        raise HTTPException(409,'No active policy remains; rerun cold investigation')
    if tool=='verify_policy' and (not data or data[0]['active_count']<1):
        raise HTTPException(409,'Goal verification failed')
    return data,elapsed


def _log_states(tenant, inv_id, step_log, warm=False):
    db_manager.query(tenant,'''CREATE (i:Investigation {id:$id,execution_mode:$mode,
      source_type:'DETERMINISTIC_POLICY_TRIAGE',model_calls:0,created_at:$now})
      CREATE (s:StateNode {id:$id+':start',state_type:'START',title:'Policy triage start'})
      CREATE (i)-[:HAS_STATE]->(s)''',{'id':inv_id,'now':int(time.time()*1000),'mode':'compiled_playbook' if warm else 'cold_multi_agent'})
    current=inv_id+':start'
    for idx,step in enumerate(step_log):
        ident=inv_id+':'+str(idx)
        parent=inv_id+':start' if step['dead_end'] else current
        kind='DEAD_END' if step['dead_end'] else ('VERIFIED_GOAL' if step['tool']=='verify_policy' else 'INTERMEDIATE')
        db_manager.query(tenant,'''MATCH (inv:Investigation {id:$inv}),(parent:StateNode {id:$parent})
          CREATE (s:StateNode {id:$id,state_type:$kind,title:$title,tool_name:$tool,
            observation_json:$observation,source_type:'DETERMINISTIC_POLICY_TRIAGE'})
          CREATE (inv)-[:HAS_STATE]->(s)
          CREATE (parent)-[:ACTION_TAKEN {agent_name:$agent,tool_name:$tool,
            cypher_executed:$cypher,params_json:$params,tokens_used:0,duration_ms:$elapsed,
            outcome:$outcome}]->(s)''',{
                'inv':inv_id,'parent':parent,'id':ident,'kind':kind,'title':step['summary'],
                'tool':step['tool'],'agent':step['agent'],'cypher':TOOLS[step['tool']],
                'params':json.dumps(step['params']),'elapsed':step['duration_ms'],
                'observation':json.dumps(step['observation']),
                'outcome':'NO_GOVERNING_POLICY_ON_CANDIDATE' if step['dead_end'] else 'VERIFIED_READ'})
        if not step['dead_end']: current=ident


def run_investigation(req: InvestigationRunRequest) -> InvestigationRunResponse:
    tenant=tenant_exists(req.tenant_graph)
    issue=bounded_text(req.issue_description,'issue_description')
    with LOCKS[tenant]:
        return _run_locked(tenant,issue,req.execution_mode)


def _run_locked(tenant,issue,mode):
    started=time.perf_counter(); inv_id='inv_'+uuid.uuid4().hex
    version=fingerprint(tenant)
    signature=db_manager.embed_text(issue)
    warm=mode=='compiled_playbook'
    cold_ms=0.0
    if warm:
        found,_=read(tenant,'''CALL db.idx.vector.queryNodes('AnomalySignature','embedding',4,vecf32($embedding))
          YIELD node,score MATCH (node)-[:COMPILED_AS]->(p:ProceduralPlaybook)
          WHERE node.pattern_text=$issue AND p.fingerprint=$version
          RETURN p.id AS id,p.compiled_steps_json AS steps,p.cold_duration_ms AS cold_ms,
          p.target_path AS path,p.context_measurement_json AS context,score ORDER BY p.created_at DESC LIMIT 1''',
          {'embedding':signature,'issue':issue,'version':version})
        if not found:
            raise HTTPException(409,'No exact, current playbook found. Run cold_multi_agent first; overrides invalidate old playbooks.')
        playbook_id=found[0]['id']; plan=json.loads(found[0]['steps'])
        target=found[0]['path']; cold_ms=found[0]['cold_ms']
        if len(plan)>12 or len(plan)<1:
            raise HTTPException(409,'Invalid compiled playbook length')
    else:
        # Select a policy-governed file using literal file mention first, lexical
        # retrieval second. Never claim an arbitrary issue has been diagnosed.
        candidates,_=read(tenant,'''MATCH (d:Decision {status:'ACTIVE'})-[:GOVERNS]->(f:File)
          RETURN DISTINCT f.path AS path ORDER BY path''')
        if not candidates: raise HTTPException(409,'No active policy available for triage')
        mentioned=[r['path'] for r in candidates if r['path'] in issue]
        if mentioned: target=mentioned[0]
        else:
            ranked,_=read(tenant,'''CALL db.idx.vector.queryNodes('Decision','embedding',8,vecf32($embedding))
              YIELD node,score MATCH (node)-[:GOVERNS]->(f:File) WHERE node.status='ACTIVE'
              RETURN f.path AS path ORDER BY score LIMIT 1''',{'embedding':signature})
            target=ranked[0]['path'] if ranked else candidates[0]['path']
        alternatives,_=read(tenant,'''MATCH (f:File) WHERE f.path<>$path
          AND NOT (f)<-[:GOVERNS]-(:Decision {status:'ACTIVE'})
          RETURN f.path AS path ORDER BY path LIMIT 2''',{'path':target})
        if len(alternatives)!=2:
            raise HTTPException(409,'Need two alternative files without governing policies for the labeled branching scenario')
        plan=[{'agent':'Scout','tool':'inspect_candidate','params':{'path':r['path']},'dead_end':True,
               'summary':'No governing policy on alternate candidate '+r['path']} for r in alternatives]
        plan.extend([
          {'agent':'Scout','tool':'inspect_target','params':{'path':target},'dead_end':False,'summary':'Locate selected target and definitions'},
          {'agent':'Historian','tool':'inspect_policies','params':{'path':target},'dead_end':False,'summary':'Retrieve current policy and replaced rules'},
          {'agent':'Verifier','tool':'verify_policy','params':{'path':target},'dead_end':False,'summary':'Verify an active governing policy exists'},
        ])
        playbook_id='playbook_'+uuid.uuid4().hex
    if warm:
        context = json.loads(found[0]['context']) if found[0].get('context') else measure_context(tenant,target,[target])
        if not found[0].get('context'):
            context['context_measurement_status'] = 'LEGACY_PLAYBOOK_NO_COLD_BASELINE'
            context['raw_files_context_tokens'] = context['raw_files_context_chars'] = context['raw_files_context_bytes'] = 0
            context['context_token_reduction_pct'] = 0.0
    else:
        context = measure_context(tenant,target,[s['params']['path'] for s in plan])
    observations=[]
    for step in plan:
        data,elapsed=_execute(tenant,step)
        if step.get('dead_end') and any(r.get('policies') for r in data):
            raise HTTPException(409,'Candidate has governing policies; branching assumptions changed')
        observations.append({**step,'duration_ms':elapsed,'observation':data,'tokens_used':0,
                             'execution_provider':'DETERMINISTIC_READ_ONLY_TOOL'})
    _log_states(tenant,inv_id,observations,warm)
    result,compile_ms=db_manager.query(tenant,CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH,{'investigation_id':inv_id})
    compiled=rows(result)
    if not compiled or not compiled[0]['compiled_steps']:
        raise HTTPException(409,'No verified path exists; no playbook was saved')
    retained_names=[s['tool'] for s in compiled[0]['compiled_steps']]
    retained=[s for s in plan if not s.get('dead_end')]
    if retained_names != [s['tool'] for s in retained]:
        raise HTTPException(409,'Compiled path and execution plan disagree')
    payload=graph_payload(tenant,investigation_id=inv_id,
                          cypher=CYPHER_COMPILE_PLAYBOOK_SHORTEST_PATH,elapsed=compile_ms)
    duration=round((time.perf_counter()-started)*1000,3)
    if not warm:
        db_manager.query(tenant,'''MATCH (inv:Investigation {id:$inv})
          CREATE (a:AnomalySignature {id:$signature,pattern_text:$issue,embedding:vecf32($embedding)})
          CREATE (p:ProceduralPlaybook {id:$id,compiled_steps_json:$steps,fingerprint:$version,
            cold_duration_ms:$duration,target_path:$path,created_at:$now,tokens_used:0,context_measurement_json:$context,
            benchmark_status:'TOKEN_SAVINGS_UNMEASURED_NO_MODEL',source_type:'DETERMINISTIC_POLICY_TRIAGE'})
          CREATE (a)-[:COMPILED_AS]->(p) CREATE (inv)-[:COMPILED]->(p)''',
          {'inv':inv_id,'signature':'sig_'+uuid.uuid4().hex,'issue':issue,'embedding':signature,
           'id':playbook_id,'steps':json.dumps(retained),'version':version,'duration':duration,
           'path':target,'context':json.dumps(context),'now':int(time.time()*1000)})
        # Include actual persistence overhead in wall time, without sleeps or multipliers.
        duration=round((time.perf_counter()-started)*1000,3)
        db_manager.query(tenant,'MATCH (p:ProceduralPlaybook {id:$id}) SET p.cold_duration_ms=$duration',
                         {'id':playbook_id,'duration':duration})
    from app.services.second_brain_wiki import compact_snapshot
    resume = compact_snapshot(tenant,target)
    # Recovery reads are part of the actual request work, not hidden from timing.
    duration=round((time.perf_counter()-started)*1000,3)
    if not warm:
        db_manager.query(tenant,'MATCH (p:ProceduralPlaybook {id:$id}) SET p.cold_duration_ms=$duration',
                         {'id':playbook_id,'duration':duration})
    return InvestigationRunResponse(resume_snapshot=resume,investigation_id=inv_id,execution_mode=mode,**context,
      root_cause_summary=f'Policy-triage goal verified for {target}. This does not establish a runtime bug cause or fix. Scout/Historian/Verifier are deterministic role tools, not LLM agents. No model called: token savings are unmeasured (numeric 0 is a contract sentinel).',
      total_steps_executed=len(observations),pruned_golden_steps=len(retained),tokens_used=0,
      duration_ms=duration,token_savings_pct=0.0,
      latency_speedup_factor=round(cold_ms/duration,3) if warm and duration else 1.0,
      agent_handoff_log=observations,compiled_playbook_id=playbook_id,
      blind_agent_comparison=BlindAgentComparison(verdict='TOKEN_BENCHMARK_UNMEASURED_NO_MODEL',
        mistake_summary='Controlled cold workflow has 5 read-only tool calls; shortestPath retains 3, not 2. Replay executes those 3 again. Wall-clock timing is measured, not guaranteed. No billed tokens or autonomous model benchmark exist.',
        steps_taken=5,tokens_burned=0,duration_ms=cold_ms if warm else duration),subgraph=payload)
