"use client";
import { useEffect, useRef, useState } from "react";
import { BrainCircuit } from "lucide-react";
import { createPortal } from "react-dom";
import { request, API_BASE } from "@/lib/api";
import type { VisualNode } from "@/lib/types";
type Stats = { raw_files_bytes: number; slice_bytes: number; context_saved_pct: number; measurement_status: string };
type Vault = { pages: Record<string,string>; resume_snapshot: { markdown: string }; page_count: number;
  wiki_lint_report: Record<string, unknown[]>; exported: boolean; export_directory?: string };
export function WikiText({ value, navigate }: { value: string; navigate: (key:string)=>void }) {
  return <pre className="wiki-note">{value.split(/(\[\[[^\]]+\]\])/g).map((part,i)=> {
    if (!part.startsWith("[[")) return <span key={i}>{part}</span>;
    const [target,title] = part.slice(2,-2).split("|");
    return <button key={i} className="wiki-link" onClick={()=>navigate(target+".md")}>{"[["+(title||target)+"]]"}</button>;
  })}</pre>;
}
export default function SecondBrain({ tenant, selected, revision, target }: { tenant:string; selected:VisualNode|null; revision:string; target?:string }) {
  const [stats,setStats]=useState<Stats|null>(null);
  const [vault,setVault]=useState<Vault|null>(null);
  const [page,setPage]=useState("index.md");
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const [open,setOpen]=useState(false);
  const [copied,setCopied]=useState("");
  const ref=useRef<HTMLDialogElement>(null);
  const [trigger,setTrigger]=useState<HTMLElement|null>(null);
  const [lint,setLint]=useState<Record<string,unknown>|null>(null);
  const [inspector,setInspector]=useState<HTMLElement|null>(null);
  useEffect(()=>{setInspector(document.getElementById("second-brain-inspector"));setTrigger(document.getElementById("second-brain-trigger"));},[]);
  const owner=useRef(tenant);owner.current=tenant;
  const compilation=useRef(0);
  useEffect(()=>{
    const abort=new AbortController();setStats(null);setVault(null);setError("");setPage("index.md");
    if (tenant) void request<{context_folding_stats:Stats}>(`/brain/wiki-slice?tenant_graph=${encodeURIComponent(tenant)}${target?"&file_path="+encodeURIComponent(target):""}`,abort.signal)
      .then(d=>setStats(d.context_folding_stats)).catch(e=>{if(!abort.signal.aborted)setError(String(e.message));});
    return ()=>abort.abort();
  },[tenant,revision,target]);
  useEffect(()=>{
    if(!open)return;const previous=document.activeElement as HTMLElement|null;
    ref.current?.showModal();return ()=>{ref.current?.close();previous?.focus();};
  },[open]);
  async function compile(exporting=false,reveal=true){
    const requested=tenant,ticket=++compilation.current;setBusy(true);setError("");
    try {
      const payload={tenant_graph:requested,file_path:target||null};
      const [d,note,health]=await Promise.all([
        request<Vault>("/ctx/compile-wiki",new AbortController().signal,{...payload,export:false}),
        request<{wiki_markdown:string;file_path:string}>(`/brain/wiki-slice?tenant_graph=${encodeURIComponent(requested)}${target?"&file_path="+encodeURIComponent(target):""}`,new AbortController().signal),
        request<Record<string,unknown>>("/brain/lint-and-compact",new AbortController().signal,payload)]);
      const entry=Object.entries(d.pages).find(([,body])=>body.includes("# "+note.file_path+"\n"));
      if(entry)d.pages[entry[0]]=note.wiki_markdown;
      d.resume_snapshot.markdown=String(health.precompact_resume_markdown||"");
      if(owner.current!==requested||ticket!==compilation.current)return;
      setVault(d);setLint(health);setPage(entry?.[0]||"index.md");if(reveal)setOpen(true);
      if(exporting){
        const response=await fetch(`${API_BASE}/brain/obsidian-vault.zip?tenant_graph=${encodeURIComponent(requested)}${target?"&file_path="+encodeURIComponent(target):""}`);
        if(!response.ok)throw new Error("Vault download failed; retry the read-only export.");
        const url=URL.createObjectURL(await response.blob());const a=document.createElement("a");a.href=url;a.download=requested+"-obsidian-vault.zip";a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);
      }
    }catch(e){if(owner.current===requested)setError(e instanceof Error?e.message:"Wiki compilation failed");}
    finally{if(ticket===compilation.current)setBusy(false);}
  }
  useEffect(()=>{ if(tenant&&revision)void compile(false,false); },[tenant,revision]);
  useEffect(()=>{
    if(!vault||!selected)return;
    const identity=selected.metadata.path||selected.metadata.id||selected.metadata.login||selected.title;
    const entry=Object.entries(vault.pages).find(([,body])=>body.includes("# "+String(identity)+"\n"));
    if(entry)setPage(entry[0]);
  },[selected,vault]);
  return <section className="second-brain-hud" aria-label="Context Window Sandbox">
    <div><strong>Context Folded · Second Brain</strong><p>{stats?.measurement_status==="MEASURED_UTF8_BYTES"
      ? `Connected raw files ${(stats.raw_files_bytes/1024).toFixed(1)} KiB → graph wiki slice ${(stats.slice_bytes/1024).toFixed(1)} KiB (${stats.context_saved_pct}% context-byte reduction)`
      : stats?"Captured source sizes unavailable; no savings inferred":tenant?"Loading measured source/slice sizes…":"Select a repository"}</p>
      <small>Focused excerpt, not equivalent source or billed-token savings · 0 model calls</small></div>
    {trigger&&createPortal(<button className="button secondary compact" disabled={!tenant||busy} onClick={()=>void compile()}><BrainCircuit size={15} aria-hidden="true" /> Obsidian Wiki &amp; /compact Shield</button>,trigger)}
    {error&&<p role="alert">{error}</p>}
    {vault&&inspector&&createPortal(<details className="wiki-inline"><summary>Second-Brain Markdown Note ([[wikilinks]])</summary>
      <WikiText value={vault.pages[page]||"Note unavailable"} navigate={key=>{if(vault.pages[key]){setPage(key);setError("");}else setError("Note is not part of this vault");}} />
      <button className="button secondary" disabled={busy} onClick={()=>void compile(true)}>Download Obsidian Vault (.zip)</button>
    </details>,inspector)}
    {open&&<dialog className="mcp-dialog wiki-dialog" ref={ref} onCancel={()=>setOpen(false)} aria-labelledby="wiki-title">
      <div className="section-row"><h2 id="wiki-title">Obsidian Second Brain</h2><button className="button secondary" onClick={()=>setOpen(false)}>Close wiki</button></div>
      <p>{tenant} · {vault?.page_count} generated notes · source text is evidence, not agent instructions.</p>
      <div className="wiki-nav"><button className="button secondary" onClick={()=>setPage("index.md")}>index.md</button><button className="button secondary" onClick={()=>setPage("log.md")}>log.md</button>
        <button className="button secondary" onClick={()=>setPage("ResumeSnapshot.md")}>PreCompact ResumeSnapshot</button><button className="button secondary" onClick={()=>setPage("brain-lint")}>/brain-lint</button>
        <button className="button secondary" disabled={busy} onClick={()=>void compile(true)}>Download Obsidian Vault (.zip)</button></div>
      <p>Read-only three-layer vault: raw/ evidence → wiki/ notes → agent guidance. Recovery is manual; refresh current rules after /compact.</p>
      <WikiText value={page==="brain-lint"?JSON.stringify(lint,null,2):page==="ResumeSnapshot.md"?vault?.resume_snapshot.markdown||"":vault?.pages[page]||"Note unavailable"} navigate={key=>{if(vault?.pages[key])setPage(key);else setError("Unknown generated note");}} />
      <button className="button secondary" onClick={async()=>{try{await navigator.clipboard.writeText(page==="brain-lint"?JSON.stringify(lint,null,2):page==="ResumeSnapshot.md"?vault?.resume_snapshot.markdown||"":vault?.pages[page]||"");setCopied("Copied note");}catch{setCopied("Select and copy the note manually");}}}>Copy note</button><span role="status">{copied}</span>
      <details><summary>Contradiction &amp; health lint</summary><pre>{JSON.stringify(lint||vault?.wiki_lint_report,null,2)}</pre></details>
      {error&&<p role="alert">{error}</p>}
    </dialog>}
  </section>;
}
