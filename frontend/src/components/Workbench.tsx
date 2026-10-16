"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Activity, ArrowLeft, GitBranch, Search, ShieldCheck, Terminal } from "lucide-react";
import { request } from "@/lib/api";
import GitHubImportGuide from "./GitHubImportGuide";
import { finalStateInput, formatBytes, queryString } from "@/lib/workbench";
import type { Brain, Subgraph, Tenant } from "@/lib/types";
const GraphCanvas = dynamic(() => import("./GraphCanvas"), { ssr: false });
type Entry = { path: string; sha256: string; revision: string; pagerank: number; why_included: string;
  symbols: { name: string; signature: string; start_line: number; end_line: number }[] };
type Context = { entry_points: Entry[]; payload_bytes: number; payload_token_equivalents: number;
  related_importers: { path: string }[]; active_rules: { id: string; rule: string }[]; coverage: { truncated: boolean } };
type Ownership = { status: string; source_document: { path: string | null; sha256: string | null; revision: string | null };
  declarations: { file_path: string; owner: string | null; owner_kind: string | null; pattern: string; source_line: number }[];
  truncated: boolean; invalid_rule_count: number };
type Snapshot = { source_revision: string | null; selected_branch: string | null; connection_kind: string;
  parent_snapshot: string | null; last_check: { status: string; checked_at: number | null; observed_revision: string | null; dirty: boolean | null; reasons: string[] } };
type Event = { id: string; timestamp: number; tool_name: string; summary: string; duration_ms: number; outcome: string; result_bytes: number };
type Finding = { id: string; summary: string; evidence_note: string; status: string; stale_reasons: string[] };
type Memory = { findings: Finding[]; stale_findings_in_scan: number; has_more: boolean };
type Impact = { changed_files: string[]; impacted_files: string[]; impacted_test_files: string[]; potentially_broken_callers: string[];
  added_dependencies: { relationship: string; source: string; target: string }[];
  removed_dependencies: { relationship: string; source: string; target: string }[];
  recommended_pytest_command: string; sandbox_cleaned_up: boolean; unresolved_calls: number;
  parse_coverage: { before_failed_files: string[]; after_failed_files: string[]; basis: string } };
