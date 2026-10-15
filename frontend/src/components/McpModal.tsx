"use client";
import { useEffect, useRef, useState } from "react";
import { Copy, X } from "lucide-react";
const tools = [
  [
    "simulate_pr_blast_radius",
    "modified_files: string[], tenant_graph?, pr_number?, proposed_description?",
    "Audit a disposable clone with labeled dependency simulations.",
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
    "Rank only PR-linked authors/reviewers in this snapshot.",
  ],
  [
    "run_or_compile_playbook",
    "issue_description, tenant_graph?, execution_mode?",
    "Run deterministic triage or replay a current compiled path.",
  ],
];
export default function McpModal({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [cwd, setCwd] = useState("/absolute/path/to/ChronosGraph/backend");
  const [copied, setCopied] = useState("");
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
      <h3>Five exposed tools</h3>
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
