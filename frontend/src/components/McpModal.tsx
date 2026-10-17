"use client";
import { useEffect, useRef, useState } from "react";
import { Copy, X } from "lucide-react";
import { buildAgentConfig, buildSnapshotHandoff } from "@/lib/agent-connection";
const tools = [
  ["discover_repositories", "cursor?, limit?", "List saved versions and exact commit hashes. Select explicitly before continuing."],
  ["inspect_repository_snapshot", "tenant_graph, expected_revision", "Confirm the selected saved version; return guard arguments to pass on every call."],
  [
    "simulate_pr_blast_radius",
    "modified_files: string[], tenant_graph?, pr_number?, proposed_description?, proposed_code_patch?",
    "Audit a disposable clone with optional AST-parsed Python snippet overlays.",
  ],
  [
    "query_bitemporal_decisions",
    "question: string, tenant_graph?, file_path?",
    "Retrieve active and superseded rules with provenance.",
  ],
  [
    "record_decision_override",
    "target_file_path, new_rule_text, rationale, tenant_graph?, scope_symbol?, author_handle?",
    "Mutates local policy state; scope must match.",
  ],
  [
    "find_true_code_owners",
    "file_path: string, tenant_graph?",
    "Rank bounded PR/review and git-commit contributor evidence.",
  ],
  [
    "run_or_compile_playbook",
    "issue_description, tenant_graph?, execution_mode?",
    "Run deterministic triage or replay a current compiled path.",
  ],
  ["simulate_diff_impact", "tenant_graph?, unified_diff? OR file_bodies?", "Preview full-file Python replacements and removed dependencies in a disposable clone."],
  ["locate_context", "query, tenant_graph?, budget_bytes?", "Find compact pinned-snapshot context; workspace freshness has not been checked."],
  ["get_symbol_source", "file_path, symbol_name, tenant_graph?", "Read one captured symbol and its exact coordinates/hash."],
  ["record_verified_finding", "summary, evidence_note, supporting_file_shas, tenant_graph?", "Store agent-reported evidence; no verification command is executed."],
  ["recall_task_memory", "query?, tenant_graph?, include_stale?", "Recall findings and flag changed files or governing policies."],
  ["propose_change_for_approval", "tenant_graph, expected_revision, task_title, proposed_files, idempotency_key, client_id?", "Preview an immutable proposal and wait for the human decision."],
  ["check_proposal_decision", "tenant_graph, expected_revision, proposal_id", "Check approval and current source/policy guards."],
  ["report_proposal_execution", "tenant_graph, expected_revision, proposal_id, proposal_hash, command_executed, exit_code, output_excerpt, idempotency_key", "Store an unverified client execution report; never run commands or mint observed evidence."]
];
export default function McpModal({ onClose, tenantGraph = "", sourceRevision = null }: { onClose: () => void; tenantGraph?: string; sourceRevision?: string | null }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [cwd, setCwd] = useState("/absolute/path/to/ChronosGraph/backend");
  const [copied, setCopied] = useState("");
  const [python, setPython] = useState("python");
  const [host, setHost] = useState("127.0.0.1");
  const [port, setPort] = useState("6379");
  const handoff = buildSnapshotHandoff(tenantGraph, sourceRevision);
  const [platform, setPlatform] = useState("Claude Code");
  const skillPath = "skills/chronos-second-brain/SKILL.md";
  let config = "", configError = "";
  try { config = buildAgentConfig({ backendDirectory: cwd, pythonExecutable: python, databaseHost: host, databasePort: port }); }
  catch (error) { configError = error instanceof Error ? error.message : "Check connection settings."; }
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      previous?.focus();
    };
  }, []);
  async function copy() {
    try {
      await navigator.clipboard.writeText(config);
      setCopied("Copied config");
    } catch {
      setCopied("Copy unavailable. Select and copy the JSON below.");
    }
  }
  return (
    <dialog
      ref={ref}
      onCancel={onClose}
      aria-labelledby="mcp-title"
      className="mcp-dialog"
    >
      <div className="section-row">
        <div>
          <span className="eyebrow">LOCAL STDIO CONNECTION</span>
          <h2 id="mcp-title">Bring the graph to your agent.</h2>
        </div>
        <button
          className="icon-button"
          aria-label="Close MCP config"
          onClick={onClose}
        >
          <X size={20} />
        </button>
      </div>
      <p>
        Configure your coding client, then ask it to discover your saved repository.
        This screen does not install a connection or prove the client is connected.
        The backend and FalkorDB must be reachable from the machine running your agent;
        a browser SSH tunnel alone does not provide an agent connection.
      </p>
      <div className="wiki-nav" role="tablist" aria-label="MCP platform">
        {["Claude Code","Cursor","Antigravity / OpenCode"].map(name=><button key={name} role="tab" aria-selected={platform===name} className="button secondary" onClick={()=>setPlatform(name)}>{name}</button>)}
      </div>
      <p>{platform}: use the client's supported stdio MCP configuration. This is a generic template, not an installed integration. Reference the portable skill from the client's project instructions; discovery varies by platform.</p>
      <p className="mono">{skillPath}</p>
      <button className="button secondary" onClick={async()=>{try{await navigator.clipboard.writeText(skillPath);setCopied("Copied skill path");}catch{setCopied("Select the skill path above");}}}>Copy SKILL.md path</button>
      <label htmlFor="mcp-cwd">Absolute backend directory</label>
      <input
        id="mcp-cwd"
        value={cwd}
        onChange={(e) => {
          setCwd(e.target.value);
          setCopied("");
        }}
      />
      <p className="subtle">
        Use the Python executable from your installed backend environment if
        needed.
      </p>
      <label htmlFor="mcp-python">Python executable on agent machine</label>
      <input id="mcp-python" value={python} onChange={e => {setPython(e.target.value);setCopied("");}} />
      <label htmlFor="mcp-host">FalkorDB host on agent machine</label>
      <input id="mcp-host" value={host} onChange={e => {setHost(e.target.value);setCopied("");}} />
      <label htmlFor="mcp-port">FalkorDB port</label>
      <input id="mcp-port" inputMode="numeric" value={port} onChange={e => {setPort(e.target.value);setCopied("");}} />
      {configError ? <p role="alert">{configError}</p> : <pre>{config}</pre>}
      <button className="button secondary" disabled={!!configError} onClick={copy}>
        <Copy size={15} />
        Copy config
      </button>
      <span role="status" className="copy-status">
        {copied}
      </span>
      <h3>Verify the connection with your coding agent</h3>
      <p>After adding the config and restarting the client if required, ask it to call
        <code> discover_repositories</code>. A successful call proves protocol access to that server,
        not access to the same database shown in this browser. Confirm the exact tenant and commit below.</p>
      {handoff ? <section aria-label="Selected snapshot handoff">
        <p>Selected saved version: <code>{tenantGraph}</code> · <code>{sourceRevision}</code></p>
        <pre>{handoff}</pre>
        <button className="button secondary" onClick={async () => {
          try { await navigator.clipboard.writeText(handoff); setCopied("Copied selected snapshot handoff"); }
          catch { setCopied("Copy unavailable. Select the handoff text above."); }
        }}>Copy selected snapshot handoff</button>
      </section> : <p>Select a saved version with a known commit hash to prepare a guarded handoff.
        Discovery is still available; do not guess a commit or silently use the default repository.</p>}
      <h3>Available tools</h3>
      <p>All thirteen operation tools accept <code>expected_revision</code>.
        Include it together with the selected <code>tenant_graph</code> on every call.
        The generated configuration requires both arguments on every operation. Other servers without strict mode retain legacy unguarded behavior; a preflight does not bind future calls automatically.</p>
      <div className="tools-list">
        {tools.map(([name, args, note]) => (
          <article key={name}>
            <code>{name}</code>
            <p>{args}</p>
            <small>{note}</small>
          </article>
        ))}
      </div>
      <p className="disclaimer">
        Trusted local clients only. Policy override writes to the selected
        tenant graph. No authentication or production isolation is provided.
      </p>
    </dialog>
  );
}
