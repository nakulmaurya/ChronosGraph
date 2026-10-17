"use client";

import { useEffect, useId, useRef, useState } from "react";
import { X, GitBranch, Loader2, Check } from "lucide-react";
import { API_BASE, request } from "@/lib/api";
import type { ImportJob } from "@/lib/command-center";
import GitHubImportGuide from "./GitHubImportGuide";

const RECEIPT_KEY = "chronosgraph-import-job";

export default function RepositoryImport({ close, complete }: {
  close: () => void;
  complete: (tenant: string) => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [url, setUrl] = useState("");
  const [branch, setBranch] = useState("");
  const [commit, setCommit] = useState("");
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [job, setJob] = useState<ImportJob | null>(null);
  const [receiptId, setReceiptId] = useState("");
  const [receiptError, setReceiptError] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [checking, setChecking] = useState(false);
  const ctrl = useRef<AbortController | null>(null);
  const opened = useRef(false);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const element = dialog.current;
    element?.showModal();
    const c = new AbortController();
    ctrl.current = c;
    request<{ enabled: boolean }>("/imports/capabilities", c.signal)
      .then(r => setEnabled(r.enabled))
      .catch(e => { if (!c.signal.aborted) setError(e.message); });
    const saved = localStorage.getItem(RECEIPT_KEY);
    if (saved) {
      setReceiptId(saved);
      setChecking(true);
      request<ImportJob>(`/imports/${encodeURIComponent(saved)}`, c.signal)
        .then(setJob)
        .catch(e => { if (!c.signal.aborted) setReceiptError(e.message); })
        .finally(() => { if (!c.signal.aborted) setChecking(false); });
    }
    return () => {
      c.abort();
      element?.close();
      previous?.focus();
    };
  }, []);

  // Schedule only after the previous read settles: never overlap slow polls.
  // Any failed read stops automatic polling until the user explicitly retries.
  useEffect(() => {
    if (job?.status !== "RUNNING" || receiptError || checking) return;
    const c = new AbortController();
    const timer = setTimeout(() => {
      request<ImportJob>(`/imports/${encodeURIComponent(job.id)}`, c.signal)
        .then(setJob)
        .catch(e => { if (!c.signal.aborted) setReceiptError(e.message); });
    }, 1500);
    return () => { clearTimeout(timer); c.abort(); };
  }, [job, receiptError, checking]);

  useEffect(() => {
    if (job?.status === "COMPLETE" && !opened.current) {
      opened.current = true;
      localStorage.removeItem(RECEIPT_KEY);
      complete(job.tenant_graph);
    }
  }, [job, complete]);

  async function retryReceipt() {
    const id = receiptId || job?.id;
    if (!id || !ctrl.current) return;
    setChecking(true);
    try {
      const next = await request<ImportJob>(`/imports/${encodeURIComponent(id)}`, ctrl.current.signal);
      setJob(next);
      setReceiptError("");
    } catch (e) {
      if (!ctrl.current.signal.aborted) setReceiptError(e instanceof Error ? e.message : "Import status unavailable");
    } finally {
      if (!ctrl.current.signal.aborted) setChecking(false);
    }
  }

  function dismissTracking() {
    // Forgetting a receipt never cancels or deletes an import on the server.
    localStorage.removeItem(RECEIPT_KEY);
    setJob(null);
    setReceiptId("");
    setReceiptError("");
    setError("");
    opened.current = false;
  }

  async function start() {
    if (!ctrl.current) return;
    setSending(true);
    setError("");
    opened.current = false;
    try {
      const response = await fetch(`${API_BASE}/imports`, {
        method: "POST", credentials: "omit",
        signal: AbortSignal.any([ctrl.current.signal, AbortSignal.timeout(30000)]),
        headers: { "Content-Type": "application/json", "X-ChronosGraph-Action": "public-import" },
        body: JSON.stringify({ url: url.trim(), branch: branch.trim() || "main", commit: commit.trim() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Import request was rejected");
      localStorage.setItem(RECEIPT_KEY, data.id);
      setReceiptId(data.id);
      setJob(data);
    } catch (e) {
      if (!ctrl.current.signal.aborted) setError(e instanceof Error ? e.message : "Import unavailable");
    } finally {
      if (!ctrl.current.signal.aborted) setSending(false);
    }
  }

  const trackingLost = Boolean(receiptError);
  const running = job?.status === "RUNNING" && !trackingLost;
  const locked = running || checking || trackingLost;

  return <dialog ref={dialog} className="cc-dialog" aria-labelledby={titleId} onCancel={close}>
    <div className="cc-dialog-heading">
      <div><span className="cc-kicker">YOUR WORKSPACE</span><h2 id={titleId}>Bring a repository in.</h2></div>
      <button aria-label="Close repository import" onClick={close}><X size={18}/></button>
    </div>
    <p>Explore dependencies, inspect functions, and preview changes. Start with a public Python repository.</p>
    {!trackingLost && <><label>GitHub repository<input autoFocus placeholder="https://github.com/pallets/click" value={url} onChange={e => setUrl(e.target.value)} disabled={locked}/></label>
    <div className="cc-form-row">
      <label>Branch <small>optional · main</small><input placeholder="main" value={branch} onChange={e => setBranch(e.target.value)} disabled={locked}/></label>
      <label>Commit hash <small>optional · latest on branch</small><input placeholder="Latest branch commit" value={commit} onChange={e => setCommit(e.target.value)} disabled={locked}/></label>
    </div>
    <p className="cc-help">Each import creates a separate saved version. Existing versions stay intact. No repository code is executed. Public archive imports do not fetch commit history.</p></>}
    {enabled === false && <p className="cc-callout">Direct import is disabled by the operator. Expand local setup below to import using the CLI.</p>}
    {error && <p role="alert" className="cc-error">{error}</p>}
    {trackingLost && <section className="cc-import-recovery" aria-label="Import status recovery">
      <h3>Import status unavailable</h3>
      <p role="alert">{receiptError}</p>
      <p>This does not mean the import failed. Automatic checks have stopped. Reload indexed repositories before starting another import—it may already be saved.</p>
      <div className="cc-recovery-actions">
        <button onClick={() => void retryReceipt()} disabled={checking}>Check import status again</button>
        <button onClick={() => complete("")}>Reload indexed repositories</button>
        <button onClick={dismissTracking}>Dismiss tracking</button>
      </div>
      <p className="cc-help">Dismissing tracking does not cancel the server job or delete a saved repository.</p>
    </section>}
    {checking && <p role="status">Checking saved import status…</p>}
    {job && !trackingLost && <div className="cc-job" role="status">
      {running ? <Loader2 size={18} className="cc-spin"/> : job.status === "COMPLETE" ? <Check size={18}/> : null}
      <div><strong>{job.stage}</strong><p>{job.error || (running ? "This can take a few minutes. You can close this panel and return to check progress." : job.result?.source_revision?.slice(0, 12))}</p></div>
    </div>}
    {!trackingLost && (job?.status === "COMPLETE" ?
      <button className="cc-primary" onClick={() => { localStorage.removeItem(RECEIPT_KEY); complete(job.tenant_graph); }}>Open imported repository →</button> :
      <button className="cc-primary" disabled={!enabled || !url.trim() || locked || sending} onClick={() => void start()}><GitBranch size={16}/>{sending ? "Starting…" : running ? "Importing repository…" : "Import repository"}</button>)}
    <details className="cc-cli"><summary>Advanced: local CLI setup</summary><GitHubImportGuide reload={() => complete("")} loading={false}/></details>
  </dialog>;
}