const views = ["Repo map & search", "Diff & impact", "Rules & contributors", "Activity & memory"];
function JsonDetails({ value, label }: { value: unknown; label: string }) {
  return <details className="wb-details"><summary>{label}</summary><pre>{JSON.stringify(value, null, 2)}</pre></details>;
}
export default function Workbench() {
  const [catalog, setCatalog] = useState<Tenant[]>([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const catalogReload = useRef<AbortController | null>(null);
  const [tenant, setTenant] = useState("");
  const tenantRef = useRef("");
  const [view, setView] = useState(0);
  const [graph, setGraph] = useState<Subgraph | null>(null);
  const [graphOwner, setGraphOwner] = useState("");
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [snapshotError, setSnapshotError] = useState("");
  const [query, setQuery] = useState("");
  const [context, setContext] = useState<Context | null>(null);
  const [source, setSource] = useState<Record<string, unknown> | null>(null);
  const [path, setPath] = useState("");
  const [diffMode, setDiffMode] = useState("diff");
  const [patch, setPatch] = useState("");
  const [impact, setImpact] = useState<Impact | null>(null);
  const [brain, setBrain] = useState<Brain | null>(null);
  const [ownership, setOwnership] = useState<Ownership | null>(null);
  const [events, setEvents] = useState<Event[]>([]);
  const [memory, setMemory] = useState<Memory | null>(null);
  const [summary, setSummary] = useState("");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const [pollError, setPollError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const operation = useRef<AbortController | null>(null);
  const current = catalog.find(t => t.tenant_graph === tenant);
  useEffect(() => {
    const ctrl = new AbortController();
    request<Tenant[]>("/tenants", ctrl.signal).then(rows => {
      setCatalog(rows); tenantRef.current = rows[0]?.tenant_graph || ""; setTenant(tenantRef.current);
    }).catch(e => { if (!ctrl.signal.aborted) setError(e.message); });
    return () => { ctrl.abort(); operation.current?.abort(); catalogReload.current?.abort(); };
  }, []);
  useEffect(() => {
    if (!tenant) return;
    const ctrl = new AbortController();
    setPath(current?.preset_files[0] || "");
    setSnapshot(null); setSnapshotError("");
    request<Snapshot>(`/workspace/snapshot?${queryString({ tenant_graph: tenant })}`, ctrl.signal).then(data => {
      if (tenantRef.current === tenant && !ctrl.signal.aborted) setSnapshot(data);
    }).catch(e => { if (!ctrl.signal.aborted) setSnapshotError(e.message); });
    request<Subgraph>(`/subgraph?${queryString({ tenant_graph: tenant })}`, ctrl.signal).then(data => {
      if (tenantRef.current !== tenant) return;
      setGraph(data); setGraphOwner(tenant);
    }).catch(e => { if (!ctrl.signal.aborted) setError(e.message); });
    return () => ctrl.abort();
    // The catalog is loaded before selecting a tenant.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenant]);
  useEffect(() => {
    if (!tenant || view !== 3) return;
    const ctrl = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const [a, m] = await Promise.all([
          request<{ events: Event[] }>(`/activity?${queryString({ tenant_graph: tenant })}`, ctrl.signal),
          request<Memory>(`/memory/findings?${queryString({ tenant_graph: tenant, include_stale: true })}`, ctrl.signal),
        ]);
        if (!ctrl.signal.aborted) { setEvents(a.events); setMemory(m); setPollError(""); }
      } catch (e) { if (!ctrl.signal.aborted) setPollError(e instanceof Error ? e.message : "Activity unavailable"); }
      if (!ctrl.signal.aborted) timer = setTimeout(poll, 2000);
    }
    void poll();
    return () => { ctrl.abort(); clearTimeout(timer); };
  }, [tenant, view]);
  async function reloadCatalog() {
    catalogReload.current?.abort();
    const ctrl = new AbortController(); catalogReload.current = ctrl; setCatalogLoading(true);
    try {
      const rows = await request<Tenant[]>("/tenants", ctrl.signal);
      if (!ctrl.signal.aborted) {
        setCatalog(rows);
        if (!rows.some(row => row.tenant_graph === tenantRef.current)) chooseTenant(rows[0]?.tenant_graph || "");
      }
    } catch (e) { if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : "Repository reload failed"); }
    finally { if (!ctrl.signal.aborted) setCatalogLoading(false); }
  }
  function chooseTenant(value: string) {
    operation.current?.abort(); tenantRef.current = value; setTenant(value); setBusy(false);
    setSnapshot(null); setSnapshotError("");
    setContext(null); setSource(null); setImpact(null); setBrain(null); setOwnership(null); setEvents([]); setMemory(null);
    setError(""); setNotice(""); setSummary(""); setNote(""); setPatch("");
    // Preserve and label previous graph until the new overview resolves.
  }
  async function run<T>(endpoint: string, accept: (data: T) => void, body?: unknown) {
    operation.current?.abort();
    const ctrl = new AbortController(); operation.current = ctrl;
    const owner = tenant; setBusy(true); setError(""); setNotice("");
    try {
      const data = await request<T>(endpoint, ctrl.signal, body);
      if (!ctrl.signal.aborted && owner === tenantRef.current) accept(data);
    } catch (e) { if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : "Request failed"); }
    finally { if (operation.current === ctrl) setBusy(false); }
  }
  function lookup() {
    void run<Context>(`/context/locate?${queryString({ tenant_graph: tenant, query })}`, data => {
      setContext(data); if (data.entry_points[0]) setPath(data.entry_points[0].path); setSource(null);
    });
  }
  function previewDiff() {
    try {
      const body = diffMode === "diff" ? { tenant_graph: tenant, unified_diff: patch }
        : { tenant_graph: tenant, file_bodies: finalStateInput(patch) };
      void run<Impact>("/diff/impact", setImpact, body);
    } catch (e) { setError(e instanceof Error ? e.message : "Invalid input"); }
  }
  async function copy(text: string) {
    try { await navigator.clipboard.writeText(text); setNotice("Copied pytest command"); }
    catch { setError("Clipboard unavailable. Select and copy the command manually."); }
  }
  return <main className="wb-shell">
    <header className="wb-header">
      <div><span className="eyebrow">CHRONOSGRAPH · T-09 WORKBENCH PREVIEW</span><h1>Find the context. Keep the evidence.</h1></div>
      <Link href="/" className="button secondary"><ArrowLeft size={16} />Three-track demo & wiki</Link>
    </header>
    <GitHubImportGuide reload={() => void reloadCatalog()} loading={catalogLoading} />
    <div className="wb-toolbar">
      <label>Indexed repository<select aria-label="Workbench repository" value={tenant} onChange={e => chooseTenant(e.target.value)} disabled={!catalog.length}>
        {catalog.map(t => <option key={t.tenant_graph} value={t.tenant_graph}>{t.repository}</option>)}
      </select></label>
      <div role="region" aria-label="Snapshot connection evidence">
        <p><strong>{snapshot?.selected_branch ? `Branch: ${snapshot.selected_branch}` : "Pinned source snapshot"}</strong><br />
          {snapshot?.source_revision && <><code>{snapshot.source_revision.slice(0, 12)}</code> · </>}
          {snapshot ? snapshot.last_check.status.replaceAll("_", " ") : snapshotError ? "Metadata unavailable" : "Loading snapshot metadata…"}
          {snapshot?.last_check.checked_at && <><br />Checked {new Date(snapshot.last_check.checked_at * 1000).toLocaleString()}</>}</p>
        {snapshotError && <p role="alert">Snapshot metadata unavailable: {snapshotError}</p>}
        <p>Last explicit check only—not live workspace monitoring. Connect and refresh use the local CLI; refresh creates a new snapshot.</p>
        {snapshot && <JsonDetails label="Branch & freshness evidence" value={snapshot} />}
      </div>
    </div>
    <nav className="wb-nav" aria-label="Workbench views">{views.map((name, i) => <button key={name}
      className={view === i ? "selected" : ""} aria-current={view === i ? "page" : undefined}
      onClick={() => { operation.current?.abort(); setBusy(false); setView(i); setError(""); setNotice(""); }}>{name}</button>)}</nav>
    {error && <p role="alert" className="wb-error">{error}</p>}
    {notice && <p role="status" className="wb-notice">{notice}</p>}
    <div className="wb-grid">
      <section className="wb-panel">
        {view === 0 && <>
          <h2><Search size={20} />Repo map & search</h2>
          <p>Start with paths or symbol names. Follow exact source coordinates before editing.</p>
          <form onSubmit={e => { e.preventDefault(); lookup(); }}><label>Search repository<input value={query} onChange={e => setQuery(e.target.value)} maxLength={200} placeholder="graph query, helper, session…" /></label>
            <button className="button primary" disabled={busy || !tenant || !query.trim()}>Locate context</button></form>
          {context && <>
            <p className="wb-meter">{formatBytes(context.payload_bytes)} context package · {context.payload_token_equivalents} char÷4 equivalents{context.coverage.truncated ? " · bounded selection" : ""}</p>
            {!context.entry_points.length && <p>No path or symbol match. Try a shorter term.</p>}
            {context.entry_points.map(entry => <article className="wb-card" key={entry.path}>
              <h3>{entry.path}</h3><p>{entry.why_included}</p><small>File PageRank {entry.pagerank.toFixed(5)} · {entry.sha256.slice(0, 12)}</small>
              {entry.symbols.map(s => <button className="wb-symbol" aria-label={`Read ${s.name}`} key={s.name} disabled={busy} onClick={() => void run<Record<string, unknown>>(
                `/context/symbol-source?${queryString({ tenant_graph: tenant, file_path: entry.path, symbol_name: s.name })}`, setSource)}>
                <code>{s.signature || s.name}</code><span>Lines {s.start_line ?? "?"}–{s.end_line ?? "?"}</span></button>)}
            </article>)}
            <JsonDetails label="Connected importers & active rules" value={{ related: context.related_importers, rules: context.active_rules }} />
          </>}
        </>}
        {view === 1 && <>
          <h2><GitBranch size={20} />Diff & impact sandbox</h2><p>Preview final Python source states in GRAPH.COPY. Nothing is applied to disk or the source graph.</p>
          <label>Input format<select aria-label="Input format" disabled={busy} value={diffMode} onChange={e => { setDiffMode(e.target.value); setPatch(""); setImpact(null); }}>
            <option value="diff">Unified git diff (multi-file)</option><option value="bodies">Final file bodies (JSON map)</option></select></label>
          <label>{diffMode === "diff" ? "Paste complete Python diff" : "Path → final source text; null deletes"}<textarea aria-label={diffMode === "diff" ? "Paste complete Python diff" : "Path → final source text; null deletes"} disabled={busy} className="wb-patch" value={patch} onChange={e => { setPatch(e.target.value); setImpact(null); }} maxLength={128000}
            placeholder={diffMode === "diff" ? "diff --git a/module.py b/module.py…" : '{"module.py":"def helper():\\n    return 1\\n"}'} /></label>
          <button className="button primary" onClick={previewDiff} disabled={busy || !tenant || !patch.trim()}>Preview replacement impact</button>
          {impact && <>
            <div className="wb-meter">{impact.impacted_files.length} candidate files · {impact.impacted_test_files.length} test files · Cleanup {impact.sandbox_cleaned_up ? "VERIFIED" : "NOT VERIFIED"}</div>
            <p>Before + after static reachability. Candidate tests are a review aid, not safe-skip proof. {impact.unresolved_calls} unresolved call expressions.</p>
            {!!impact.parse_coverage?.after_failed_files.length && <p className="wb-error">Incomplete AST coverage: {impact.parse_coverage.after_failed_files.length} existing files could not be parsed. Missing edges do not mean no impact.</p>}
            <JsonDetails label="AST parse coverage" value={impact.parse_coverage} />
            {impact.recommended_pytest_command && <><pre>{impact.recommended_pytest_command}</pre><button className="button secondary" onClick={() => void copy(impact.recommended_pytest_command)}>Copy pytest command</button></>}
            <JsonDetails label={`Removed dependencies (${impact.removed_dependencies.length})`} value={impact.removed_dependencies} />
            <JsonDetails label={`Added dependencies (${impact.added_dependencies.length})`} value={impact.added_dependencies} />
            <JsonDetails label="Potentially broken callers & impacted files" value={{ callers: impact.potentially_broken_callers, files: impact.impacted_files }} />
          </>}
        </>}
        {view === 2 && <>
          <h2><ShieldCheck size={20} />Rules & contributors</h2><p>Keep current local policy separate from historical rules and bounded Git author evidence.</p>
          <label>Target file<input disabled={busy} value={path} onChange={e => { setPath(e.target.value); setBrain(null); setOwnership(null); }} maxLength={1024} /></label>
          <button className="button primary" disabled={busy || !path || !tenant} onClick={() => void run<Brain>("/track3/ask-brain", setBrain,
            { tenant_graph: tenant, file_path: path, question: "Show current and superseded governing rules and commit contributors" })}>Inspect rules & contributors</button>
          {brain && <>
            <h3>ACTIVE local rules</h3>{brain.active_decisions.map((r, i) => <article className="wb-card" key={i}>{String(r.rule ?? r.active_rule ?? "")}</article>)}
            <JsonDetails label="Superseded history (not current instructions)" value={brain.superseded_decisions} />
            <JsonDetails label="Source-extracted constraints" value={brain.repository_constraints} />
            <h3>Git contributors — separate from declared CODEOWNERS</h3><JsonDetails label="Source-linked contributors" value={brain.top_experts} />

          </>}
        </>}
        {view === 2 && <>
          <h3>Declared CODEOWNERS</h3>
          <button className="button secondary" disabled={busy || !path || !tenant} onClick={() => void run<Ownership>(
            `/context/owners?${queryString({ tenant_graph: tenant, file_path: path })}`, setOwnership)}>Trace declared owners</button>
          {ownership && <section className="wb-card" aria-label="Declared owner evidence">
            <p>{ownership.status}</p>
            <p>File → matching rule → declared owner. Pinned commit evidence, not verified GitHub identity or access.</p>
            {ownership.declarations.map((d, i) => <p key={i}><strong>{d.owner || "No declared owner (matching rule clears owners)"}</strong><br />
              <code>{d.pattern}</code> · {ownership.source_document.path}:{d.source_line}</p>)}
            {!ownership.declarations.length && <p>No matching declaration returned. Older snapshots may need ownership indexing in a new tenant.</p>}
            {ownership.truncated && <p>Bounded owner selection; additional declarations omitted.</p>}
            {!!ownership.invalid_rule_count && <p>{ownership.invalid_rule_count} unsupported or invalid rules skipped.</p>}
            <JsonDetails label="Pinned CODEOWNERS source" value={ownership.source_document} />
          </section>}
        </>}
        {view === 3 && <>
          <h2><Activity size={20} />Agent activity & memory</h2><p>Actual ChronosGraph MCP invocations only, refreshed every 2 seconds. Browser REST reads are not agent events.</p>
          {pollError && <p role="alert" className="wb-error">{pollError}</p>}
          {!events.length && <p>No recorded MCP calls for this repository. Connect the T-09 stdio server to an agent to populate this timeline.</p>}
          {events.map(event => <article className="wb-card" key={event.id}><strong>{event.tool_name}</strong><p>{event.outcome} · {event.duration_ms.toFixed(2)} ms · {formatBytes(event.result_bytes)}</p><small>{new Date(event.timestamp).toLocaleString()}</small></article>)}
          <h3>Source-bound findings</h3><p>Agent-reported evidence is saved, not independently executed. Stale file hashes or governing policies flag it for review.</p>
          {memory?.findings.map(f => <article className="wb-card" key={f.id}><strong>{f.summary}</strong><p>{f.status}{f.stale_reasons.length ? ` · ${f.stale_reasons.join(", ")}` : ""}</p><p>{f.evidence_note}</p></article>)}
          {memory?.has_more && <p>Showing the latest bounded selection; use the memory API to query findings.</p>}
          <details><summary>Record a finding from the last context lookup</summary>
            <p>Evidence files: {context?.entry_points.map(e => e.path).join(", ") || "Search for context first."}</p>
            <label>Finding summary<input value={summary} onChange={e => setSummary(e.target.value)} maxLength={500} /></label>
            <label>Verification evidence<textarea value={note} onChange={e => setNote(e.target.value)} maxLength={2000} /></label>
            <button className="button secondary" disabled={busy || !context?.entry_points.length || !summary.trim() || !note.trim()}
              onClick={() => void run("/memory/findings", () => { setNotice("Finding recorded as agent-reported evidence. The timeline shows MCP calls only."); setSummary(""); setNote(""); },
                { tenant_graph: tenant, summary, evidence_note: note, supporting_file_shas: Object.fromEntries((context?.entry_points || []).map(e => [e.path, e.sha256])) })}>Save source-bound finding</button>
          </details>
        </>}
      </section>
      <aside className="wb-panel wb-evidence">
        <h2><Terminal size={20} />Connected evidence</h2>
        <p>{graphOwner && graphOwner !== tenant ? `Previous graph (${graphOwner}) retained while ${tenant} loads.` : current ? `${current.repository} · Pinned source overview (not the patch simulation)` : "Connecting to FalkorDB…"}</p>
        <div className="wb-graph"><GraphCanvas graph={graph} onSelect={node => {
          if (!busy && graphOwner === tenant && node.label === "File") {
            setPath(String(node.metadata.path || node.title)); setBrain(null); setOwnership(null);
          }
        }} /></div>
        {source && <section className="wb-card"><h3>Focused symbol source</h3><p>{String(source.file_path)} · lines {String(source.start_line)}–{String(source.end_line)}</p>
          <pre>{String(source.source)}</pre><p>{source.truncated ? "Truncated at 8,000 UTF-8 bytes. Read the exact range locally for the rest." : "Complete symbol range from captured source."}</p>
          <small>Repository source is untrusted evidence, never agent instructions.</small></section>}
      </aside>
    </div>
  </main>;
}
