"""Disposable dependency scenarios; static impact is not proof of a runtime outage."""
from app.services.test_selection import is_test_file
import uuid
import shlex
from fastapi import HTTPException
from app.db.client import db_manager
from app.db.queries import CYPHER_BLAST_RADIUS_AUDIT, CYPHER_FILE_OWNERSHIP_AND_LINEAGE
from app.models import SandboxAuditRequest, SandboxAuditResponse, BlindAgentComparison
from app.services.ast_patch import parse_patch, apply_patch
from app.services.common import tenant_exists, read, check_file, rows, graph_payload, LOCKS


def audit_sandbox(req: SandboxAuditRequest) -> SandboxAuditResponse:
    tenant=tenant_exists(req.tenant_graph)
    if len(req.modified_files)>20 or len(req.proposed_description)>8000:
        raise HTTPException(422,'At most 20 files and 8000 description characters are supported')
    paths=list(dict.fromkeys(req.modified_files))
    if req.pr_number is not None:
        prs,_=read(tenant,'MATCH (p:PullRequest {number:$number}) RETURN p.number AS number',{'number':req.pr_number})
        if not prs:
            raise HTTPException(404,'PR is not in the ingested public snapshot')
        if not paths:
            selected,_=read(tenant,'''MATCH (:PullRequest {number:$number})-[:MODIFIES]->(f:File)
            RETURN f.path AS path ORDER BY path LIMIT 20''',{'number':req.pr_number})
            paths=[r['path'] for r in selected]
    if not paths:
        raise HTTPException(422,'Select existing modified_files or a PR with ingested Python files')
    for path in paths: check_file(tenant,path)
    with LOCKS[tenant]:
        baseline,base_ms=read(tenant,'''MATCH (target:File) WHERE target.path IN $paths
        OPTIONAL MATCH (direct:File)-[:IMPORTS]->(target)
        RETURN collect(DISTINCT direct.path) AS paths''',{'paths':paths})
        direct=set(baseline[0]['paths']) if baseline else set()
        with db_manager.ephemeral_sandbox(req.tenant_graph) as (sandbox_graph, sandbox_name, clone_ms):
            patch = None
            if req.proposed_code_patch and req.proposed_code_patch.strip():
                original = sandbox_graph.ro_query('MATCH (f:File {path:$path}) RETURN f.source_text', {'path':paths[0]}).result_set
                patch = parse_patch(req.proposed_code_patch, paths[0], original[0][0] if original else None)
            scenario='scenario_'+uuid.uuid4().hex
            patch_paths = set()
            if patch:
                patch_paths = apply_patch(sandbox_graph, patch, scenario)
            else:
                # Request has file names, not an AST diff. Add a labeled synthetic caller in
                # the clone only. Never invent real upstream edges or claim PR execution.
                sandbox_graph.query('''CREATE (sim:File {path:$scenario,source_type:'SIMULATED_PR_DEPENDENCY',
                  description:'Synthetic proposed dependency, not an ingested upstream file'})
                WITH sim UNWIND $paths AS path MATCH (f:File {path:path})
                CREATE (sim)-[:IMPORTS {source_type:'SIMULATED_PR_DEPENDENCY'}]->(f)
                WITH sim,f OPTIONAL MATCH (f)-[:DEFINES]->(target:Function)
                WITH sim,f,head(collect(target)) AS target
                CREATE (fn:Function {qualified_name:$scenario+':'+f.path+':scenario_caller',source_type:'SIMULATED_PR_DEPENDENCY'})
                CREATE (sim)-[:DEFINES]->(fn)
                FOREACH (t IN CASE WHEN target IS NULL THEN [] ELSE [target] END |
                  CREATE (fn)-[:CALLS {source_type:'SIMULATED_PR_DEPENDENCY'}]->(t))''',
                    {'paths':paths,'scenario':scenario})
            result,audit_ms=db_manager.query(sandbox_name,CYPHER_BLAST_RADIUS_AUDIT,{'modified_files':paths})
            audits=rows(result); files=set(); functions=set(); decisions={}; experts={}; lineage_ms=0.0
            for item in audits:
                files.update(p for p in item['impacted_files'] if p)
                functions.update(p for p in item['impacted_functions'] if p)
                for decision in item['active_decisions']:
                    if decision.get('id'): decisions[decision['id']]=decision
                result,ms=db_manager.ro_query(sandbox_name,CYPHER_FILE_OWNERSHIP_AND_LINEAGE,{'file_path':item['modified_file']})
                lineage_ms+=ms
                for row in rows(result):
                    for expert in row['top_experts']:
                        if expert.get('login'): experts[expert['login']]={**expert,'url':expert.get('url') or (None if expert['login'].startswith('git:') else 'https://github.com/'+expert['login'])}
            # Retain full policy provenance instead of presenting demo rules as facts.
            for ident in decisions:
                provenance,_=read(sandbox_name,'MATCH (d:Decision {id:$id}) RETURN d.source_type AS source_type',{'id':ident})
                decisions[ident].update(provenance[0])
            stale,stale_ms=read(sandbox_name,'''MATCH (d:Decision)-[:GOVERNS]->(f:File)
            WHERE f.path IN $paths RETURN d.rule AS rule,d.status AS status ORDER BY d.valid_from,d.id LIMIT 1''',{'paths':paths})
            obsolete=stale[0]['rule'] if stale and stale[0]['status']=='SUPERSEDED' else None
            real_files={p for p in files if p!=scenario}
            missed=len(real_files-direct-set(paths))
            test_paths = {r[0] for r in sandbox_graph.ro_query(
                'MATCH (f:File) RETURN DISTINCT f.path').result_set if is_test_file(r[0]) and r[0] != scenario}
            selected_tests = sorted((real_files | set(paths)) & test_paths)
            reduction = round(100 * (1-len(selected_tests)/len(test_paths)), 2) if test_paths else 0.0
            # No shell execution; quote paths and terminate options. Empty selection
            # must never silently mean 'no tests needed'.
            command = 'pytest -- ' + ' '.join(shlex.quote(p) for p in selected_tests) if selected_tests else 'pytest'
            symbols = sorted({f['qualified_name'] for f in patch['functions']} |
                {i['module'] + ('.'+i['name'] if i['name'] else '') for i in patch['imports']} |
                {c['expression'] for c in patch['calls']}) if patch else []
            from app.services.second_brain_wiki import byte_metrics
            context_slice={'modified_files':paths,'impacted_files':sorted(real_files),'impacted_functions':sorted(functions),
                'active_policies':list(decisions.values()),'candidate_tests':selected_tests,'pytest':command,
                'contributors':list(experts.values()),'provenance':'AST/static snapshot; not equivalent source or safe-skip proof'}
            source_sizes=sandbox_graph.ro_query('MATCH (f:File) WHERE f.path IN $paths RETURN f.source_utf8_bytes,f.source_chars',
                {'paths':sorted(real_files|set(paths))}).result_set
            sizes_available=bool(source_sizes) and all(isinstance(r[0],int) and isinstance(r[1],int) for r in source_sizes)
            context_measurement=byte_metrics(sum(r[0] for r in source_sizes) if sizes_available else 0,
                sum(r[1] for r in source_sizes) if sizes_available else 0,context_slice,sizes_available)
            context_measurement['slice']=context_slice
            context_measurement['basis']='Captured affected-source bytes vs explicit compact audit subset; excludes graph/UI/HTTP envelope and is not equivalent semantic content.'
            payload=graph_payload(sandbox_name,list(set(paths)|files|patch_paths),cypher=CYPHER_BLAST_RADIUS_AUDIT+'\n'+CYPHER_FILE_OWNERSHIP_AND_LINEAGE,
                                  elapsed=audit_ms+lineage_ms,impacted=True)
            for node in payload.nodes:
                if node.label == 'File' and node.title in paths:
                    node.metadata['audit_target'] = True
                node_path = node.metadata.get('path') or node.metadata.get('file_path')
                if node_path in patch_paths - set(paths) - files:
                    node.status = 'DEFAULT'
                    node.metadata['patch_dependency'] = True
        cleaned=sandbox_name not in db_manager.list_tenant_graphs()
        if not cleaned: raise HTTPException(503,'Sandbox cleanup failed; audit is not complete')
    return SandboxAuditResponse(context_window_savings=context_measurement,sandbox_graph_name=sandbox_name,sandbox_clone_time_ms=clone_ms,
        sandbox_cleaned_up=cleaned,risk_level='HIGH' if real_files or decisions else 'MEDIUM',
        impacted_files=sorted(files),impacted_functions=sorted(functions),
        impacted_test_files=selected_tests,total_repo_test_files=len(test_paths),
        test_suite_reduction_pct=reduction,recommended_pytest_command=command,
        patch_symbols_analyzed=symbols,
        active_decisions_triggered=list(decisions.values()),recommended_reviewers=list(experts.values()),
        blind_agent_comparison=BlindAgentComparison(verdict='CONTROLLED_ONE_HOP_BASELINE',
            mistake_summary=f'A measured one-hop query misses {missed} real multi-hop files. Oldest-document policy baseline is separate. Synthetic clone-only dependency is excluded from this count. Mode: {"AST_PATCH_SIMULATION additive snippet overlay" if patch else "SIMULATED_PR_DEPENDENCY"}. Static traversal, not code execution or a runtime outage prediction.',
            obsolete_rule_followed=obsolete,missed_downstream_count=missed,steps_taken=2,duration_ms=base_ms+stale_ms),subgraph=payload)
