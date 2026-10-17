"use client";
import {useEffect,useRef,useState} from 'react';
import {API_BASE,request} from '@/lib/api';
import {operatorRequest} from '@/lib/operator-api';
import {queryString} from '@/lib/workbench';
type Replay={total_steps_executed:number;pruned_golden_steps:number;duration_ms:number;compiled_context_slice_preview:string;agent_handoff_log:unknown[];subgraph:{cypher_executed:string}};
export default function TrackTools({tenant,revision,path,kind,onPolicyChanged}:{tenant:string;revision:string|null;path:string;kind:'memory'|'ownership';onPolicyChanged:()=>void}){
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const [rule,setRule]=useState(''),[reason,setReason]=useState(''),[confirm,setConfirm]=useState(false);
  const [replay,setReplay]=useState<Replay|null>(null),[cold,setCold]=useState<number|null>(null);
  const [resume,setResume]=useState(''),[wiki,setWiki]=useState('');
  const op=useRef<AbortController|null>(null);
  useEffect(()=>{op.current?.abort();setBusy(false);setError('');setNotice('');setReplay(null);setCold(null);setResume('');setWiki('');setRule('');setReason('');setConfirm(false);return()=>op.current?.abort();},[tenant,revision,path,kind]);
  async function run(fn:(signal:AbortSignal)=>Promise<void>){op.current?.abort();const c=new AbortController();op.current=c;setBusy(true);setError('');try{await fn(c.signal);}catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'Action failed');}finally{if(!c.signal.aborted)setBusy(false);}}
  const qs=queryString({tenant_graph:tenant,...(path?{file_path:path}:{})});
  async function play(warm:boolean,signal:AbortSignal){
    const d=await request<Replay>('/track2/investigate',signal,{tenant_graph:tenant,issue_description:`Review current policy for ${path}`,execution_mode:warm?'compiled_playbook':'cold_multi_agent'});
    if(signal.aborted)return;setReplay(d);if(!warm)setCold(d.total_steps_executed);
  }
  async function compact(signal:AbortSignal){const data=await request<{precompact_resume_markdown:string}>('/brain/lint-and-compact',signal,{tenant_graph:tenant,file_path:path||null});if(!signal.aborted)setResume(data.precompact_resume_markdown);}
  return <section className="cc-track-tools" aria-label={kind==='memory'?'Playbook and session recovery':'Policy decisions and portable notes'}>
    {error&&<p role="alert" className="cc-error">{error}</p>}{notice&&<p role="status">{notice}</p>}
    {kind==='memory'?<>
      <section className="cc-change-input"><h2>Remember the useful path.</h2><p>Review policy once, then replay the retained read-only steps with shortestPath. This controlled workflow uses deterministic tools, not autonomous model agents.</p>
        <p>Target: <code>{path||'Select a Python file in Repository first'}</code></p>
        <button disabled={busy||!path} onClick={()=>void run(s=>play(false,s))}>Run policy investigation</button><button disabled={busy||!path||cold===null} onClick={()=>void run(s=>play(true,s))}>Replay verified path</button>
        {replay&&<><p>{cold!==null?`${cold} cold actions → `:''}{replay.total_steps_executed} actions this run · {replay.duration_ms.toFixed(2)} ms</p><details><summary>Tool handoff and native query</summary><pre>{JSON.stringify(replay.agent_handoff_log,null,2)}</pre><pre>{replay.subgraph.cypher_executed}</pre></details></>}
      </section>
      <section className="cc-change-input"><h2>Pick up after a context reset.</h2><p>Generate a current ResumeSnapshot.md for manual /compact recovery. Size is measured per snapshot, not a fixed promise.</p><button disabled={busy} onClick={()=>void run(compact)}>Prepare recovery note</button>
        {resume&&<><p>{new TextEncoder().encode(resume).length} UTF-8 bytes</p><pre>{resume}</pre><button onClick={()=>void navigator.clipboard.writeText(resume).then(()=>setNotice('Recovery note copied. Refresh current context before replay.')).catch(()=>setError('Select and copy the note manually.'))}>Copy ResumeSnapshot.md</button></>}
      </section>
    </>:<>
      <section className="cc-change-input"><h2>Keep the current decision clear.</h2><p>Record an explicit local policy override. The old rule stays visible as history; dependent proposals and findings become stale.</p><p>Target: <code>{path||'Select a Python file first'}</code></p>
        <label>New rule<textarea value={rule} onChange={e=>setRule(e.target.value)} maxLength={8000}/></label><label>Why this replaces the old decision<textarea value={reason} onChange={e=>setReason(e.target.value)} maxLength={8000}/></label>
        <label><input type="checkbox" checked={confirm} onChange={e=>setConfirm(e.target.checked)}/> Confirm this file-wide local policy change.</label>
        <button disabled={busy||!path||!revision||!confirm||!rule.trim()||!reason.trim()} onClick={()=>void run(async signal=>{
          await operatorRequest('/command-center/policy-override',{tenant_graph:tenant,expected_revision:revision,target_file_path:path,new_rule_text:rule,rationale:reason,scope_symbol:'module_root',author_handle:'local-operator'},signal);
          if(!signal.aborted){setNotice('Policy recorded. Dependent evidence must be rechecked.');setConfirm(false);onPolicyChanged();}
        })}>Record policy override</button>
      </section>
      <section className="cc-change-input"><h2>Take connected notes with you.</h2><p>Three-layer Obsidian vault: captured evidence, linked notes, and portable agent guidance. Source remains untrusted evidence.</p>
        <button disabled={busy} onClick={()=>void run(async signal=>{const d=await request<{wiki_markdown:string}>(`/brain/wiki-slice?${qs}`,signal);if(!signal.aborted)setWiki(d.wiki_markdown);})}>Preview [[Wikilink]] note</button>
        <button disabled={busy} onClick={()=>void run(async signal=>{const response=await fetch(`${API_BASE}/brain/obsidian-vault.zip?${qs}`,{signal});if(!response.ok)throw new Error('Vault export failed');const blob=await response.blob();if(signal.aborted)return;const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download=tenant+'-obsidian-vault.zip';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);setNotice('Obsidian vault downloaded.');})}>Download Obsidian vault (.zip)</button>
        {wiki&&<pre>{wiki}</pre>}
      </section>
    </>}
  </section>;
}
