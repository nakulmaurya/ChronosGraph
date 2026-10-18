"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { Activity, ArrowLeft, ArrowUpRight, Box, ChevronRight, Code2, FileCode2, Folder, GitBranch, GitCommitHorizontal, Layers, Network, Plus, Search, Shield, Terminal, X } from "lucide-react";
import { buildPairing, pinnedCommit } from "@/lib/release";
import { request, safeUrl } from "@/lib/api";
import { queryString } from "@/lib/workbench";
import { breadcrumbParent, boundedMapNotice, type RepositoryMap, type FileDetail, type HistoryData } from "@/lib/command-center";
import type { Tenant } from "@/lib/types";
import Workbench from "./Workbench";
import RepositoryImport from "./RepositoryImport";
import TrackTools from './TrackTools';
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
    next_cursor?: string | null; symbols_truncated?: boolean;
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
function readSavedRepository() { try { return localStorage.getItem("chronosgraph-repository"); } catch { return null; } }
const tabs = [{ name: "Repository", icon: Network }, { name: "Changes", icon: GitBranch }, { name: "History", icon: GitCommitHorizontal }, { name: "Ownership", icon: Shield }, { name: "Agent activity", icon: Activity }];
export default function CommandCenter() {
    const frontendCommit=pinnedCommit(process.env.NEXT_PUBLIC_CHRONOSGRAPH_BUILD_COMMIT);
    const [apiCommit,setApiCommit]=useState<string | null>(null);
    useEffect(()=>{const c=new AbortController();request<{application_commit:string|null}>("/release/identity",c.signal).then(r=>{if(!c.signal.aborted)setApiCommit(pinnedCommit(r.application_commit));}).catch(()=>{if(!c.signal.aborted)setApiCommit(null);});return ()=>c.abort();},[]);
    const pairing=buildPairing(frontendCommit,apiCommit);
    const [policyVersion,setPolicyVersion]=useState(0);
    const [catalog, setCatalog] = useState<Tenant[]>([]), [tenant, setTenant] = useState("");
    const [table, setTable] = useState(false);
    const [map, setMap] = useState<RepositoryMap | null>(null), [prefix, setPrefix] = useState("");
    const [detail, setDetail] = useState<FileDetail | null>(null), [snapshot, setSnapshot] = useState<Snapshot | null>(null);
    const [tab, setTab] = useState(0), [functions, setFunctions] = useState(false), [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchData | null>(null), [source, setSource] = useState<Source | null>(null);
    const [history, setHistory] = useState<HistoryData | null>(null), [commit, setCommit] = useState("");
    const [importOpen, setImportOpen] = useState(false), [agentOpen, setAgentOpen] = useState(false);
    const [error, setError] = useState(""), [loading, setLoading] = useState(false), [inspecting, setInspecting] = useState(false);
    const [mapError, setMapError] = useState("");
    const [mapAttempt, setMapAttempt] = useState(0);
    const [mapPages,setMapPages]=useState<string[]>([""]);
    const mapCursor=mapPages[mapPages.length-1];
    const [historyLoading, setHistoryLoading] = useState(false), [historyAttempt, setHistoryAttempt] = useState(0);
    const [historyPages,setHistoryPages]=useState<string[]>([""]),[changePages,setChangePages]=useState<string[]>([""]);
    const incomingLink = useRef<URLSearchParams | null>(null);
    const [linkNotice,setLinkNotice]=useState("");
    const operation = useRef<AbortController | null>(null);
    const current = catalog.find(t => t.tenant_graph === tenant);
    async function catalogLoad(pick = "", signal?: AbortSignal) {
        const rows = await request<Tenant[]>("/tenants", signal || new AbortController().signal);
        setCatalog(rows);
        const linked = new URLSearchParams(window.location.search).get("snapshot");
        if(!pick && !tenant && linked) {
            if(!rows.some(r => r.tenant_graph === linked)) { setError("The linked saved version is unavailable. Choose a saved version explicitly; it has not been substituted."); return; }
            incomingLink.current=new URLSearchParams(window.location.search); setTenant(linked); return;
        }
        setTenant(previous => pick || (rows.some(r => r.tenant_graph === previous) ? previous : rows.find(r => r.tenant_graph === readSavedRepository())?.tenant_graph || rows[0]?.tenant_graph || ""));
    }
    useEffect(() => { const c = new AbortController(); void catalogLoad("", c.signal).catch(e => { if (!c.signal.aborted)
        setError(e.message); }); return () => { c.abort(); operation.current?.abort(); }; }, []);
    useEffect(() => {
        if (!tenant)
            return;
        const c = new AbortController();
        operation.current?.abort();
        try { localStorage.setItem("chronosgraph-repository", tenant); } catch { /* Browsing still works without persistence. */ }
        setMapPages([""]);
        setPrefix("");
        setDetail(null);
        setResults(null);
        setSource(null);
        setCommit("");
        setHistoryPages([""]); setChangePages([""]);
        setHistory(null);
        setSnapshot(null);
        setMap(null);
        setMapError("");
        setFunctions(false);
        setQuery("");
        setTab(0);
        setError("");
        setInspecting(false);
        request<Snapshot>(`/workspace/snapshot?${queryString({ tenant_graph: tenant })}`, c.signal).then(value => { if (!c.signal.aborted) { setSnapshot(value);
            const linked=incomingLink.current;incomingLink.current=null;
            if(linked) {
                if(linked.get("revision") && linked.get("revision")!==value.source_revision) {setError("The linked commit does not match this saved version. Linked file navigation was stopped.");return;}
                const path=linked.get("file");const view=Number(linked.get("view")||0);
                if(path)void inspect(path);else if(Number.isInteger(view)&&view>=0&&view<tabs.length)setTab(view);
            }
        } }).catch(e => { if (!c.signal.aborted)
            setError(e.message); });
        return () => c.abort();
    }, [tenant]);
    useEffect(() => {
        if (!tenant)
            return;
        const c = new AbortController();
        setLoading(true);
        setMapError("");
        request<RepositoryMap>(`/repository/map?${queryString({ tenant_graph: tenant, prefix, after: mapCursor })}`, c.signal).then(value => { if (!c.signal.aborted) setMap(value); }).catch(e => { if (!c.signal.aborted)
            setMapError(e.message); }).finally(() => { if (!c.signal.aborted)
            setLoading(false); });
        return () => c.abort();
    }, [tenant, prefix, mapAttempt, mapCursor]);
    useEffect(() => {
        if (!tenant || tab !== 2)
            return;
        const c = new AbortController();
        setHistory(null);
        setHistoryLoading(true);
        setError("");
        request<HistoryData>(`/repository/history?${queryString({ tenant_graph: tenant, commit, after: historyPages[historyPages.length-1], change_after: changePages[changePages.length-1] })}`, c.signal).then(value => { if (!c.signal.aborted) setHistory(value); }).catch(e => { if (!c.signal.aborted)
            setError(e.message); }).finally(() => { if (!c.signal.aborted) setHistoryLoading(false); });
        return () => c.abort();
    }, [tenant, tab, commit, historyAttempt, historyPages, changePages]);
    async function inspect(path: string, symbol?: string) {
        operation.current?.abort();
        const c = new AbortController();
        operation.current = c;
        setInspecting(true);
        setError("");
        setSource(null);
        setDetail(null);
        try {
            const data = await request<FileDetail>(`/repository/file?${queryString({ tenant_graph: tenant, file_path: path })}`, c.signal);
            if (c.signal.aborted)
                return;
            setDetail(data);
            setTab(0);
            if (symbol) {
                setFunctions(true);
                const captured = await request<Source>(`/context/symbol-source?${queryString({ tenant_graph: tenant, file_path: path, symbol_name: symbol })}`, c.signal);
                if (!c.signal.aborted) setSource(captured);
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
    async function search(after = "") {
        operation.current?.abort();
        const c = new AbortController();
        operation.current = c;
        setError("");
        setInspecting(true);
        try {
            const found = await request<SearchData>(`/repository/search?${queryString({ tenant_graph: tenant, query, after })}`, c.signal);
            if (!c.signal.aborted) setResults(found);
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
    function updateQuery(value: string) { operation.current?.abort(); setInspecting(false); setQuery(value); setResults(null); }
    function folder(path: string) { operation.current?.abort(); setInspecting(false); setMapPages([""]); setPrefix(path); setMap(null); setDetail(null); setSource(null); setResults(null); setFunctions(false); setTab(0); }
    function pick(path: string, kind: string, symbol?: string) { if (kind === "folder")
        folder(path);
    else
        void inspect(path, symbol); }
    function switchTab(value: number) { operation.current?.abort(); setInspecting(false); setError(""); setTab(value); }
    function resetMap() { operation.current?.abort(); setInspecting(false); setDetail(null); setSource(null); setFunctions(false); }
    return <main className="cc-app">
    <aside className="cc-rail"><Link href="/workbench" aria-label="ChronosGraph home" className="cc-logo"><Network size={24}/></Link><div className="cc-rail-rule"/>{tabs.map((t, i) => <button key={t.name} title={t.name} aria-label={t.name} aria-current={tab === i ? "page" : undefined} className={tab === i ? "active" : ""} onClick={() => switchTab(i)}><t.icon size={19}/></button>)}<button title="Connect coding agent" aria-label="Connect coding agent" className="cc-rail-bottom" onClick={() => setAgentOpen(true)}><Terminal size={20}/></button></aside>
    <div className="cc-main"><header className="cc-topbar"><div className="cc-brand">ChronosGraph <span>/</span> <span>Workspace</span></div><div className="cc-top-actions"><span className="cc-local"><i />Local workspace</span><button aria-label="Connect agent" onClick={() => setAgentOpen(true)}><Terminal size={14}/>Connect agent</button><button aria-label="Import repository" className="cc-primary" onClick={() => setImportOpen(true)}><Plus size={15}/>Import repository</button></div></header>
      <div className="cc-projectbar"><div className="cc-project"><span className="cc-project-icon"><Box size={22}/></span><div><span className="cc-kicker">REPOSITORY COMMAND CENTER</span><select aria-label="Repository" value={tenant} disabled={!catalog.length} onChange={e => setTenant(e.target.value)}>{!tenant && <option value="">Choose a saved version</option>}{catalog.map(t => <option key={t.tenant_graph} value={t.tenant_graph}>{t.repository} · {t.source_revision?.slice(0,8) || "legacy"} · {t.tenant_graph.slice(-8)}</option>)}</select></div></div><div className="cc-revision"><span><GitBranch size={13}/>{snapshot?.selected_branch || "Pinned version"}</span><code>{snapshot?.source_revision?.slice(0, 8) || "Version unavailable"}</code><span className="cc-pill">{snapshot?.last_check.status === "MATCHED_AT_CHECK" ? "Matched at last check" : snapshot?.last_check.status === "PINNED_AT_IMPORT" ? "Saved at import" : "Saved snapshot"}</span></div></div>
      <p className="cc-help" aria-label="Application and saved snapshot identity" role={pairing==="MISMATCH" ? "alert" : undefined}>
        UI build <code title={frontendCommit||undefined}>{frontendCommit?.slice(0,8)||"unrecorded"}</code> · API build <code title={apiCommit||undefined}>{apiCommit?.slice(0,8)||"unrecorded"}</code> · {pairing==="MISMATCH" ? "Build mismatch — preview parity not verified" : pairing==="MATCHED_DECLARATIONS" ? "Matched build declarations" : "Build parity unverified"}. Saved source <code title={snapshot?.source_revision||undefined}>{snapshot?.source_revision?.slice(0,8)||"unavailable"}</code>.
      </p>
      {linkNotice && <p role="status" className="cc-help">{linkNotice}</p>}
      <nav className="cc-tabs" aria-label="Command center views">{tabs.map((t, i) => <button key={t.name} className={tab === i ? "active" : ""} aria-current={tab === i ? "page" : undefined} onClick={() => switchTab(i)}><t.icon size={15}/>{t.name}</button>)}<button disabled={!tenant || !snapshot?.source_revision} onClick={() => {
        const url=new URL(window.location.href);url.search="";
        url.searchParams.set("snapshot",tenant);url.searchParams.set("revision",snapshot!.source_revision!);
        if(detail)url.searchParams.set("file",detail.file.path);else url.searchParams.set("view",String(tab));
        void navigator.clipboard.writeText(url.toString()).then(()=>setLinkNotice("Workspace link copied: exact saved version, not live workspace state.")).catch(()=>setLinkNotice("Clipboard unavailable. Workspace link was not copied."));
      }}>Copy workspace link</button><Link href="/demo" className="cc-demo-link">Demo & wiki <ArrowUpRight size={13}/></Link></nav>
      {error && <div className="cc-error" role="alert">{error}<button aria-label="Dismiss error" onClick={() => setError("")}><X size={14}/></button></div>}
      {tab === 0 && <><section className="cc-overview"><div><h1>Your codebase. Connected.</h1><p>Find your way through the code, then see what a change could affect.</p></div><div className="cc-stats"><div><strong>{map ? (map.counts.TrackedFile ?? map.counts.File ?? 0).toLocaleString() : "—"}</strong><span>tracked files</span></div><div><strong>{map ? (map.counts.Function || 0).toLocaleString() : "—"}</strong><span>functions</span></div><div><strong>{map ? (map.counts.Class || 0).toLocaleString() : "—"}</strong><span>classes</span></div></div></section>
      <div className="cc-workspace"><aside className="cc-explorer"><div className="cc-panel-title"><span>EXPLORER</span><span>{map ? (map.counts.TrackedFile ?? map.counts.File ?? 0) : "…"}</span></div><form className="cc-search" onSubmit={e => { e.preventDefault(); void search(); }}><Search size={14}/><input aria-label="Search files and symbols" placeholder="Search files or symbols…" value={query} onChange={e => updateQuery(e.target.value)} maxLength={200}/><button aria-label="Run repository search" disabled={!query.trim() || inspecting}>↵</button></form>
        <div className={`cc-tree-scroll ${results ? "cc-search-results" : ""}`}>{results ? <><div className="cc-tree-caption">Search results <button onClick={() => updateQuery("")}>Clear</button></div>{!results.entry_points.length && <p className="cc-empty">No match. Try a file path or a shorter symbol name.</p>}{results.entry_points.map(f => <div key={f.path}><button className="cc-tree-file" title={f.path} onClick={() => void inspect(f.path)}><FileCode2 size={14}/><span>{f.path}</span></button>{f.symbols.slice(0, 8).map(s => <button className="cc-tree-symbol" key={s.name} onClick={() => void inspect(f.path, s.name)}>ƒ {s.name}</button>)}{f.symbols.length>8 && <p className="cc-limit">First 8 definitions shown. Open this file to inspect more.</p>}</div>)}{results.next_cursor && <button disabled={inspecting} onClick={() => void search(results.next_cursor!)}>Next search results</button>}{results.symbols_truncated && <p className="cc-limit">Some definitions are omitted. Narrow your query.</p>}</> : <>{prefix && <button className="cc-tree-file" onClick={() => folder(breadcrumbParent(prefix))}><ArrowLeft size={14}/>Parent folder</button>}{map?.nodes.map(n => <button key={n.id} className={`cc-tree-file ${detail?.file.path === n.path ? "active" : ""}`} title={n.path} onClick={() => pick(n.path, n.kind)}>{n.kind === "folder" ? <Folder size={14}/> : <FileCode2 size={14}/>}<span>{n.path.slice(prefix.length).replace(/\/$/, "")}</span>{n.kind === "folder" && <small>{n.files}</small>}</button>)}{(mapPages.length > 1 || map?.next_cursor) && <div className="cc-page-controls"><button disabled={loading || mapPages.length === 1} onClick={() => { setMap(null); setMapPages(p => p.slice(0,-1)); }}>Previous folders / files</button><span>Page {mapPages.length}</span><button disabled={loading || !map?.next_cursor} onClick={() => { if(map?.next_cursor) { setMapPages(p => [...p,map.next_cursor!]); setMap(null); } }}>Next folders / files</button></div>}{!map?.nodes.length && !loading && !mapError && <p className="cc-empty">No tracked files here.</p>}</>}</div>
        <div className="cc-explorer-footer"><Layers size={13}/>{loading ? "Loading repository…" : "File inventory · Python analysis"}</div></aside>
        <section className="cc-map-panel" aria-label="Interactive repository graph"><div className="cc-map-toolbar"><div className="cc-breadcrumb"><button onClick={() => folder("")}><Box size={13}/>Repository</button>{prefix && <><ChevronRight size={12}/><button onClick={resetMap}>{prefix}</button></>}{detail && <><ChevronRight size={12}/><span>{detail.file.path.split("/").pop()}</span></>}</div><div className="cc-segment"><button className={!functions ? "active" : ""} onClick={() => setFunctions(false)}>Dependencies</button><button className={functions ? "active" : ""} disabled={!detail || !!detail.file.analysis_status} onClick={() => setFunctions(true)}>Functions</button></div></div>
          <div className="cc-canvas" aria-busy={loading || inspecting}>{map && <CommandGraph table={table} setTable={setTable} map={map} detail={detail} functions={functions} selected={source ? source.qualified_name : detail?.file.path || ""} onPick={pick}/>} {(loading || inspecting) && <span className="cc-loading" role="status">{inspecting ? "Inspecting source…" : "Loading map…"}</span>}{mapError && !loading && <div className="cc-map-recovery" role="alert"><Network size={30}/><h2>Repository map unavailable.</h2><p>{mapError}</p><button className="cc-primary" onClick={() => setMapAttempt(value => value + 1)}>Retry map</button><p className="cc-help">Your saved repository has not been changed.</p></div>}{!tenant && !loading && <div className="cc-blank"><Network size={34}/><h2>Start with your repository.</h2><p>Import a public Python project to explore its structure.</p><button className="cc-primary" onClick={() => setImportOpen(true)}>Import repository</button></div>}</div>
          <div className="cc-map-footer"><span><i className="cc-dot"/>{detail ? detail.file.analysis_status ? "Inventory only · semantic dependencies unavailable" : functions ? "File definitions & resolved internal calls" : "Incoming ← selected file → imported dependencies" : "Folders group actual file-import relationships"}</span><span>{detail ? "Pinned graph data" : `Overview query · ${map?.execution_time_ms.toFixed(1) ?? "—"} ms`}</span></div>
          {map?.inventory_basis?.startsWith("LEGACY_") && <p className="cc-limit">This older snapshot contains Python files only. Import a new saved version for the complete tracked-file inventory.</p>}{map && boundedMapNotice(map) && <p className="cc-limit">Bounded map: {map.coverage.groups_total} groups in this folder. Use explorer paging to reach more files and folders. Edges are bounded Python imports only; inventory is not all-language semantic analysis.</p>}
          {detail && functions && detail.symbols.length > 60 && <p className="cc-limit">Showing the first 60 definitions on the canvas. The inspector lists up to 160.</p>}
        </section>
        <aside className="cc-inspector" aria-label="File inspector"><div className="cc-panel-title"><span>{detail ? "FILE INSPECTOR" : "GET YOUR BEARINGS"}</span>{detail && <button aria-label="Close file inspector" onClick={resetMap}><X size={14}/></button>}</div>
          {detail ? <><div className="cc-inspector-heading"><FileCode2 size={23}/><h2>{detail.file.path.split("/").pop()}</h2><p>{detail.file.path}</p><div className="cc-file-meta">{detail.file.analysis_status ? <span>{detail.file.language} · inventory only</span> : <><span>{detail.file.lines} lines</span><span>{detail.symbols.length} definitions</span></>}</div>{safeUrl(detail.file.source_url) && <a href={safeUrl(detail.file.source_url)} target="_blank" rel="noreferrer">View pinned source <ArrowUpRight size={12}/></a>}</div>
          <section className="cc-inspector-section"><button className="cc-primary" disabled={!!detail.file.analysis_status} onClick={() => switchTab(1)}>Plan a change to this file</button>{detail.file.analysis_status && <p className="cc-limit">{detail.file.analysis_status.replaceAll("_"," ").toLowerCase()}. This entry is included in the repository inventory, not dependency or source analysis. No missing edge should be treated as proof of no impact.</p>}</section>
          {!!detail.file.parse_errors && <p className="cc-limit">This file has parse errors. Dependencies may be incomplete.</p>}
          {!detail.file.analysis_status && <><section className="cc-inspector-section"><h3>What depends on this <span>{detail.importers.length}</span></h3><p>These files import the selected file.</p>{detail.importers.slice(0, 12).map(f => <button className="cc-dependency" key={f.path} onClick={() => void inspect(f.path)} title={f.path}><FileCode2 size={12}/><span>{f.path}</span><ChevronRight size={12}/></button>)}{!detail.importers.length && <p className="cc-empty">No resolved importers in this snapshot.</p>}</section>
          <section className="cc-inspector-section"><h3>Imports <span>{detail.imports.length}</span></h3>{detail.imports.slice(0, 12).map(f => <button className="cc-dependency" key={f.path} onClick={() => void inspect(f.path)} title={f.path}><FileCode2 size={12}/><span>{f.path}</span><ChevronRight size={12}/></button>)}{!detail.imports.length && <p className="cc-empty">No resolved local imports.</p>}</section>
          <section className="cc-inspector-section">{(detail.imports.length > 12 || detail.importers.length > 12) && <p className="cc-limit">Dependency lists show the first 12 per direction; the graph shows up to 20. Coverage details below record API limits.</p>}<h3>Functions & classes <span>{detail.symbols.length}</span></h3>{detail.symbols.map(s => <button className="cc-definition" key={s.qualified_name} onClick={() => void inspect(detail.file.path, s.qualified_name)}><div><Code2 size={12}/><code>{s.name}</code><small>L{s.start_line}</small></div>{s.docstring && <p>{s.docstring.split("\n")[0]}</p>}</button>)}{!detail.symbols.length && <p className="cc-empty">No captured definitions.</p>}</section>
          {source && <section className="cc-inspector-section"><h3>Source · L{source.start_line}–{source.end_line}</h3><pre>{source.source}</pre>{source.truncated && <p className="cc-limit">Source preview truncated. Open the pinned source for the full range.</p>}</section>}
          </>}<details className="cc-inspector-section"><summary>Index coverage & provenance</summary><p>Static relationships, not runtime dispatch. Missing edges do not prove no impact.</p><pre>{JSON.stringify(detail.coverage, null, 2)}</pre><small>File hash {detail.file.sha256?.slice(0, 16) || "not captured"}</small></details></> : <div className="cc-onboarding"><span className="cc-onboarding-icon"><Network size={28}/></span><h2>Follow the connections.</h2><p>Select a folder to zoom into the architecture. Select a file to see its dependencies, functions, and source.</p><ol><li><strong>Explore</strong><span>Start with folders or search a symbol.</span></li><li><strong>Understand</strong><span>Trace imports and inspect real definitions.</span></li><li><strong>Plan a change</strong><span>Preview downstream impact in Changes.</span></li></ol><button onClick={() => setAgentOpen(true)}><Terminal size={14}/>Connect your coding agent</button></div>}
        </aside></div>
        <footer className="cc-statusbar"><span>Saved version {snapshot?.source_revision?.slice(0, 8) || "—"} · not live workspace monitoring</span><span>{current?.repository || "No repository selected"}</span></footer></>}
      {tab === 2 && <section className="cc-history"><div className="cc-section-heading"><span className="cc-kicker">CHANGE EXPLORER</span><h1>Understand what changed.</h1><p>Commit-linked file changes from the indexed Git history.</p></div><div className="cc-history-grid"><div><h2>Indexed commits</h2>{historyLoading && <p role="status">Loading commit history…</p>}{!historyLoading && !history && <button onClick={() => setHistoryAttempt(value => value + 1)}>Retry history</button>}{history && !history.commits.length && <div className="cc-empty-card"><GitCommitHorizontal size={24}/><h3>No commit history in this saved version.</h3><p>Public archive imports capture one commit’s source, not its history. Connect a trusted local Git checkout to index bounded commit history.</p></div>}{history?.commits.map(c => <button className={`cc-commit ${commit === c.sha ? "active" : ""}`} key={c.sha} onClick={() => { setHistory(null); setChangePages([""]); setCommit(c.sha); }}><strong>{c.title}</strong><span><code>{c.sha.slice(0, 8)}</code> · {c.author || "Git author"} · {c.timestamp ? new Date(c.timestamp * 1000).toLocaleDateString() : "Date unavailable"}</span></button>)}<div className="cc-page-controls"><button disabled={historyLoading || historyPages.length===1} onClick={() => setHistoryPages(p => p.slice(0,-1))}>Newer commits</button><button disabled={historyLoading || !history?.next_cursor} onClick={() => { if(history?.next_cursor)setHistoryPages(p => [...p,history.next_cursor!]); }}>Older commits</button></div></div><div><h2>{commit ? "Files changed in this commit" : "Select a commit"}</h2>{commit && <button onClick={() => { setHistory(null); setChangePages([""]); setCommit(""); }}>All indexed commits</button>}<p className="cc-help">File inspection opens the current indexed source—not the historical commit’s source.</p>{history?.changes.map(f => <button className="cc-changed-file" key={f.path} disabled={f.status === "D"} title={f.status === "D" ? "Deleted in this commit. Historical source checkout is not available." : "Open current saved source, which may differ or be absent"} onClick={() => void inspect(f.path)}><FileCode2 size={14}/><span>{f.path}{f.status && ` · ${f.status === "D" ? "deleted" : f.status === "A" ? "added" : "modified"}`}</span><code>+{f.additions} −{f.deletions}</code><ArrowUpRight size={13}/></button>)}{commit && history && !history.changes.length && <p>No indexed file links for this commit.</p>}{history?.change_basis === "LEGACY_CURRENT_PYTHON_FILES_ONLY" && <p className="cc-limit">Older snapshot: only links to current Python files were captured. Reimport local Git history to include deleted and non-Python files.</p>}<div className="cc-page-controls"><button disabled={historyLoading || changePages.length===1} onClick={() => setChangePages(p => p.slice(0,-1))}>Previous file changes</button><button disabled={historyLoading || !history?.change_next_cursor} onClick={() => { if(history?.change_next_cursor)setChangePages(p => [...p,history.change_next_cursor!]); }}>Next file changes</button></div></div></div></section>}
      {tab === 1 && tenant && <ChangePlanner key={`${tenant}:${detail?.file.path || ""}`} tenant={tenant} revision={snapshot?.tenant_graph === tenant ? snapshot.source_revision : null} path={detail?.file.path || ""} onInspect={path => void inspect(path)}/>}
      {(tab === 3 || tab === 4) && <section className="cc-tools"><div className="cc-section-heading"><span className="cc-kicker">{tab === 3 ? "KNOW WHO AND WHY" : "HUMAN + AGENT"}</span><h1>{tab === 3 ? "Rules, authors, and owners." : "Keep the work visible."}</h1><p>{tab === 3 ? "Understand the current rules and people connected to this code." : "Real tool calls and source-linked findings. No invented agent thoughts."}</p></div>{tenant && <Workbench key={`${tenant}:${policyVersion}`} fixedTenant={tenant} fixedPath={detail?.file.path || ""} onInspect={path => void inspect(path)} active evidenceEntries={detail?.file.sha256 ? [{ path: detail.file.path, sha256: detail.file.sha256 }] : []} defaultView={tab === 3 ? 2 : 3}/>} {tenant&&<TrackTools key={`${tenant}:${tab}:${detail?.file.path||''}`} tenant={tenant} revision={snapshot?.tenant_graph===tenant?snapshot.source_revision:null} path={detail?.file.path||''} kind={tab===3?'ownership':'memory'} onPolicyChanged={()=>setPolicyVersion(n=>n+1)}/>}</section>}
    </div>{importOpen && <RepositoryImport close={() => setImportOpen(false)} complete={value => { setImportOpen(false); void catalogLoad(value).then(() => { if (value)
        setTab(0); }).catch(e => setError(e.message)); }}/>}{agentOpen && <McpModal onClose={() => setAgentOpen(false)} tenantGraph={tenant} sourceRevision={snapshot?.tenant_graph === tenant ? snapshot.source_revision : null}/>}
  </main>;
}
