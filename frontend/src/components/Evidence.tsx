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
                (text(o.login).startsWith("git:") ? undefined : `https://github.com/${encodeURIComponent(text(o.login))}`)
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
          No PR/commit-file contributor link in the ingested snapshot. This does not mean
          the file has no maintainer.
        </p>
      )}
      <p className="disclaimer">
        Ranked from bounded PR/review or git-commit file links, not definitive ownership.
        Git authors are not verified GitHub maintainers.
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
          <Provenance value="SIMULATED_PR_DEPENDENCY" />
          <p className="subtle">
            Synthetic changes exist only in the disposable clone.
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
