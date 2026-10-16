"use client";
import { useEffect, useRef, useState } from "react";
import { Copy, X } from "lucide-react";
const tools = [
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
  ["recall_task_memory", "query?, tenant_graph?, include_stale?", "Recall findings and flag changed files or governing policies."]
];
export default function McpModal({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [cwd, setCwd] = useState("/absolute/path/to/ChronosGraph/backend");
  const [copied, setCopied] = useState("");
  const [platform, setPlatform] = useState("Claude Code");
  const skillPath = "skills/chronos-second-brain/SKILL.md";
  const config = JSON.stringify(
    {
      mcpServers: {
        chronosgraph: {
          command: "python",
          args: ["-m", "app.mcp_server.server"],
          cwd,
        },
      },
    },
    null,
    2,
  );
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
        Configuration template only. No IDE connection has been installed. Seed
        FalkorDB on localhost:6379 and install the backend first.
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
      <pre>{config}</pre>
      <button className="button secondary" onClick={copy}>
        <Copy size={15} />
        Copy config
      </button>
      <span role="status" className="copy-status">
        {copied}
      </span>
      <h3>Ten exposed tools · five core interfaces preserved</h3>
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
