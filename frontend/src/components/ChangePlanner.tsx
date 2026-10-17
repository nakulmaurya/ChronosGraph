"use client";
import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { readDraft, saveDraft, type ChangeDraft } from '@/lib/change-drafts';
import { request } from '@/lib/api';
import { queryString } from '@/lib/workbench';
import { changedRegion, dependencyMap, type ChangeImpact } from '@/lib/change-planning';
const CommandGraph=dynamic(()=>import('./CommandGraph'),{ssr:false});
type Captured={source:string;source_revision:string;source_sha256:string;file_path:string};
export default function ChangePlanner({tenant,revision,path,onInspect}:{tenant:string;revision:string|null;path:string;onInspect:(path:string)=>void}) {
  const [target,setTarget]=useState(path),[loaded,setLoaded]=useState<Captured|null>(null);
  const [final,setFinal]=useState(''),[deleted,setDeleted]=useState(false),[impact,setImpact]=useState<ChangeImpact|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState('');
  const [draft,setDraft]=useState<ChangeDraft|null>(null),[draftWarning,setDraftWarning]=useState('');
  const operation=useRef<AbortController|null>(null);
  useEffect(()=>{ operation.current?.abort();setTarget(path);setLoaded(null);setImpact(null);setFinal('');setDeleted(false);setError('');setBusy(false); },[tenant,revision,path]);
  useEffect(()=>{try{setDraft(revision?readDraft(sessionStorage,tenant,revision):null);}catch{setDraftWarning('Tab storage unavailable; keep this view open to retain your proposal.');}},[tenant,revision,path]);
  useEffect(()=>()=>operation.current?.abort(),[]);
  function persist(proposed:string,remove:boolean){
    if(!loaded||!revision)return;
    const value={path:loaded.file_path,revision,sha256:loaded.source_sha256,proposed,deleted:remove};
    setDraft(value);
    try{if(!saveDraft(sessionStorage,tenant,value))setDraftWarning('Draft could not be saved in this tab. Copy your proposal before navigating away.');}catch{setDraftWarning('Tab storage unavailable. Copy your proposal before navigating away.');}
  }
  function invalidate(){operation.current?.abort();setBusy(false);setImpact(null);setError('');}
  async function load(resume?:ChangeDraft){
    if(!revision)return;
    invalidate();const c=new AbortController();operation.current=c;setBusy(true);setLoaded(null);
    try {const data=await request<Captured>(`/repository/file-source?${queryString({tenant_graph:tenant,file_path:resume?.path||target,expected_revision:revision})}`,c.signal);
      if(!c.signal.aborted){
        if(resume&&(resume.revision!==data.source_revision||resume.sha256!==data.source_sha256))throw new Error('Draft baseline does not match the captured file. Nothing was restored.');
        if(!resume){try{setDraft(readDraft(sessionStorage,tenant,revision,data.file_path));}catch{setDraftWarning('Tab storage unavailable. Copy your proposal before navigating away.');}}
        setTarget(data.file_path);setLoaded(data);setFinal(resume?resume.proposed:data.source);setDeleted(resume?.deleted||false);
      }
    } catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'Source unavailable');}
    finally{if(!c.signal.aborted)setBusy(false);}
  }
  async function preview(){
    if(!loaded||!revision)return;
    invalidate();const c=new AbortController();operation.current=c;setBusy(true);
    try {const result=await request<ChangeImpact>('/diff/impact',c.signal,{tenant_graph:tenant,expected_revision:revision,file_bodies:{[loaded.file_path]:deleted?null:final}});
      if(!c.signal.aborted)setImpact(result);
    } catch(e){if(!c.signal.aborted)setError(e instanceof Error?e.message:'Preview failed');}
    finally{if(!c.signal.aborted)setBusy(false);}
  }
  const diff=loaded?changedRegion(loaded.source,deleted?'':final):null;
  return <section className="cc-change-planner" aria-label="Selected file change planner">
    <div className="cc-section-heading"><span className="cc-kicker">PLAN BEFORE YOU EDIT</span><h1>See the reach of a change.</h1><p>Start with a captured file. Compare your proposed source, then trace candidate impacts. Nothing is applied to your repository.</p></div>
    {draft&&<div className="cc-change-input"><p>Last proposal in this tab: <code>{draft.path}</code>. Bound to this saved commit; no preview results are restored.</p><button disabled={busy} onClick={()=>void load(draft)}>Resume saved draft</button></div>}
    {draftWarning&&<p role="status">{draftWarning}</p>}
    <div className="cc-change-input"><label htmlFor="change-target">Python file in selected saved version</label>
      <div><input id="change-target" value={target} onChange={e=>{invalidate();setTarget(e.target.value);setLoaded(null);}} placeholder="src/package/module.py"/>
      <button className="cc-primary" disabled={!revision||!target.trim()||busy} onClick={()=>void load()}>Load captured file</button></div>
      <p>Commit <code>{revision||'unavailable — choose a version with captured commit identity'}</code></p></div>
    {error&&<p className="cc-error" role="alert">{error}</p>}
    {busy&&<p role="status">{loaded?'Computing isolated impact…':'Loading captured source…'}</p>}
    {loaded&&<>
      <div className="cc-change-editors"><section><h2>Saved source</h2><pre aria-label="Saved source">{loaded.source}</pre><small>SHA-256 {loaded.source_sha256}</small></section>
        <section><h2>Proposed source</h2><label><input type="checkbox" checked={deleted} onChange={e=>{invalidate();setDeleted(e.target.checked);persist(final,e.target.checked);}}/> Preview deleting this file</label>
          <textarea aria-label="Proposed source" spellCheck={false} disabled={deleted} value={final} onChange={e=>{invalidate();setFinal(e.target.value);persist(e.target.value,deleted);}}/>
        </section></div>
      <details className="cc-change-diff" open><summary>Changed region · saved → proposed</summary><pre>{diff?.text}</pre>{diff?.truncated&&<p>Display limited to 240 lines; review both complete sources above.</p>}<small>Contiguous changed region, not a minimal patch. This display is never applied.</small></details>
      <button className="cc-primary" disabled={busy||(!deleted&&diff?.unchanged)} onClick={()=>void preview()}>Preview change impact</button>
    </>}
    {impact&&<section aria-label="Change impact results" className="cc-impact-results">
      <h2>{impact.impacted_files.length} candidate files · {impact.impacted_test_files.length} candidate tests</h2>
      <p role="status">{impact.sandbox_cleaned_up?'Isolated graph cleanup verified.':'Graph cleanup unverified.'} Saved source is unchanged.</p>
      <p>Before + after static reachability, not runtime proof or permission to skip other tests. {impact.unresolved_calls} unresolved function-scope call expressions.</p>
      {impact.call_coverage&&<p className="cc-help">{impact.call_coverage.after.observed} observed calls; {impact.call_coverage.after.excluded_non_function_scope} not analyzed in function scope. {impact.call_coverage.receiver_basis}.</p>}
      {!!(impact.parse_coverage.before_failed_files.length+impact.parse_coverage.after_failed_files.length)&&<p className="cc-limit">Incomplete AST coverage: {impact.parse_coverage.before_failed_files.length} before / {impact.parse_coverage.after_failed_files.length} after parse failures. Missing edges do not mean no impact.</p>}
      <div className="cc-impact-graphs">{(['before','after'] as const).map(mode=>{const view=impact.dependency_graphs[mode];return <section key={mode}><h3>{mode==='before'?'Before change':'After change'}</h3><p>File imports inside candidate impact scope. Arrows point to imported files.</p>
        <div className="cc-impact-canvas" aria-label={`${mode} dependency graph`}>{view.paths.length?<CommandGraph map={dependencyMap(view)} detail={null} functions={false} selected={loaded?.file_path||''} onPick={onInspect}/>:<p>No captured files in this view.</p>}</div>
        {(view.nodes_truncated||view.edges_truncated)&&<p className="cc-limit">Bounded view: first 30 of {view.nodes_total} candidate files and up to 120 imports. Full candidate list below.</p>}</section>;})}</div>
      <h3>Potentially broken callers</h3>{impact.potentially_broken_callers.length?<ul>{impact.potentially_broken_callers.map(c=><li key={c}><code>{c}</code></li>)}</ul>:<p>No statically resolved callers flagged. This is not proof of compatibility.</p>}
      <div className="cc-change-lists"><section><h3>Candidate files</h3>{impact.impacted_files.map(p=><button key={p} onClick={()=>onInspect(p)}>{p}</button>)}</section><section><h3>Candidate tests</h3>{impact.impacted_test_files.length?impact.impacted_test_files.map(p=><button key={p} onClick={()=>onInspect(p)}>{p}</button>):<p>No candidate tests found in the indexed radius. Run your usual checks.</p>}<pre>{impact.recommended_pytest_command||'No candidate pytest command available.'}</pre><p>Recommendation only. No test command has been executed.</p></section></div>
      <details><summary>Added and removed static dependencies</summary><pre>{JSON.stringify({added:impact.added_dependencies,removed:impact.removed_dependencies},null,2)}</pre></details>
    </section>}
  </section>;
}
