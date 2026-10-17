"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Activity, ArrowLeft, ArrowUpRight, Box, ChevronRight, Code2, FileCode2, Folder, GitBranch, GitCommitHorizontal, Layers, Network, Plus, Search, Shield, Terminal, X } from "lucide-react";
import { request, safeUrl } from "@/lib/api";
import { queryString } from "@/lib/workbench";
import { breadcrumbParent, boundedMapNotice, type RepositoryMap, type FileDetail, type HistoryData } from "@/lib/command-center";
import type { Tenant } from "@/lib/types";
import Workbench from "./Workbench";
import RepositoryImport from "./RepositoryImport";
import ChangePlanner from "./ChangePlanner";
const CommandGraph = dynamic(() => import("./CommandGraph"), { ssr: false });
const McpModal = dynamic(() => import("./McpModal"), { ssr: false });
type Snapshot = {
    tenant_graph: string;
    source_revision: string | null;
    selected_branch: string | null;
    last_check: {
        status: string;
        checked_at: number | null;
    };
    connection_kind: string;
};
type SearchData = {
    entry_points: {
        path: string;
        symbols: {
            name: string;
            signature: string;
        }[];
    }[];
};
type Source = {
    qualified_name: string;
    file_path: string;
    start_line: number;
    end_line: number;
    source: string;
    truncated: boolean;
};
const tabs = [{ name: "Repository", icon: Network }, { name: "Changes", icon: GitBranch }, { name: "History", icon: GitCommitHorizontal }, { name: "Ownership", icon: Shield }, { name: "Agent activity", icon: Activity }];
export default function CommandCenter() {
    const [catalog, setCatalog] = useState<Tenant[]>([]), [tenant, setTenant] = useState("");
    const [map, setMap] = useState<RepositoryMap | null>(null), [prefix, setPrefix] = useState("");
    const [detail, setDetail] = useState<FileDetail | null>(null), [snapshot, setSnapshot] = useState<Snapshot | null>(null);
    const [tab, setTab] = useState(0), [functions, setFunctions] = useState(false), [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchData | null>(null), [source, setSource] = useState<Source | null>(null);
    const [history, setHistory] = useState<HistoryData | null>(null), [commit, setCommit] = useState("");
    const [importOpen, setImportOpen] = useState(false), [agentOpen, setAgentOpen] = useState(false);
    const [error, setError] = useState(""), [loading, setLoading] = useState(false), [inspecting, setInspecting] = useState(false);
    const [mapError, setMapError] = useState("");
    const [mapAttempt, setMapAttempt] = useState(0);
    const operation = useRef<AbortController | null>(null);
    const current = catalog.find(t => t.tenant_graph === tenant);
    async function catalogLoad(pick = "", signal?: AbortSignal) {
        const rows = await request<Tenant[]>("/tenants", signal || new AbortController().signal);
        setCatalog(rows);
        setTenant(previous => pick || (rows.some(r => r.tenant_graph === previous) ? previous : rows.find(r => r.tenant_graph === localStorage.getItem("chronosgraph-repository"))?.tenant_graph || rows[0]?.tenant_graph || ""));
    }
    useEffect(() => { const c = new AbortController(); void catalogLoad("", c.signal).catch(e => { if (!c.signal.aborted)
        setError(e.message); }); return () => { c.abort(); operation.current?.abort(); }; }, []);
    useEffect(() => {
        if (!tenant)
            return;
        const c = new AbortController();
        operation.current?.abort();
        localStorage.setItem("chronosgraph-repository", tenant);
        setPrefix("");
        setDetail(null);
        setResults(null);
        setSource(null);
        setCommit("");
        setHistory(null);
        setSnapshot(null);
        setMap(null);
        setMapError("");
        setFunctions(false);
        setQuery("");
        setTab(0);
        setError("");
        setInspecting(false);
        request<Snapshot>(`/workspace/snapshot?${queryString({ tenant_graph: tenant })}`, c.signal).then(setSnapshot).catch(e => { if (!c.signal.aborted)
            setError(e.message); });
        return () => c.abort();
    }, [tenant]);
    useEffect(() => {
        if (!tenant)
            return;
        const c = new AbortController();
        setLoading(true);
        setMapError("");
        request<RepositoryMap>(`/repository/map?${queryString({ tenant_graph: tenant, prefix })}`, c.signal).then(setMap).catch(e => { if (!c.signal.aborted)
            setMapError(e.message); }).finally(() => { if (!c.signal.aborted)
            setLoading(false); });
        return () => c.abort();
    }, [tenant, prefix, mapAttempt]);
    useEffect(() => {
        if (!tenant || tab !== 2)
            return;
        const c = new AbortController();
        request<HistoryData>(`/repository/history?${queryString({ tenant_graph: tenant, commit })}`, c.signal).then(setHistory).catch(e => { if (!c.signal.aborted)
            setError(e.message); });
        return () => c.abort();
    }, [tenant, tab, commit]);
    async function inspect(path: string, symbol?: string) {
        operation.current?.abort();
        const c = new AbortController();
        operation.current = c;
        setInspecting(true);
        setError("");
        setSource(null);
        try {
            const data = await request<FileDetail>(`/repository/file?${queryString({ tenant_graph: tenant, file_path: path })}`, c.signal);
            if (c.signal.aborted)
                return;
            setDetail(data);
            setTab(0);
            if (symbol) {
                setFunctions(true);
                setSource(await request<Source>(`/context/symbol-source?${queryString({ tenant_graph: tenant, file_path: path, symbol_name: symbol })}`, c.signal));
            }
        }
        catch (e) {
            if (!c.signal.aborted)
                setError(e instanceof Error ? e.message : "File unavailable");
        }
        finally {
            if (operation.current === c)
                setInspecting(false);
        }
    }
    async function search() {
        operation.current?.abort();
        const c = new AbortController();
        operation.current = c;
        setError("");
        setInspecting(true);
        try {
            setResults(await request<SearchData>(`/context/locate?${queryString({ tenant_graph: tenant, query })}`, c.signal));
        }
        catch (e) {
            if (!c.signal.aborted)
                setError(e instanceof Error ? e.message : "Search failed");
        }
        finally {
            if (operation.current === c)
                setInspecting(false);
        }
    }
    function folder(path: string) { operation.current?.abort(); setInspecting(false); setPrefix(path); setMap(null); setDetail(null); setSource(null); setResults(null); setFunctions(false); setTab(0); }
    function pick(path: string, kind: string, symbol?: string) { if (kind === "folder")
        folder(path);
    else
        void inspect(path, symbol); }
    function switchTab(value: number) { operation.current?.abort(); setInspecting(false); setError(""); setTab(value); }
    function resetMap() { operation.current?.abort(); setInspecting(false); setDetail(null); setSource(null); setFunctions(false); }
    return <main className="cc-app">
    <aside className="cc-rail"><Link href="/workbench" aria-label="ChronosGraph home" className="cc-logo"><Network size={24}/></Link><div className="cc-rail-rule"/>{tabs.map((t, i) => <button key={t.name} title={t.name} aria-label={t.name} aria-current={tab === i ? "page" : undefined} className={tab === i ? "active" : ""} onClick={() => switchTab(i)}><t.icon size={19}/></button>)}<button title="Connect coding agent" aria-label="Connect coding agent" className="cc-rail-bottom" onClick={() => setAgentOpen(true)}><Terminal size={20}/></button></aside>
    <div className="cc-main"><header className="cc-topbar"><div className="cc-brand">ChronosGraph <span>/</span> <span>Workspace</span></div><div className="cc-top-actions"><span className="cc-local"><i />Local workspace</span><button aria-label="Connect agent" onClick={() => setAgentOpen(true)}><Terminal size={14}/>Connect agent</button><button aria-label="Import repository" className="cc-primary" onClick={() => setImportOpen(true)}><Plus size={15}/>Import repository</button></div></header>
      <div className="cc-projectbar"><div className="cc-project"><span className="cc-project-icon"><Box size={22}/></span><div><span className="cc-kicker">REPOSITORY COMMAND CENTER</span><select aria-label="Repository" value={tenant} disabled={!catalog.length} onChange={e => setTenant(e.target.value)}>{catalog.map(t => <option key={t.tenant_graph} value={t.tenant_graph}>{t.repository}</option>)}</select></div></div><div className="cc-revision"><span><GitBranch size={13}/>{snapshot?.selected_branch || "Pinned version"}</span><code>{snapshot?.source_revision?.slice(0, 8) || "Version unavailable"}</code><span className="cc-pill">{snapshot?.last_check.status === "MATCHED_AT_CHECK" ? "Matched at last check" : snapshot?.last_check.status === "PINNED_AT_IMPORT" ? "Saved at import" : "Saved snapshot"}</span></div></div>
      <nav className="cc-tabs" aria-label="Command center views">{tabs.map((t, i) => <button key={t.name} className={tab === i ? "active" : ""} aria-current={tab === i ? "page" : undefined} onClick={() => switchTab(i)}><t.icon size={15}/>{t.name}</button>)}<Link href="/demo" className="cc-demo-link">Demo & wiki <ArrowUpRight size={13}/></Link></nav>
      {error && <div className="cc-error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError("")}><X size={14}/></button></div>}
      {tab === 0 && <><section className="cc-overview"><div><h1>Your codebase. Connected.</h1><p>Find your way through the code, then see what a change could affect.</p></div><div className="cc-stats"><div><strong>{map ? (map.counts.File || 0).toLocaleString() : "—"}</strong><span>indexed files</span></div><div><strong>{map ? (map.counts.Function || 0).toLocaleString() : "—"}</strong><span>functions</span></div><div><strong>{map ? (map.counts.Class || 0).toLocaleString() : "—"}</strong><span>classes</span></div></div></section>
      <div className="cc-workspace"><aside className="cc-explorer"><div className="cc-panel-title"><span>EXPLORER</span><span>{map?.counts.File ?? "…"}</span></div><form className="cc-search" onSubmit={e => { e.preventDefault(); void search(); }}><Search size={14}/><input aria-label="Search files and symbols" placeholder="Search files or symbols…" value={query} onChange={e => { setQuery(e.target.value); if (!e.target.value)
            setResults(null); }} maxLength={200}/><button aria-label="Run repository search" disabled={!query.trim() || inspecting}>↵</button></form>
        <div className={`cc-tree-scroll ${results ? "cc-search-results" : ""}`}>{results ? <><div className="cc-tree-caption">Search results <button onClick={() => { setResults(null); setQuery(""); }}>Clear</button></div>{!results.entry_points.length && <p className="cc-empty">No match. Try a file path or a shorter symbol name.</p>}{results.entry_points.map(f => <div key={f.path}><button className="cc-tree-file" title={f.path} onClick={() => void inspect(f.path)}><FileCode2 size={14}/><span>{f.path}</span></button>{f.symbols.slice(0, 8).map(s => <button className="cc-tree-symbol" key={s.name} onClick={() => void inspect(f.path, s.name)}>ƒ {s.name}</button>)}</div>)}</> : <>{prefix && <button className="cc-tree-file" onClick={() => folder(breadcrumbParent(prefix))}><ArrowLeft size={14}/>Parent folder</button>}{map?.nodes.map(n => <button key={n.id} className={`cc-tree-file ${detail?.file.path === n.path ? "active" : ""}`} title={n.path} onClick={() => pick(n.path, n.kind)}>{n.kind === "folder" ? <Folder size={14}/> : <FileCode2 size={14}/>}<span>{n.path.slice(prefix.length).replace(/\/$/, "")}</span>{n.kind === "folder" && <small>{n.files}</small>}</button>)}{!map?.nodes.length && !loading && !mapError && <p className="cc-empty">No indexed files here.</p>}</>}</div>
        <div className="cc-explorer-footer"><Layers size={13}/>{loading ? "Loading repository…" : "Python AST · saved source"}</div></aside>
        <section className="cc-map-panel" aria-label="Interactive repository graph"><div className="cc-map-toolbar"><div className="cc-breadcrumb"><button onClick={() => folder("")}><Box size={13}/>Repository</button>{prefix && <><ChevronRight size={12}/><button onClick={resetMap}>{prefix}</button></>}{detail && <><ChevronRight size={12}/><span>{detail.file.path.split("/").pop()}</span></>}</div><div className="cc-segment"><button className={!functions ? "active" : ""} onClick={() => setFunctions(false)}>Dependencies</button><button className={functions ? "active" : ""} disabled={!detail} onClick={() => setFunctions(true)}>Functions</button></div></div>
          <div className="cc-canvas" aria-busy={loading || inspecting}>{map && <CommandGraph map={map} detail={detail} functions={functions} selected={source ? source.qualified_name : detail?.file.path || ""} onPick={pick}/>} {(loading || inspecting) && <span className="cc-loading" role="status">{inspecting ? "Inspecting source…" : "Loading map…"}</span>}{mapError && !loading && <div className="cc-map-recovery" role="alert"><Network size={30}/><h2>Repository map unavailable.</h2><p>{mapError}</p><button className="cc-primary" onClick={() => setMapAttempt(value => value + 1)}>Retry map</button><p className="cc-help">Your saved repository has not been changed.</p></div>}{!tenant && !loading && <div className="cc-blank"><Network size={34}/><h2>Start with your repository.</h2><p>Import a public Python project to explore its structure.</p><button className="cc-primary" onClick={() => setImportOpen(true)}>Import repository</button></div>}</div>
          <div className="cc-map-footer"><span><i className="cc-dot"/>{detail ? functions ? "File definitions & resolved internal calls" : "Incoming ← selected file → imported dependencies" : "Folders group actual file-import relationships"}</span><span>{detail ? "Pinned graph data" : `Overview query · ${map?.execution_time_ms.toFixed(1) ?? "—"} ms`}</span></div>
          {map && boundedMapNotice(map) && <p className="cc-limit">Bounded map: {map.coverage.groups_total} groups in this folder. Some nodes or edges are omitted. Open a folder or search to narrow the view.</p>}
          {detail && functions && detail.symbols.length > 60 && <p className="cc-limit">Showing the first 60 definitions on the canvas. The inspector lists up to 160.</p>}
        </section>
        <aside className="cc-inspector" aria-label="File inspector"><div className="cc-panel-title"><span>{detail ? "FILE INSPECTOR" : "GET YOUR BEARINGS"}</span>{detail && <button aria-label="Close file inspector" onClick={resetMap}><X size={14}/></button>}</div>
          {detail ? <><div className="cc-inspector-heading"><FileCode2 size={23}/><h2>{detail.file.path.split("/").pop()}</h2><p>{detail.file.path}</p><div className="cc-file-meta"><span>{detail.file.lines} lines</span><span>{detail.symbols.length} definitions</span></div>{safeUrl(detail.file.source_url) && <a href={safeUrl(detail.file.source_url)} target="_blank" rel="noreferrer">View pinned source <ArrowUpRight size={12}/></a>}</div>
          <section className="cc-inspector-section"><button className="cc-primary" onClick={() => switchTab(1)}>Plan a change to this file</button></section>
          {!!detail.file.parse_errors && <p className="cc-limit">This file has parse errors. Dependencies may be incomplete.</p>}
          <section className="cc-inspector-section"><h3>What depends on this <span>{detail.importers.length}</span></h3><p>These files import the selected file.</p>{detail.importers.slice(0, 12).map(f => <button className="cc-dependency" key={f.path} onClick={() => void inspect(f.path)} title={f.path}><FileCode2 size={12}/><span>{f.path}</span><ChevronRight size={12}/></button>)}{!detail.importers.length && <p className="cc-empty">No resolved importers in this snapshot.</p>}</section>
          <section className="cc-inspector-section"><h3>Imports <span>{detail.imports.length}</span></h3>{detail.imports.slice(0, 12).map(f => <button className="cc-dependency" key={f.path} onClick={() => void inspect(f.path)} title={f.path}><FileCode2 size={12}/><span>{f.path}</span><ChevronRight size={12}/></button>)}{!detail.imports.length && <p className="cc-empty">No resolved local imports.</p>}</section>
          <section className="cc-inspector-section">{(detail.imports.length > 12 || detail.importers.length > 12) && <p className="cc-limit">Dependency lists show the first 12 per direction; the graph shows up to 20. Coverage details below record API limits.</p>}<h3>Functions & classes <span>{detail.symbols.length}</span></h3>{detail.symbols.map(s => <button className="cc-definition" key={s.qualified_name} onClick={() => void inspect(detail.file.path, s.qualified_name)}><div><Code2 size={12}/><code>{s.name}</code><small>L{s.start_line}</small></div>{s.docstring && <p>{s.docstring.split("\n")[0]}</p>}</button>)}{!detail.symbols.length && <p className="cc-empty">No captured definitions.</p>}</section>
          {source && <section className="cc-inspector-section"><h3>Source · L{source.start_line}–{source.end_line}</h3><pre>{source.source}</pre>{source.truncated && <p className="cc-limit">Source preview truncated. Open the pinned source for the full range.</p>}</section>}
          <details className="cc-inspector-section"><summary>Index coverage & provenance</summary><p>Static relationships, not runtime dispatch. Missing edges do not prove no impact.</p><pre>{JSON.stringify(detail.coverage, null, 2)}</pre><small>File hash {detail.file.sha256?.slice(0, 16) || "not captured"}</small></details></> : <div className="cc-onboarding"><span className="cc-onboarding-icon"><Network size={28}/></span><h2>Follow the connections.</h2><p>Select a folder to zoom into the architecture. Select a file to see its dependencies, functions, and source.</p><ol><li><strong>Explore</strong><span>Start with folders or search a symbol.</span></li><li><strong>Understand</strong><span>Trace imports and inspect real definitions.</span></li><li><strong>Plan a change</strong><span>Preview downstream impact in Changes.</span></li></ol><button onClick={() => setAgentOpen(true)}><Terminal size={14}/>Connect your coding agent</button></div>}
        </aside></div>
        <footer className="cc-statusbar"><span>Saved version {snapshot?.source_revision?.slice(0, 8) || "—"} · not live workspace monitoring</span><span>{current?.repository || "No repository selected"}</span></footer></>}
      {tab === 2 && <section className="cc-history"><div className="cc-section-heading"><span className="cc-kicker">CHANGE EXPLORER</span><h1>Understand what changed.</h1><p>Commit-linked file changes from the indexed Git history.</p></div><div className="cc-history-grid"><div><h2>Indexed commits</h2>{!history?.commits.length && <div className="cc-empty-card"><GitCommitHorizontal size={24}/><h3>No commit history in this saved version.</h3><p>Public archive imports capture one commit’s source, not its history. Connect a trusted local Git checkout to index bounded commit history.</p></div>}{history?.commits.map(c => <button className={`cc-commit ${commit === c.sha ? "active" : ""}`} key={c.sha} onClick={() => setCommit(c.sha)}><strong>{c.title}</strong><span><code>{c.sha.slice(0, 8)}</code> · {c.author || "Git author"} · {c.timestamp ? new Date(c.timestamp * 1000).toLocaleDateString() : "Date unavailable"}</span></button>)}</div><div><h2>{commit ? "Files changed in this commit" : "Select a commit"}</h2><p className="cc-help">File inspection opens the current indexed source—not the historical commit’s source.</p>{history?.changes.map(f => <button className="cc-changed-file" key={f.path} onClick={() => void inspect(f.path)}><FileCode2 size={14}/><span>{f.path}</span><code>+{f.additions} −{f.deletions}</code><ArrowUpRight size={13}/></button>)}{commit && !history?.changes.length && <p>No indexed file links for this commit.</p>}{history?.changes_truncated && <p>Showing the first 300 file changes.</p>}</div></div></section>}
      {tab === 1 && tenant && <ChangePlanner key={`${tenant}:${detail?.file.path || ""}`} tenant={tenant} revision={snapshot?.tenant_graph === tenant ? snapshot.source_revision : null} path={detail?.file.path || ""} onInspect={path => void inspect(path)}/>}
      {(tab === 3 || tab === 4) && <section className="cc-tools"><div className="cc-section-heading"><span className="cc-kicker">{tab === 3 ? "KNOW WHO AND WHY" : "HUMAN + AGENT"}</span><h1>{tab === 3 ? "Rules, authors, and owners." : "Keep the work visible."}</h1><p>{tab === 3 ? "Understand the current rules and people connected to this code." : "Real tool calls and source-linked findings. No invented agent thoughts."}</p></div>{tenant && <Workbench key={tenant} fixedTenant={tenant} fixedPath={detail?.file.path || ""} onInspect={path => void inspect(path)} active evidenceEntries={detail?.file.sha256 ? [{ path: detail.file.path, sha256: detail.file.sha256 }] : []} defaultView={tab === 3 ? 2 : 3}/>}</section>}
    </div>{importOpen && <RepositoryImport close={() => setImportOpen(false)} complete={value => { setImportOpen(false); void catalogLoad(value).then(() => { if (value)
        setTab(0); }).catch(e => setError(e.message)); }}/>}{agentOpen && <McpModal onClose={() => setAgentOpen(false)} tenantGraph={tenant} sourceRevision={snapshot?.tenant_graph === tenant ? snapshot.source_revision : null}/>}
  </main>;
}
