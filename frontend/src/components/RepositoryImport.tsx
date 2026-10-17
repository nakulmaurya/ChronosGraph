"use client";
import { useEffect, useRef, useState } from "react";
import { X, GitBranch, Loader2, Check } from "lucide-react";
import { API_BASE, request } from "@/lib/api";
import type { ImportJob } from "@/lib/command-center";
import GitHubImportGuide from "./GitHubImportGuide";
export default function RepositoryImport({ close, complete }: { close: () => void; complete: (tenant: string) => void }) {
  const dialog=useRef<HTMLDialogElement>(null);
  const [url,setUrl]=useState(""); const [branch,setBranch]=useState(""); const [commit,setCommit]=useState("");
  const [enabled,setEnabled]=useState<boolean|null>(null); const [job,setJob]=useState<ImportJob|null>(null); const [error,setError]=useState(""); const [sending,setSending]=useState(false);
  const ctrl=useRef<AbortController|null>(null); const opened=useRef(false);
  useEffect(() => {
    dialog.current?.showModal(); const c=new AbortController(); ctrl.current=c;
    request<{enabled:boolean}>("/imports/capabilities",c.signal).then(r=>setEnabled(r.enabled)).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    const saved=localStorage.getItem("chronosgraph-import-job");
    if(saved) request<ImportJob>(`/imports/${encodeURIComponent(saved)}`,c.signal).then(setJob).catch(()=>localStorage.removeItem("chronosgraph-import-job"));
    return ()=>c.abort();
  },[]);
  useEffect(()=>{
    if(job?.status!=="RUNNING")return;
    const c=new AbortController(); const timer=setInterval(()=>{
      request<ImportJob>(`/imports/${job.id}`,c.signal).then(setJob).catch(e=>{if(!c.signal.aborted)setError(e.message);});
    },1500); return ()=>{clearInterval(timer);c.abort();};
  },[job?.id,job?.status]);
  useEffect(()=>{if(job?.status==="COMPLETE"&&!opened.current){opened.current=true;localStorage.removeItem("chronosgraph-import-job");complete(job.tenant_graph);}},[job,complete]);
  async function start() {
    setSending(true);setError("");
    try {
      const response=await fetch(`${API_BASE}/imports`,{method:"POST",credentials:"omit",signal:AbortSignal.timeout(30000),headers:{"Content-Type":"application/json","X-ChronosGraph-Action":"public-import"},body:JSON.stringify({url:url.trim(),branch:branch.trim()||"main",commit:commit.trim()})});
      const data=await response.json(); if(!response.ok)throw new Error(typeof data.detail==="string"?data.detail:"Import request was rejected");
      localStorage.setItem("chronosgraph-import-job",data.id);setJob(data);
    }catch(e){setError(e instanceof Error?e.message:"Import unavailable");}finally{setSending(false);}
  }
  const running=job?.status==="RUNNING";
  return <dialog ref={dialog} className="cc-dialog" onCancel={close}><div className="cc-dialog-heading"><div><span className="cc-kicker">YOUR WORKSPACE</span><h2>Bring a repository in.</h2></div><button aria-label="Close repository import" onClick={close}><X size={18}/></button></div>
    <p>Explore dependencies, inspect functions, and preview changes. Start with a public Python repository.</p>
    <label>GitHub repository<input autoFocus placeholder="https://github.com/pallets/click" value={url} onChange={e=>setUrl(e.target.value)} disabled={running}/></label>
    <div className="cc-form-row"><label>Branch <small>optional · main</small><input placeholder="main" value={branch} onChange={e=>setBranch(e.target.value)} disabled={running}/></label><label>Commit hash <small>optional · latest on branch</small><input placeholder="Latest branch commit" value={commit} onChange={e=>setCommit(e.target.value)} disabled={running}/></label></div>
    <p className="cc-help">Each import creates a separate saved version. Existing versions stay intact. No repository code is executed. Public archive imports do not fetch commit history.</p>
    {enabled===false && <p className="cc-callout">Direct import is disabled by the operator. Expand local setup below to import using the CLI.</p>}
    {error && <p role="alert" className="cc-error">{error}</p>}
    {job && <div className="cc-job" role="status">{running?<Loader2 size={18} className="cc-spin"/>:job.status==="COMPLETE"?<Check size={18}/>:null}<div><strong>{job.stage}</strong><p>{job.error || (running?"This can take a few minutes. You can close this panel and return to check progress.":job.result?.source_revision?.slice(0,12))}</p></div></div>}
    {job?.status==="COMPLETE"?<button className="cc-primary" onClick={()=>{localStorage.removeItem("chronosgraph-import-job");complete(job.tenant_graph);}}>Open imported repository →</button>:<button className="cc-primary" disabled={!enabled||!url.trim()||running||sending} onClick={()=>void start()}><GitBranch size={16}/>{sending?"Starting…":running?"Importing repository…":"Import repository"}</button>}
    <details className="cc-cli"><summary>Advanced: local CLI setup</summary><GitHubImportGuide reload={()=>complete("")} loading={false}/></details>
  </dialog>;
}
