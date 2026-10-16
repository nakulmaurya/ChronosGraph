"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Activity,
  ArrowRight,
  Braces,
  ChevronRight,
  Database,
  GitBranch,
  Layers3,
  LoaderCircle,
  Play,
  Plug,
  RefreshCw,
  ShieldCheck,
  Terminal,
  Workflow,
} from "lucide-react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { replayEvidence } from "@/lib/graph";
import { ApiError, API_BASE, ms, request } from "@/lib/api";
import type {
  Audit,
  Brain,
  Investigation,
  Result,
  Subgraph,
  Tenant,
  VisualNode,
} from "@/lib/types";
import {
  Badge,
  BaselineCard,
  ComparisonStrip,
  NodeInspector,
  ResultInspector,
} from "./Evidence";
import McpModal from "./McpModal";
import SecondBrain from "./SecondBrain";
const GraphCanvas = dynamic(() => import("./GraphCanvas"), {
  ssr: false,
  loading: () => <div className="canvas-loading">Loading graph renderer…</div>,
});
const tracks = [
  { id: 1, title: "Crash-test clone", subtitle: "GRAPH.COPY", icon: Layers3 },
  { id: 2, title: "Memory compiler", subtitle: "shortestPath", icon: Workflow },
  {
    id: 3,
    title: "Time-travel rulebook",
    subtitle: "Bi-temporal lineage",
    icon: ShieldCheck,
  },
];
export default function Arena() {
  const [catalog, setCatalog] = useState<Tenant[]>([]);
  const [tenant, setTenant] = useState("");
  const [track, setTrack] = useState(1);
  const [graph, setGraph] = useState<Subgraph | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [selected, setSelected] = useState<VisualNode | null>(null);
  const [loading, setLoading] = useState("Connecting to local backend");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [modal, setModal] = useState(false);
  const [stale, setStale] = useState(false);
  const [files, setFiles] = useState<string[]>([]);
  const [pr, setPr] = useState("");
  const [patchCode, setPatchCode] = useState("");
  const [patchEnabled, setPatchEnabled] = useState(false);
  const [graphOwner, setGraphOwner] = useState("");
  const [graphContext, setGraphContext] = useState("Source overview");
  const overviewCache = useRef(new Map<string, Subgraph>());
  const [description, setDescription] = useState("");
  const [issue, setIssue] = useState("");
  const [file, setFile] = useState("");
  const [question, setQuestion] = useState(
    "What is the current policy for this file, and what did it replace?",
  );
  const [scope, setScope] = useState("module_root");
  const [rule, setRule] = useState("");
  const [rationale, setRationale] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [cold, setCold] = useState<Investigation | null>(null);
  const [compiledIssue, setCompiledIssue] = useState("");
  const activeRequest = useRef<AbortController | null>(null);
  const sequence = useRef(0);
  const tenantRef = useRef("");
  const busy = Boolean(loading);
  const current = catalog.find((t) => t.tenant_graph === tenant);
  function begin(label: string) {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;
    const id = ++sequence.current;
    setLoading(label);
    setError("");
    setNotice("");
    return { controller, id };
  }
  const fetchCatalog = useCallback(async () => {
    const { controller, id } = begin("Connecting to local backend");
    try {
      const tenants = await request<Tenant[]>("/tenants", controller.signal);
      if (id !== sequence.current) return;
      if (!tenants.length)
        throw new Error(
          "The backend returned no seeded repositories. Run the seeder, then retry.",
        );
      setCatalog(tenants);
      setTenant((t) =>
        tenants.some((x) => x.tenant_graph === t) ? t : tenants[0].tenant_graph,
      );
    } catch (e) {
      if (!controller.signal.aborted && id === sequence.current)
        setError(e instanceof Error ? e.message : "Cannot load tenant catalog");
    } finally {
      if (id === sequence.current) setLoading("");
    }
  }, []);
  useEffect(() => {
    void fetchCatalog();
    return () => {
      activeRequest.current?.abort();
      sequence.current++;
    };
  }, [fetchCatalog]);
  useEffect(() => {
    if (!tenant) return;
    tenantRef.current = tenant;
    setResult(null);
    const cached = overviewCache.current.get(tenant);
    if (cached) {
      setGraph(cached);
      setGraphOwner(tenant);
      setGraphContext("Source overview");
    }
    setSelected(null);
    setCold(null);
    setCompiledIssue("");
    setStale(false);
    setPr("");
    setRule("");
    setRationale("");
    setConfirmed(false);
    const entry = catalog.find((t) => t.tenant_graph === tenant);
    setPatchEnabled(false);
    const module = (entry?.preset_files[0] || "example.py")
      .replace(/^.*?src\//, "")
      .replace(/\.py$/, "")
      .replace(/\//g, ".");
    setPatchCode(
      tenant === "repo_falkordb_py"
        ? "from falkordb.query_result import __parse_string\n\ndef parse_response(value, graph):\n    return __parse_string(value, graph)\n"
        : `import ${module} as repository_module\n\ndef bounded_timeout(seconds):\n    return max(1, seconds)\n\ndef proposed_timeout(seconds):\n    return bounded_timeout(seconds)\n`,
    );
    setFiles(entry?.preset_files.slice(0, 1) || []);
    setFile(entry?.preset_files[0] || "");
    setIssue(
      `Review the current policy for ${entry?.preset_files[0] || "the selected file"}`,
    );
    setScope("module_root");
    const { controller, id } = begin("Loading source graph");
    request<Subgraph>(
      `/subgraph?tenant_graph=${encodeURIComponent(tenant)}`,
      controller.signal,
    )
      .then((g) => {
        if (id === sequence.current) {
          overviewCache.current.set(tenant, g);
          setGraph(g);
          setGraphOwner(tenant);
          setGraphContext("Source overview");
        }
      })
      .catch((e) => {
        if (!controller.signal.aborted && id === sequence.current)
          setError(e.message);
      })
      .finally(() => {
        if (id === sequence.current) setLoading("");
      });
    return () => controller.abort();
    // Catalog refresh is not a tenant switch; a new tenant always uses the current catalog.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenant]);
  function switchTrack(id: number) {
    if (busy) return;
    activeRequest.current?.abort();
    sequence.current++;
    setTrack(id);
    setResult(null);
    setSelected(null);
    // Keep this tenant’s last evidence visible until a new action completes.
    setError("");
    setNotice("");
  }
  async function run(kind: "audit" | "brain" | "cold" | "replay" | "override") {
    if (busy || !current) return;
    const requestedTenant = tenant;
    const { controller, id } = begin(
      (
        {
          audit: "Cloning graph & auditing potential impact",
          brain: "Reading current and superseded policies",
          cold: "Recording deterministic triage",
          replay: "Replaying verified graph tools",
          override: "Writing local policy override",
        } as const
      )[kind],
    );
    setSelected(null);
    setStale(false);
    const path =
      kind === "audit"
        ? "/track1/sandbox-audit"
        : kind === "brain"
          ? "/track3/ask-brain"
          : kind === "override"
            ? "/track3/override-policy"
            : "/track2/investigate";
    const body =
      kind === "audit"
        ? {
            tenant_graph: tenant,
            modified_files: files,
            pr_number: pr ? Number(pr) : null,
            proposed_description: description,
            proposed_code_patch: patchEnabled ? patchCode : null,
          }
        : kind === "brain"
          ? { tenant_graph: tenant, question, file_path: file || null }
          : kind === "override"
            ? {
                tenant_graph: tenant,
                target_file_path: file,
                scope_symbol: scope,
                new_rule_text: rule,
                rationale,
              }
            : {
                tenant_graph: tenant,
                issue_description: issue.trim(),
                execution_mode:
                  kind === "cold" ? "cold_multi_agent" : "compiled_playbook",
              };
    try {
      const data = await request<Audit | Brain | Investigation>(
        path,
        controller.signal,
        body,
      );
      if (id !== sequence.current || tenantRef.current !== requestedTenant)
        return;
      const next: Result =
        kind === "audit"
          ? { kind: "audit", data: data as Audit }
          : kind === "brain" || kind === "override"
            ? { kind: "brain", data: data as Brain }
            : { kind: "memory", data: data as Investigation };
      setResult(next);
      setGraph(
        kind === "replay" && cold
          ? replayEvidence(data.subgraph, cold.subgraph)
          : data.subgraph,
      );
      setGraphOwner(requestedTenant);
      setGraphContext(
        kind === "audit"
          ? "Track 1 audit"
          : kind === "cold"
            ? "Track 2 cold investigation"
            : kind === "replay"
              ? "Track 2 replay + historical cold evidence (not re-executed)"
              : "Track 3 policy lineage",
      );
      if (kind === "cold") {
        setCold(data as Investigation);
        setCompiledIssue(issue.trim());
      }
      if (kind === "brain" || kind === "override") {
        const brain = data as Brain;
        const existingScope = brain.active_decisions[0]?.scope_symbol;
        if (typeof existingScope === "string") setScope(existingScope);
      }
      if (kind === "override") {
        setCold(null);
        setCompiledIssue("");
        setConfirmed(false);
        setNotice(
          "Policy override recorded. Prior history is preserved; run a fresh cold triage before replay.",
        );
      }
    } catch (e) {
      if (!controller.signal.aborted && id === sequence.current) {
        setError(e instanceof Error ? e.message : "Request failed");
        if (
          kind === "replay" &&
          e instanceof ApiError &&
          (e.status === 404 || e.status === 409)
        ) {
          setStale(true);
          // Retain the last cold measurement for the previous-result inspector.
          // Replay is invalidated independently via stale + compiledIssue.
          setCompiledIssue("");
        }
        if (kind === "override") {
          setConfirmed(false);
          setNotice(
            "If the connection failed after submission, read the rulebook before retrying: the write may already have succeeded.",
          );
        }
      }
    } finally {
      if (id === sequence.current) setLoading("");
    }
  }
  useEffect(() => {
    document.querySelector(".results-panel")?.scrollTo({ top: 0 });
  }, [result]);
  function changeFile(path: string) {
    setFile(path);
    setConfirmed(false);
    setRule("");
    setRationale("");
    setScope("module_root");
  }
  const replayReady = Boolean(cold && compiledIssue === issue.trim() && !stale);
  return (
    <main className="arena bg-slate-950 text-slate-100">
      <header className="topbar">
        <a className="brand" href="/" aria-label="ChronosGraph home">
          <span className="brand-mark">
            <GitBranch size={22} />
          </span>
          <span>
            Chronos<span className="brand-light">Graph</span>
            <small>V1.4 · SECOND BRAIN + CONTEXT MODE</small>
          </span>
        </a>
        <div className="tenant-control">
          <Database size={15} />
          <label className="sr-only" htmlFor="tenant">
            Repository
          </label>
          <select
            id="tenant"
            value={tenant}
            disabled={!catalog.length || busy}
            onChange={(e) => setTenant(e.target.value)}
          >
            {!catalog.length && <option value="">Waiting for backend…</option>}
            {catalog.map((t) => (
              <option key={t.tenant_graph} value={t.tenant_graph}>
                {t.repository} · {t.node_count.toLocaleString()} nodes
              </option>
            ))}
          </select>
        </div>
        <div className="header-actions"><span id="second-brain-trigger" />
          <span className="connection">
            <Activity size={14} />
            {graph ? ms(graph.execution_time_ms) : "No query timing"}
          </span>
          <button
            className="button secondary compact"
            onClick={() => setModal(true)}
          >
            <Plug size={15} />
            MCP config
          </button>
        </div>
      </header>
      <div className="wb-entry"><Link href="/workbench">Open T-09 workbench preview →</Link></div>
      <nav className="trackbar" aria-label="Investigation tracks">
        {tracks.map((t) => (
          <button
            key={t.id}
            className={`track ${track === t.id ? "selected" : ""}`}
            disabled={busy}
            aria-current={track === t.id ? "page" : undefined}
            onClick={() => switchTrack(t.id)}
          >
            <t.icon size={18} />
            <span>
              <small>TRACK 0{t.id}</small>
              {t.title}
            </span>
            <code>{t.subtitle}</code>
          </button>
        ))}
        <span className="zero-model">LOCAL / ZERO MODEL CALLS</span>
      </nav>
      <div className="workspace-intro">
        <div>
          <span className="eyebrow">
            CONNECTED CONTEXT, PRESERVED PROVENANCE
          </span>
          <h1>
            {track === 1
              ? "See beyond the changed file."
              : track === 2
                ? "Don’t repeat the wrong turns."
                : "The latest rule. Not the loudest document."}
          </h1>
        </div>
        <span className="scope-label">
          <Terminal size={14} />
          Trusted localhost demo
        </span>
      </div>
      <SecondBrain tenant={tenant} selected={selected} target={result?.kind === "brain" ? result.data.file_path : result?.kind === "audit" ? String(result.data.subgraph.nodes.find(n=>n.metadata.audit_target)?.metadata.path||"") : result?.kind === "memory" ? result.data.resume_snapshot?.file_path : undefined} revision={result ? JSON.stringify([result.kind,result.data.subgraph.execution_time_ms,result.data.subgraph.nodes.map(n=>n.id)]) : ""} />
      {(error || notice || loading) && (
        <div className="notification-stack">
          {loading && (
            <div className="loading-banner" role="status">
              <LoaderCircle size={16} className="spin" />
              {loading}…
            </div>
          )}
          {error && (
            <div role="alert" className="error-banner">
              <strong>
                {stale
                  ? "Playbook unavailable or stale. Run a fresh cold triage."
                  : "Request could not complete."}
              </strong>
              <span>{error}</span>
              {!busy && (
                <button
                  className="text-button"
                  onClick={() => {
                    if (!catalog.length) void fetchCatalog();
                    else
                      void run(
                        track === 1 ? "audit" : track === 2 ? "cold" : "brain",
                      );
                  }}
                >
                  <RefreshCw size={14} />
                  Retry {track === 2 ? "cold triage" : ""}
                </button>
              )}
            </div>
          )}
          {notice && (
            <p role="status" className="notice-banner">
              {notice}
            </p>
          )}
        </div>
      )}
      <div className="workbench">
        <aside className="controls-panel" aria-label="Track controls">
          <div className="panel-heading">
            <span className="eyebrow">01 / RUN CONTROL</span>
            <Braces size={16} />
          </div>
          <section className="control-section">
            <h2>
              {track === 1
                ? "Crash-test a change"
                : track === 2
                  ? "Compile the investigation"
                  : "Inspect the rulebook"}
            </h2>
            <p>
              {track === 1
                ? "Clone the graph. Trace potential impact. Delete the clone."
                : track === 2
                  ? "Deterministic Scout → Historian → Verifier tools. Explore five actions, retain three."
                  : "Retrieve active policy, its history, and PR-linked expertise."}
            </p>
            {track === 1 && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void run("audit");
                }}
              >
                <label htmlFor="pr">
                  Snapshot PR / git commit <span>optional</span>
                </label>
                <select
                  id="pr"
                  value={pr}
                  onChange={(e) => {
                    setPr(e.target.value);
                    if (e.target.value) setFiles([]);
                  }}
                  disabled={busy}
                >
                  <option value="">Choose files manually</option>
                  {current?.pull_requests.map((p) => (
                    <option key={p.number} value={p.number}>
                      {p.record_kind === "COMMIT"
                        ? `Git ${p.commit_sha?.slice(0, 8)}`
                        : `#${p.number}`}{" "}
                      · {p.title}
                    </option>
                  ))}
                </select>
                <fieldset disabled={busy}>
                  <legend>
                    Modified files <span>preset snapshot</span>
                  </legend>
                  <div className="file-choices">
                    {current?.preset_files.map((path) => (
                      <label key={path} className="file-choice">
                        <input
                          type="checkbox"
                          checked={files.includes(path)}
                          onChange={(e) =>
                            setFiles((previous) =>
                              e.target.checked
                                ? [...previous, path]
                                : previous.filter((p) => p !== path),
                            )
                          }
                        />
                        <span>{path}</span>
                      </label>
                    ))}
                    {!current?.preset_files.length && (
                      <p>No policy-governed preset files returned.</p>
                    )}
                  </div>
                </fieldset>
                <p className="field-note">
                  Selecting a PR/commit uses its ingested changed Python files.
                  Explicit checkboxes take priority. The optional snippet
                  overlays the first selected file; it is not fetched commit
                  diff content.
                </p>
                <label htmlFor="description">
                  Proposed change <span>context only</span>
                </label>
                <textarea
                  id="description"
                  value={description}
                  maxLength={8000}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the change being assessed"
                  disabled={busy}
                />
                <details className="patch-editor">
                  <summary>Proposed Python patch (AST-parsed in clone)</summary>
                  <label className="check-line">
                    <input
                      type="checkbox"
                      checked={patchEnabled}
                      onChange={(e) => setPatchEnabled(e.target.checked)}
                      disabled={busy}
                    />{" "}
                    Apply Python snippet overlay
                  </label>
                  <label htmlFor="python-patch">Editable Python snippet or single-file git diff</label>
                  <textarea
                    id="python-patch"
                    className="mono"
                    value={patchCode}
                    maxLength={32000}
                    spellCheck={false}
                    onChange={(e) => setPatchCode(e.target.value)}
                    disabled={busy}
                  />
                  <p className="field-note">
                    Additive imports, definitions and conservatively resolved
                    calls. Diffs must match captured source at the ingested revision. Parsed, never executed. Unresolved calls are
                    reported, not guessed.
                  </p>
                </details>
                <button
                  className="button primary"
                  type="submit"
                  disabled={busy || !tenant || (!files.length && !pr)}
                >
                  <Layers3 size={16} />
                  Run GRAPH.COPY audit
                  <ArrowRight size={15} />
                </button>
                <p className="field-note">
                  {patchEnabled
                    ? "AST_PATCH_SIMULATION · additive snippet overlay inside the clone only."
                    : "SIMULATED_PR_DEPENDENCY · enable the Python snippet for actual AST-parsed dependencies."}
                </p>
              </form>
            )}
            {track === 2 && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void run("cold");
                }}
              >
                <label htmlFor="scenario">Policy triage scenario</label>
                <textarea
                  id="scenario"
                  value={issue}
                  maxLength={8000}
                  onChange={(e) => setIssue(e.target.value)}
                  disabled={busy}
                />
                <p className="field-note">
                  Mention a real policy-governed file. This is policy triage,
                  not arbitrary bug diagnosis.
                </p>
                <button
                  className="button primary"
                  disabled={busy || !tenant || !issue.trim()}
                >
                  <Play size={16} />
                  Run #1 · Cold triage
                </button>
                <div className="path-note">
                  <span>6 states · 5 tool actions</span>
                  <span>2 dead-end branches</span>
                </div>
                <button
                  type="button"
                  className="button secondary"
                  disabled={busy || !replayReady}
                  onClick={() => void run("replay")}
                >
                  <Workflow size={16} />
                  Run #2 · Compiled replay
                </button>
                <div className="path-note">
                  <span>3 verified actions</span>
                  <span>No dead ends replayed</span>
                </div>
                {!replayReady && issue.trim() && <button type="button" className="button secondary" disabled={busy} onClick={()=>void run("replay")}>Check backend replay guard</button>}
                {!replayReady && (
                  <p className="field-note">
                    Run cold triage for this exact scenario first. Changing the
                    scenario or tenant requires a fresh run.
                  </p>
                )}
                <div className="honesty-note">
                  <strong>Real work reduction.</strong>
                  <br />
                  40% fewer tool actions in the approved topology. Token savings
                  are unmeasured: no external model is called.
                </div>
              </form>
            )}
            {track === 3 && (
              <>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void run("brain");
                  }}
                >
                  <label htmlFor="policy-file">Policy-governed file</label>
                  <select
                    id="policy-file"
                    value={file}
                    onChange={(e) => changeFile(e.target.value)}
                    disabled={busy}
                  >
                    {!current?.preset_files.length && (
                      <option value="">No files available</option>
                    )}
                    {current?.preset_files.map((path) => (
                      <option key={path} value={path}>
                        {path}
                      </option>
                    ))}
                  </select>
                  <label htmlFor="question">Policy question</label>
                  <textarea
                    id="question"
                    value={question}
                    maxLength={8000}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={busy}
                  />
                  <button
                    className="button primary"
                    disabled={busy || !tenant || !question.trim()}
                  >
                    <ShieldCheck size={16} />
                    Read current policy
                  </button>
                  <p className="field-note">
                    Vectors use lexical hashing, not semantic LLM embeddings.
                  </p>
                </form>
                <details className="override-form">
                  <summary>
                    Live architect policy override <ChevronRight size={15} />
                  </summary>
                  <p>
                    Writes to this local tenant. Prior rules are retained as
                    SUPERSEDED. Read the file’s policy first to discover its
                    exact scope.
                  </p>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      void run("override");
                    }}
                  >
                    <label htmlFor="target-file">Target file</label>
                    <input id="target-file" value={file} readOnly />
                    <label htmlFor="scope">Scope symbol</label>
                    <input
                      id="scope"
                      maxLength={256}
                      value={scope}
                      onChange={(e) => setScope(e.target.value)}
                      required
                      disabled={busy}
                    />
                    <label htmlFor="rule">New active rule</label>
                    <textarea
                      id="rule"
                      maxLength={8000}
                      value={rule}
                      onChange={(e) => setRule(e.target.value)}
                      required
                      disabled={busy}
                    />
                    <label htmlFor="rationale">Rationale</label>
                    <textarea
                      id="rationale"
                      maxLength={8000}
                      value={rationale}
                      onChange={(e) => setRationale(e.target.value)}
                      required
                      disabled={busy}
                    />
                    <label className="file-choice confirmation">
                      <input
                        type="checkbox"
                        checked={confirmed}
                        onChange={(e) => setConfirmed(e.target.checked)}
                        disabled={busy}
                      />
                      I confirm this mutates the selected local graph.
                    </label>
                    <button
                      className="button danger"
                      disabled={
                        busy ||
                        !file ||
                        !scope.trim() ||
                        !rule.trim() ||
                        !rationale.trim() ||
                        !confirmed
                      }
                    >
                      Record policy override
                    </button>
                    <p className="field-note">
                      Recorded as lead-maintainer (demo actor), not verified
                      GitHub identity. Mixed scopes are guarded with HTTP 409.
                    </p>
                  </form>
                </details>
              </>
            )}
          </section>
          <BaselineCard baseline={result?.data.blind_agent_comparison} />
          <div className="source-note">
            <Database size={15} />
            <span>
              Real repository snapshots.
              <br />
              Explicitly labeled demo policies.
            </span>
          </div>
        </aside>
        <section className="canvas-panel" aria-label="Graph flight recorder">
          <p className="canvas-context" role="status">
            {graphOwner && graphOwner !== tenant
              ? `Loading selected repository · previous evidence: ${catalog.find((t) => t.tenant_graph === graphOwner)?.repository || graphOwner}`
              : `${current?.repository || "Connecting"} · ${graphContext}`}
          </p>
          <GraphCanvas
            graph={graph}
            onSelect={(n) => {
              if (graphOwner === tenant) setSelected(n);
            }}
          />
        </section>
        <aside className="results-panel" aria-label="Results and provenance">
          <div className="panel-heading">
            <span className="eyebrow">03 / EVIDENCE INSPECTOR</span>
            <ShieldCheck size={16} />
          </div>
          <ComparisonStrip result={result} cold={cold} />
          <div id="second-brain-inspector" />
          {error && result && (
            <p className="retained-result-note">
              Previous successful result retained below. The latest request
              failed.
            </p>
          )}
          {selected && (
            <NodeInspector node={selected} onClose={() => setSelected(null)} />
          )}
          <ResultInspector result={result} cold={cold} />
        </aside>
      </div>
      <footer className="statusbar">
        <span>
          <GitBranch size={13} />
          {current?.repository || "Backend not connected"}
        </span>
        <span title={API_BASE}>{API_BASE}</span>
        <span>Scoped evidence · no production safety guarantee</span>
      </footer>
      {modal && <McpModal onClose={() => setModal(false)} />}
    </main>
  );
}
