"use client";
import { useState } from "react";
import { githubIntakeCommands } from "@/lib/github-import";
export default function GitHubImportGuide({ reload, loading }: { reload: () => void; loading: boolean }) {
  const [url, setUrl] = useState("https://github.com/pallets/click");
  const [branch, setBranch] = useState("");
  const [tenant, setTenant] = useState("");
  const [revision, setRevision] = useState("");
  const [notice, setNotice] = useState("");
  let commands: ReturnType<typeof githubIntakeCommands> | null = null;
  let error = "";
  try { commands = githubIntakeCommands(url, branch, tenant, revision); }
  catch (e) { error = e instanceof Error ? e.message : "Invalid import inputs"; }
  async function copy(value: string) {
    try { await navigator.clipboard.writeText(value); setNotice("Copied local CLI command. Nothing has been imported by the browser."); }
    catch { setNotice("Clipboard unavailable. Select and copy the command below."); }
  }
  return <details className="wb-import-guide">
    <summary>Connect a public GitHub repository · local CLI setup</summary>
    <p>Turn a public Python repository into a pinned FalkorDB context graph. Run these commands from your installed ChronosGraph checkout on the machine running FalkorDB. This panel only prepares commands; it does not launch imports.</p>
    <div className="wb-import-fields">
      <label>Public GitHub repository URL<input aria-label="Public GitHub repository URL" value={url} onChange={e => setUrl(e.target.value)} maxLength={240} /></label>
      <label>GitHub branch (optional)<input placeholder="main" aria-label="GitHub branch" value={branch} onChange={e => setBranch(e.target.value)} maxLength={200} /></label>
      <label>Saved copy name (optional)<input placeholder="Automatic unique name" aria-label="Saved copy name" value={tenant} onChange={e => setTenant(e.target.value)} maxLength={100} /></label>
      <label>Commit hash (optional)<input aria-label="Commit hash" value={revision} onChange={e => setRevision(e.target.value)} maxLength={40} placeholder="Empty = latest branch commit" /></label>
    </div>
    {error && <p role="alert" className="wb-error">{error}</p>}
    {commands && <>
      <p>Leave branch empty for <code>main</code>. Leave commit hash empty to use the latest branch commit when you run the import command. Each import creates a separate saved copy; an empty name generates a unique internal ID.</p>
      <p>For a specific version, open your repository on GitHub → Commits → select a commit → copy its full 40-character hash. You can also copy <code>source_revision</code> from the optional inspect command below.</p>
      <h3>1. Inspect the public branch (optional)</h3><pre>{commands.inspect}</pre>
      <button type="button" className="button secondary" onClick={() => void copy(commands!.inspect)}>Copy inspect command</button>
      <h3>2. Import a saved copy</h3>
      {commands.usesLatest && <p>Latest mode resolves the current branch commit first, then imports that exact version. If the branch moves during import, it stops safely; rerun the command.</p>}
      {commands.importCommand ? <pre>{commands.importCommand}</pre> : <p>Use a full 40-character commit hash, or leave it empty for latest. Custom saved-copy names must start with <code>repo_</code> and use lowercase letters, digits or underscores.</p>}
      <button type="button" className="button secondary" disabled={!commands.importCommand} onClick={() => commands?.importCommand && void copy(commands.importCommand)}>Copy import command</button>
    </>}
    <p>Public repositories only; no token, model calls, code execution, history fetching, submodules or symlinks. Size and archive checks may refuse unsupported repositories. Existing snapshots are never overwritten. Browser-run import jobs and private GitHub connections are not implemented.</p>
    <button type="button" className="button secondary" disabled={loading} onClick={reload}>{loading ? "Reloading repositories…" : "Reload indexed repositories"}</button>
    {notice && <p role="status">{notice}</p>}
  </details>;
}
