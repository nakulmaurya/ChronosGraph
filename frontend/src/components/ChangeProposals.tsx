"use client";
import {useEffect,useRef,useState} from 'react';
import {request} from '@/lib/api';
import {operatorRequest} from '@/lib/operator-api';
import {queryString} from '@/lib/workbench';
import {changedRegion,type ChangeImpact} from '@/lib/change-planning';
type Execution={id:string;provenance_kind:string;exit_code:number;output_excerpt:string;finding_id?:string};
type Proposal={id:string;task_title:string;status:string;proposal_hash:string;base_revision:string;
  proposed_files:Record<string,string|null>;base_file_shas:Record<string,string|null>;executions:Execution[];
  impact_summary:ChangeImpact&{active_rules:{id:string;rule:string}[];declared_ownership:unknown}};
export default function ChangeProposals({tenant,revision}:{tenant:string;revision:string|null}){
  const [proposals,setProposals]=useState<Proposal[]>([]),[selected,setSelected]=useState('');
  const [error,setError]=useState(''),[busy,setBusy]=useState(false),[reason,setReason]=useState('');
  const [runner,setRunner]=useState(false),[ack,setAck]=useState(false),[tick,setTick]=useState(0);
  const [diffs,setDiffs]=useState<Record<string,string>>({}),[notice,setNotice]=useState('');
  const action=useRef<AbortController|null>(null),runKeys=useRef<Record<string,string>>({});
  useEffect(()=>{
    const c=new AbortController();let timer:ReturnType<typeof setTimeout>|undefined;
    setProposals([]);setSelected('');setError('');setRunner(false);
    async function poll(){
      if(!revision)return;
      try{const data=await request<{proposals:Proposal[]}>(`/proposals?${queryString({tenant_graph:tenant,revision})}`,c.signal);
        if(!c.signal.aborted){setProposals(data.proposals);timer=setTimeout(()=>void poll(),2500);}
      }catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'Proposal list unavailable; automatic refresh stopped.');}
    }
    void poll();
    void request<{enabled:boolean}>(`/proposals/runner-capabilities?${queryString({tenant_graph:tenant})}`,c.signal).then(r=>{if(!c.signal.aborted)setRunner(r.enabled);}).catch(()=>{});
    return()=>{c.abort();clearTimeout(timer);action.current?.abort();};
  },[tenant,revision,tick]);
  const p=proposals.find(row=>row.id===selected);
  useEffect(()=>{
    const c=new AbortController();setDiffs({});setReason('');setAck(false);
    if(p&&revision)void Promise.all(Object.entries(p.proposed_files).map(async([path,body])=>{
      let before='';if(p.base_file_shas[path])before=(await request<{source:string}>(`/repository/file-source?${queryString({tenant_graph:tenant,expected_revision:revision,file_path:path})}`,c.signal)).source;
      return [path,changedRegion(before,body||'').text] as const;
    })).then(entries=>{if(!c.signal.aborted)setDiffs(Object.fromEntries(entries));}).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    return()=>c.abort();
  },[p?.id,tenant,revision]);
  async function decide(approve:boolean){
    if(!p||!revision)return;const c=new AbortController();action.current=c;setBusy(true);setError('');
    try{const updated=await operatorRequest<Proposal>(`/proposals/${p.id}/decision`,{tenant_graph:tenant,expected_revision:revision,proposal_hash:p.proposal_hash,approve,reason},c.signal);
      if(!c.signal.aborted){setProposals(rows=>rows.map(row=>row.id===updated.id?updated:row));setNotice(approve?'Exact proposal approved. Nothing has been applied.':'Proposal rejected.');}}
    catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'Decision failed');}
    finally{if(!c.signal.aborted)setBusy(false);}
  }
  async function execute(){
    if(!p||!revision||!ack)return;const c=new AbortController();action.current=c;setBusy(true);setError('');
    const key=runKeys.current[p.id]||crypto.randomUUID();runKeys.current[p.id]=key;
    try{const e=await operatorRequest<Execution>(`/proposals/${p.id}/execute-disposable-worktree`,{tenant_graph:tenant,expected_revision:revision,proposal_hash:p.proposal_hash,idempotency_key:key,acknowledge_code_execution:ack},c.signal);
      if(!c.signal.aborted){setProposals(rows=>rows.map(row=>row.id===p.id?{...row,status:e.exit_code===0?'EXECUTED_VERIFIED':'EXECUTED_FAILED',executions:[e,...row.executions]}:row));setNotice(`Observed candidate pytest exit code: ${e.exit_code}. Saved repository unchanged.`);}}
    catch(e){if(!c.signal.aborted)setError((e instanceof Error?e.message:'Execution status unavailable')+'. Check the proposal record before retrying; closing this page does not cancel server execution.');}
    finally{if(!c.signal.aborted)setBusy(false);}
  }
  return <section className="cc-change-input" aria-label="Pending and recent change proposals">
    <h2>Review your agent’s proposed changes.</h2><p>Durable proposals from connected clients. Approve the exact version—not an open-ended permission to edit.</p>
    <label htmlFor="proposal-select">Pending &amp; recent proposals</label><select id="proposal-select" disabled={busy} value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Select a proposal ({proposals.length})</option>{proposals.map(row=><option key={row.id} value={row.id}>{row.task_title} · {row.status}</option>)}</select>
    {!proposals.length&&<p>No proposals in the latest bounded selection. Connect an MCP client and call propose_change_for_approval.</p>}
    {error&&<p role="alert" className="cc-error">{error}</p>}<button disabled={busy} onClick={()=>setTick(n=>n+1)}>Refresh proposals</button>
    {notice&&<p role="status">{notice}</p>}
    {p&&<><h3>{p.task_title}</h3><p>Status: <strong>{p.status}</strong></p><p>Base commit <code>{p.base_revision}</code></p><p>Exact proposal hash <code>{p.proposal_hash}</code></p>
      <details><summary>Base file hashes</summary><pre>{JSON.stringify(p.base_file_shas,null,2)}</pre></details>
      {Object.entries(p.proposed_files).map(([path,body])=><details key={path}><summary>{path} · {body===null?'Delete':'Replacement'}</summary><pre>{diffs[path]||'Loading captured-source comparison…'}</pre><details><summary>Complete proposed source</summary><pre>{body??'(deleted)'}</pre></details></details>)}
      <h3>What could be affected</h3><p>{p.impact_summary.impacted_files.length} candidate files · {p.impact_summary.impacted_test_files.length} candidate tests. Static candidates, not safe-skip proof.</p>
      <h4>Potentially broken callers</h4><pre>{p.impact_summary.potentially_broken_callers.join('\n')||'No resolved callers flagged; not a compatibility guarantee.'}</pre>
      <h4>Candidate pytest files</h4><pre>{p.impact_summary.recommended_pytest_command||'No candidate command available'}</pre><button onClick={()=>void navigator.clipboard.writeText(p.impact_summary.recommended_pytest_command).then(()=>setNotice('Copied candidate test command.')).catch(()=>setError('Clipboard unavailable; select and copy the command.'))}>Copy candidate test command</button>
      <details><summary>Added vs. removed dependencies</summary><pre>{JSON.stringify({added:p.impact_summary.added_dependencies,removed:p.impact_summary.removed_dependencies},null,2)}</pre></details>
      <details><summary>Applicable rules &amp; declared owners</summary><pre>{JSON.stringify({rules:p.impact_summary.active_rules,owners:p.impact_summary.declared_ownership},null,2)}</pre></details>
      {p.status==='PROPOSED'&&<><label>Decision reason<input value={reason} onChange={e=>setReason(e.target.value)} maxLength={1000}/></label><button className="cc-primary" disabled={busy||!reason.trim()} onClick={()=>void decide(true)}>Approve exact proposal</button><button disabled={busy||!reason.trim()} onClick={()=>void decide(false)}>Reject proposal</button></>}
      {runner&&p.status==='APPROVED'&&<><label><input type="checkbox" checked={ack} onChange={e=>setAck(e.target.checked)}/> Run trusted repository code on this machine. A disposable worktree is not a security sandbox.</label><button disabled={busy||!ack} onClick={()=>void execute()}>Run candidate tests in disposable worktree</button></>}
      {p.executions.map(e=><article key={e.id}><h4>{e.provenance_kind} · exit {e.exit_code}</h4><pre>{e.output_excerpt}</pre>{e.finding_id&&<p>Memory evidence: <code>{e.finding_id}</code></p>}</article>)}
    </>}
  </section>;
}
