import { useState } from "react";
import { comparison } from "@/lib/comparison";
import { ExternalLink, ShieldCheck } from "lucide-react";
import { ms, safeUrl, text, timestamp } from "@/lib/api";
import type {
  Baseline,
  RecordData,
  Result,
  VisualNode,
  Investigation,
} from "@/lib/types";
export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}
export function Provenance({ value }: { value: unknown }) {
  return <Badge>{text(value)}</Badge>;
}
export function Metric({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
export function BaselineCard({ baseline }: { baseline: Baseline | undefined }) {
  return (
    <section className="baseline-card">
      <span className="eyebrow">CONTROLLED BASELINE</span>
      <h3>What a shallow query sees</h3>
      {baseline ? (
        <>
          <Provenance value={baseline.verdict} />
          <p>{baseline.mistake_summary}</p>
          <div className="metric-grid">
            <Metric label="Query / run time" value={ms(baseline.duration_ms)} />
            <Metric label="Tool actions" value={baseline.steps_taken} />
            <Metric
              label="Missed downstream"
              value={baseline.missed_downstream_count}
            />
          </div>
          {baseline.obsolete_rule_followed && (
            <blockquote>
              {baseline.obsolete_rule_followed}
              <small>Obsolete rule selected by the baseline</small>
            </blockquote>
          )}
        </>
      ) : (
        <p>
          Run a track to compare its measured baseline with connected evidence.
        </p>
      )}
      <p className="disclaimer">
        Controlled graph queries, not an LLM benchmark or proof of a production
        outage.
      </p>
    </section>
  );
}
function CopyPayload({ value, label }: { value: string; label: string }) {
  const [status, setStatus] = useState("");
  return (
    <div className="copy-payload">
      <pre>{value}</pre>
      <button type="button" className="button" onClick={async () => {
        try { await navigator.clipboard.writeText(value); setStatus("Copied"); }
        catch { setStatus("Clipboard unavailable — select and copy the text above"); }
      }}>{label}</button>
      <span role="status">{status}</span>
    </div>
  );
}
export function ComparisonStrip({ result, cold }: {
  result: Result | null; cold: Investigation | null;
}) {
  if (!result) return null;
  const values = comparison(result, cold);
  return (
    <section className="comparison-strip" aria-label="Shallow Baseline vs. ChronosGraph">
      <h3>⚡ Real-World Optimization &amp; Baseline Comparison</h3>
      <div className="comparison-pills">
        <p className="comparison-baseline">{values.left}</p>
        <p className="comparison-connected">{values.right}</p>
      </div>
      {result.kind === "audit" && (
        <div className="utility-card" data-testid="test-impact-plan">
          {result.data.context_window_savings?.measurement_status === "MEASURED_UTF8_BYTES" && <p>{result.data.context_window_savings.raw_repo_bytes} affected-source bytes → {result.data.context_window_savings.slice_bytes} compact audit bytes ({result.data.context_window_savings.context_saved_pct}% reduction; focused subset)</p>}
          <strong>Selective CI Test Runner: {result.data.impacted_test_files?.length ?? 0}/{result.data.total_repo_test_files ?? 0} test files</strong>
          <p>{result.data.test_suite_reduction_pct ?? 0}% outside static candidate selection. Not guaranteed safe to skip.</p>
          {!result.data.impacted_test_files?.length && <p>No reachable tests: full-suite fallback.</p>}
          <CopyPayload value={result.data.recommended_pytest_command || "pytest"} label="Copy pytest command" />
          <details>
            <summary>Selection limits and AST symbols</summary>
            <p>Three-hop evidence can miss dynamic imports, fixtures, plugins and runtime dependencies. Full-suite CI remains the safety gate.</p>
            <pre>{result.data.patch_symbols_analyzed?.join("\n") || "No submitted patch symbols."}</pre>
          </details>
        </div>
      )}
      {result.kind === "memory" && (
        <div className="utility-card" data-testid="context-compression">
          <strong>MCP Context Compression</strong>
          {result.data.context_measurement_status === "MEASURED_SOURCE_CHARS_DIV_4" ? <>
            <p>{result.data.raw_files_context_tokens} raw → {result.data.compiled_slice_context_tokens} slice token equivalents ({result.data.context_token_reduction_pct}% reduction)</p>
            <p>{result.data.raw_files_context_bytes} → {result.data.compiled_slice_context_bytes} UTF-8 bytes</p>
          </> : <p>Source baseline unavailable: enrich the snapshot, then rerun cold triage.</p>}
          <p>Unicode chars ÷ 4, rounded down. 0 external LLM calls.</p>
          <details>
            <summary>Measurement basis and limits</summary>
            <p>Deterministic MCP context-window compression: full candidate files vs. shortestPath AST+policy slice. Not tokenizer counts or billed savings.</p>
            <p>Counterfactual full-file payload, not source text read by the five graph tools. The focused slice omits bodies, imports and non-target files; it is not a semantics-preserving replacement. Negative reduction means the slice is larger.</p>
          </details>
          {!!result.data.compiled_context_slice_preview && <details>
            <summary>Actual compiled MCP context slice</summary>
            <CopyPayload value={result.data.compiled_context_slice_preview} label="Copy context slice" />
          </details>}
        </div>
      )}
    </section>
  );
}

function Link({ url }: { url: unknown }) {
  const href = safeUrl(url);
  return href ? (
    <a href={href} target="_blank" rel="noopener noreferrer">
      Source <ExternalLink size={12} />
    </a>
  ) : null;
}
export function Policy({
  policy,
  old = false,
}: {
  policy: RecordData;
  old?: boolean;
}) {
  return (
    <article className={`policy ${old ? "old" : "active"}`}>
      <div className="section-row">
        <Badge tone={old ? "rose" : "green"}>
          {old ? "SUPERSEDED" : "ACTIVE"}
        </Badge>
        <Link url={policy.source_url} />
      </div>
      <p className="rule">{text(policy.rule)}</p>
      <Provenance value={policy.source_type} />
      <details>
        <summary>Validity & provenance</summary>
        <dl>
          {[
            "scope_symbol",
            "rationale",
            "author_handle",
            "context_pr_url",
            "time_basis",
          ]
            .filter((k) => policy[k] != null)
            .map((k) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{text(policy[k])}</dd>
              </div>
            ))}
          {[
            "valid_from",
            "valid_to",
            "recorded_at",
            "recorded_from",
            "recorded_to",
          ]
            .filter((k) => policy[k] != null)
            .map((k) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{timestamp(policy[k])}</dd>
              </div>
            ))}
        </dl>
      </details>
    </article>
  );
}
export function Owners({ owners }: { owners: RecordData[] }) {
  return (
    <section className="inspector-section">
      <h3>Evidence-based reviewers</h3>
      {owners.length ? (
        owners.map((o, i) => (
          <article className="owner" key={`${text(o.login)}-${i}`}>
            <strong>{text(o.name || o.login)}</strong>
            <Link
              url={
                o.url ||
                (text(o.login).startsWith("git:")
                  ? undefined
                  : `https://github.com/${encodeURIComponent(text(o.login))}`)
              }
            />
            <dl>
              {Object.entries(o)
                .filter(([k]) => !["login", "url"].includes(k))
                .map(([k, v]) => (
                  <div key={k}>
                    <dt>{k.replaceAll("_", " ")}</dt>
                    <dd>{text(v)}</dd>
                  </div>
                ))}
            </dl>
          </article>
        ))
      ) : (
        <p className="empty-note">
          No PR/commit-file contributor link in the ingested snapshot. This does
          not mean the file has no maintainer.
        </p>
      )}
      <p className="disclaimer">
        Ranked from bounded PR/review or git-commit file links, not definitive
        ownership. Git authors are not verified GitHub maintainers.
      </p>
    </section>
  );
}
function StringList({ title, values }: { title: string; values: string[] }) {
  return (
    <details className="list-details">
      <summary>
        {title} <span>{values.length}</span>
      </summary>
      {values.length ? (
        <ul>
          {values.map((v) => (
            <li key={v}>{v}</li>
          ))}
        </ul>
      ) : (
        <p>No entries returned.</p>
      )}
    </details>
  );
}
export function ResultInspector({
  result,
  cold,
}: {
  result: Result | null;
  cold: Investigation | null;
}) {
  if (!result)
    return (
      <div className="inspector-section empty-inspector">
        <ShieldCheck size={26} />
        <h3>Evidence, not estimates.</h3>
        <p>
          Run an audit, compile a playbook, or inspect policy history. Results
          and source labels will appear here.
        </p>
        <div className="honesty-note">
          Native FalkorDB · local trusted-user demo · zero external models
        </div>
      </div>
    );
  if (result.kind === "audit") {
    const d = result.data;
    const patch = d.subgraph.nodes.find(
      (n) => n.metadata.patch_source_type === "AST_PATCH_SIMULATION",
    );
    return (
      <>
        <section className="inspector-section">
          <span className="eyebrow">DISPOSABLE SANDBOX</span>
          <h3>
            Impact audit <Badge tone="amber">{d.risk_level}</Badge>
          </h3>
          <div className="metric-grid">
            <Metric label="GRAPH.COPY" value={ms(d.sandbox_clone_time_ms)} />
            <Metric
              label="Cleanup"
              value={d.sandbox_cleaned_up ? "VERIFIED" : "FAILED"}
            />
          </div>
          <p className="disclaimer">
            Static potential impact, not code execution or an outage prediction.
          </p>
          <Provenance
            value={patch ? "AST_PATCH_SIMULATION" : "SIMULATED_PR_DEPENDENCY"}
          />
          {patch && (
            <p className="patch-summary">
              {text(patch.metadata.patch_resolved_calls)} resolved calls ·{" "}
              {text(patch.metadata.patch_unresolved_calls)} unresolved calls.
              Additive snippet overlay on {patch.title}.
            </p>
          )}
          <p className="subtle">
            Proposed dependencies exist only in the disposable clone.
          </p>
          <StringList title="Impacted files" values={d.impacted_files} />
          <StringList
            title="Impacted functions"
            values={d.impacted_functions}
          />
          {d.active_decisions_triggered.map((p, i) => (
            <Policy key={i} policy={p} />
          ))}
        </section>
        <Owners owners={d.recommended_reviewers} />
      </>
    );
  }
  if (result.kind === "brain") {
    const d = result.data;
    return (
      <>
        <section className="inspector-section" data-testid="repository-constraints"><h3>Repository-extracted constraints</h3>
          <p>Source-revision facts, separate from local ACTIVE/SUPERSEDED overrides.</p>
          {d.repository_constraints?.length ? d.repository_constraints.map((p,i) => <article className="policy" key={i}>
            <Provenance value={p.source_type} /><p>{text(p.rule)}</p>
            <p>{text(p.source_path)}:{text(p.source_line)} · {text(p.scope)}</p><Link url={p.source_url} />
          </article>) : <p>No concrete constraints extracted from this snapshot.</p>}
        </section>
        <section className="inspector-section">
          <span className="eyebrow">BI-TEMPORAL RULEBOOK</span>
          <h3>Current truth. Full history.</h3>
          <p className="mono break">{d.file_path || "No matching file"}</p>
          {d.active_decisions.length ? (
            d.active_decisions.map((p, i) => <Policy key={i} policy={p} />)
          ) : (
            <p>No active policy returned for this file.</p>
          )}
          {d.superseded_decisions.map((p, i) => (
            <Policy key={i} policy={p} old />
          ))}
        </section>
        <Owners owners={d.top_experts} />
      </>
    );
  }
  const d = result.data;
  const replay = d.execution_mode === "compiled_playbook";
  const reduction = cold
    ? (100 * (cold.total_steps_executed - d.total_steps_executed)) /
      cold.total_steps_executed
    : null;
  return (
    <section className="inspector-section">
      <span className="eyebrow">COMPILED PROCEDURAL MEMORY</span>
      <h3>
        {replay
          ? "The verified path, replayed."
          : "Explore once. Keep the proof."}
      </h3>
      <Provenance value="DETERMINISTIC_POLICY_TRIAGE" />
      <div className="step-comparison">
        <div>
          <strong>
            {cold?.total_steps_executed ?? d.total_steps_executed}
          </strong>
          <span>Cold actions</span>
        </div>
        <span>→</span>
        <div>
          <strong>
            {replay ? d.total_steps_executed : d.pruned_golden_steps}
          </strong>
          <span>{replay ? "Replayed" : "Compiled"} actions</span>
        </div>
      </div>
      {replay && reduction != null && (
        <Badge tone="cyan">{reduction.toFixed(0)}% fewer actions</Badge>
      )}
      <div className="metric-grid">
        <Metric label="This run" value={ms(d.duration_ms)} />
        <Metric
          label="Measured speedup"
          value={
            replay ? `${d.latency_speedup_factor.toFixed(3)}×` : "Cold baseline"
          }
        />
        {cold && <Metric label="Cold duration" value={ms(cold.duration_ms)} />}
        <Metric label="Model tokens" value={d.tokens_used} />
      </div>
      <p>{d.root_cause_summary}</p>
      <p className="disclaimer">
        token_savings_pct: {d.token_savings_pct} — zero-model sentinel, not
        measured token savings. Roles execute deterministic graph tools, not
        autonomous LLM agents.
      </p>
      <h3>Tool handoff log</h3>
      {d.agent_handoff_log.map((log, i) => (
        <details key={i} className="handoff">
          <summary>
            Action {i + 1} ·{" "}
            {text(
              log.agent_role ||
                log.agent ||
                log.tool_name ||
                log.tool ||
                "Graph tool",
            )}
          </summary>
          <pre>{JSON.stringify(log, null, 2)}</pre>
        </details>
      ))}
      <details>
        <summary>Investigation identifiers</summary>
        <pre>
          {JSON.stringify(
            {
              investigation_id: d.investigation_id,
              compiled_playbook_id: d.compiled_playbook_id,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </section>
  );
}
export function NodeInspector({
  node,
  onClose,
}: {
  node: VisualNode;
  onClose: () => void;
}) {
  return (
    <section className="inspector-section selection-inspector">
      <div className="section-row">
        <span className="eyebrow">SELECTED NODE</span>
        <button onClick={onClose} className="text-button">
          Clear selection
        </button>
      </div>
      <h3>{node.label}</h3>
      <p className="break">{node.title}</p>
      <Badge>{node.status}</Badge>
      {node.subtitle && <Provenance value={node.subtitle} />}
      <Link url={node.url} />
      <details open>
        <summary>Source metadata</summary>
        <pre>{JSON.stringify(node.metadata, null, 2)}</pre>
      </details>
    </section>
  );
}
