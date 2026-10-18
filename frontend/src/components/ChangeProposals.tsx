"use client";
import { useEffect, useRef, useState } from "react";
import { request } from "@/lib/api";
import { operatorRequest } from "@/lib/operator-api";
import { queryString } from "@/lib/workbench";
import { changedRegion, type ChangeImpact } from "@/lib/change-planning";
import OrganizationEvidence from "./OrganizationEvidence";
import { proposalStatusLabel, type OwnershipEvidence } from "@/lib/proposals";

type Execution = {
  id: string;
  provenance_kind: string;
  exit_code: number;
  output_excerpt: string;
  finding_id?: string;
};
type Proposal = {
  id: string;
  task_title: string;
  task_id?: string;
  plan_id?: string;
  pack_id?: string;
  agent_run_id?: string;
  overlay_digest?: string;
  declared_rationale?: string;
  status: string;
  proposal_hash: string;
  base_revision: string;
  proposed_files: Record<string, string | null>;
  base_file_shas: Record<string, string | null>;
  executions: Execution[];
  impact_summary: ChangeImpact & {
    active_rules: { id: string; rule: string }[];
    declared_ownership: OwnershipEvidence;
  };
};
type ProposalList = {
  proposals: Proposal[];
  truncated: boolean;
  limit: number;
};
const message = (error: unknown, fallback: string) =>
  error instanceof Error ? error.message : fallback;

export default function ChangeProposals({
  tenant,
  revision,
}: {
  tenant: string;
  revision: string | null;
}) {
  const [proposals, setProposals] = useState<Proposal[]>([]),
    [selected, setSelected] = useState("");
  const [listError, setListError] = useState(""),
    [actionError, setActionError] = useState(""),
    [diffError, setDiffError] = useState("");
  const [busy, setBusy] = useState(false),
    [reason, setReason] = useState(""),
    [runner, setRunner] = useState(false);
  const [ack, setAck] = useState(false),
    [tick, setTick] = useState(0),
    [loaded, setLoaded] = useState(false);
  const [loading, setLoading] = useState(false),
    [comparing, setComparing] = useState(false),
    [truncated, setTruncated] = useState(false);
  const [diffs, setDiffs] = useState<Record<string, string>>({}),
    [notice, setNotice] = useState("");
  const action = useRef<AbortController | null>(null),
    runKeys = useRef<Record<string, string>>({});
  // A list read started before a mutation must not overwrite its newer response.
  const mutationEpoch = useRef(0),
    busyRef = useRef(false);

  useEffect(() => {
    action.current?.abort();
    mutationEpoch.current++;
    busyRef.current = false;
    setBusy(false);
    setProposals([]);
    setSelected("");
    setLoaded(false);
    setRunner(false);
    setNotice("");
    setActionError("");
    setListError("");
    runKeys.current = {};
  }, [tenant, revision]);

  useEffect(() => {
    const c = new AbortController();
    let timer: ReturnType<typeof setTimeout> | undefined;
    if (!revision) return () => c.abort();
    const expectedRevision = revision;
    async function poll() {
      if (c.signal.aborted) return;
      if (busyRef.current) {
        timer = setTimeout(() => void poll(), 2500);
        return;
      }
      const epoch = mutationEpoch.current;
      setLoading(true);
      try {
        const data = await request<ProposalList>(
          `/proposals?${queryString({ tenant_graph: tenant, revision: expectedRevision })}`,
          c.signal,
        );
        if (!c.signal.aborted && epoch === mutationEpoch.current) {
          setProposals(data.proposals);
          setTruncated(data.truncated);
          setLoaded(true);
          setListError("");
          setSelected((id) =>
            data.proposals.some((row) => row.id === id) ? id : "",
          );
        }
        if (!c.signal.aborted) timer = setTimeout(() => void poll(), 2500);
      } catch (error) {
        if (!c.signal.aborted)
          setListError(
            message(error, "Proposal list unavailable") +
              ". Automatic refresh stopped; retry to check the current state.",
          );
      } finally {
        if (!c.signal.aborted) setLoading(false);
      }
    }
    void poll();
    void request<{ enabled: boolean }>(
      `/proposals/runner-capabilities?${queryString({ tenant_graph: tenant })}`,
      c.signal,
    )
      .then((result) => {
        if (!c.signal.aborted) setRunner(result.enabled);
      })
      .catch(() => {});
    return () => {
      c.abort();
      clearTimeout(timer);
    };
  }, [tenant, revision, tick]);
  useEffect(() => () => action.current?.abort(), []);

  const p = proposals.find((row) => row.id === selected);
  useEffect(() => {
    setReason("");
    setAck(false);
    setNotice("");
    setActionError("");
  }, [p?.id, tenant, revision]);
  useEffect(() => {
    const c = new AbortController();
    setDiffs({});
    setDiffError("");
    setComparing(false);
    if (p && revision) {
      setComparing(true);
      void Promise.all(
        Object.entries(p.proposed_files).map(async ([path, body]) => {
          let before = "";
          if (p.base_file_shas[path])
            before = (
              await request<{ source: string }>(
                `/repository/file-source?${queryString({ tenant_graph: tenant, expected_revision: revision, file_path: path })}`,
                c.signal,
              )
            ).source;
          return [path, changedRegion(before, body ?? "").text] as const;
        }),
      )
        .then((entries) => {
          if (!c.signal.aborted) setDiffs(Object.fromEntries(entries));
        })
        .catch((error) => {
          if (!c.signal.aborted)
            setDiffError(
              message(error, "Captured-source comparison unavailable"),
            );
        })
        .finally(() => {
          if (!c.signal.aborted) setComparing(false);
        });
    }
    return () => c.abort();
    // Proposal bodies are immutable; polling a new status must preserve review input.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p?.id, tenant, revision, tick]);

  function startAction() {
    action.current?.abort();
    const c = new AbortController();
    action.current = c;
    mutationEpoch.current++;
    busyRef.current = true;
    setBusy(true);
    setActionError("");
    setNotice("");
    return c;
  }
  function finishAction(c: AbortController) {
    if (!c.signal.aborted) {
      busyRef.current = false;
      setBusy(false);
    }
  }
  async function decide(approve: boolean) {
    if (!p || !revision) return;
    const c = startAction();
    try {
      const updated = await operatorRequest<Proposal>(
        `/proposals/${p.id}/decision`,
        {
          tenant_graph: tenant,
          expected_revision: revision,
          proposal_hash: p.proposal_hash,
          approve,
          reason,
        },
        c.signal,
      );
      if (!c.signal.aborted) {
        setProposals((rows) =>
          rows.map((row) => (row.id === updated.id ? updated : row)),
        );
        setNotice(
          approve
            ? "Exact proposal approved. Nothing has been applied."
            : "Proposal rejected.",
        );
      }
    } catch (error) {
      if (!c.signal.aborted) setActionError(message(error, "Decision failed"));
    } finally {
      finishAction(c);
    }
  }
  async function execute() {
    if (!p || !revision || !ack) return;
    const c = startAction();
    const key = runKeys.current[p.id] || crypto.randomUUID();
    runKeys.current[p.id] = key;
    try {
      const e = await operatorRequest<Execution>(
        `/proposals/${p.id}/execute-disposable-worktree`,
        {
          tenant_graph: tenant,
          expected_revision: revision,
          proposal_hash: p.proposal_hash,
          idempotency_key: key,
          acknowledge_code_execution: ack,
        },
        c.signal,
      );
      if (!c.signal.aborted) {
        setProposals((rows) =>
          rows.map((row) =>
            row.id === p.id
              ? {
                  ...row,
                  status:
                    e.exit_code === 0 ? "EXECUTED_VERIFIED" : "EXECUTED_FAILED",
                  executions: [
                    e,
                    ...row.executions.filter((old) => old.id !== e.id),
                  ],
                }
              : row,
          ),
        );
        setNotice(
          `Observed candidate pytest exit code: ${e.exit_code}. Saved repository unchanged.`,
        );
      }
    } catch (error) {
      if (!c.signal.aborted)
        setActionError(
          message(error, "Execution status unavailable") +
            ". Check the proposal record before retrying; closing this page does not cancel server execution.",
        );
    } finally {
      finishAction(c);
    }
  }
  const impact = p?.impact_summary,
    owners = impact?.declared_ownership;
  const comparisonReady =
    !!p &&
    !comparing &&
    !diffError &&
    Object.keys(diffs).length === Object.keys(p.proposed_files).length;
  return (
    <section
      className="cc-change-input"
      aria-label="Pending and recent change proposals"
    >
      <h2>Review your agent’s proposed changes.</h2>
      <p>
        Review what changes, who owns it, and which tests could help. Approval
        applies only to these exact contents.
      </p>
      <label htmlFor="proposal-select">Pending &amp; recent proposals</label>
      <select
        id="proposal-select"
        disabled={busy}
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
      >
        <option value="">Select a proposal ({proposals.length})</option>
        {proposals.map((row) => (
          <option key={row.id} value={row.id}>
            {row.task_title} · {proposalStatusLabel(row.status)}
          </option>
        ))}
      </select>
      {!revision && (
        <p>
          Select a saved version with an exact commit before reviewing
          proposals.
        </p>
      )}
      {loading && !loaded && <p role="status">Loading proposals…</p>}
      {loaded && !proposals.length && !listError && (
        <p>
          No proposals yet. Connect your coding agent, then ask it to submit a
          change for review.
        </p>
      )}
      {truncated && (
        <p className="cc-help">
          Showing the latest 50 proposals in this saved version.
        </p>
      )}
      {listError && (
        <p role="alert" className="cc-error">
          {listError} Any displayed proposals are the last successfully loaded
          state.
        </p>
      )}
      {actionError && (
        <p role="alert" className="cc-error">
          {actionError}
        </p>
      )}
      <button
        disabled={busy || !revision}
        onClick={() => setTick((n) => n + 1)}
      >
        Refresh proposals
      </button>
      {notice && <p role="status">{notice}</p>}
      {p && impact && (
        <>
          <h3>{p.task_title}</h3>
          {p.plan_id && <section className="wb-card" aria-label="Managed task evidence">
            <h4>Task and evidence binding</h4>
            <p>Task <code>{p.task_id}</code><br/>Plan <code>{p.plan_id}</code><br/>Run <code>{p.agent_run_id}</code><br/>Context pack <code>{p.pack_id}</code></p>
            <p>Initial worktree overlay digest: <code>{p.overlay_digest}</code>. Local plugin-reported identity; not a security attestation or proof the final checkout matches this proposal.</p>
            <p><strong>Agent-declared rationale</strong><br/>{p.declared_rationale || 'Not supplied; no hidden reasoning is inferred.'}</p>
            <p>Current plan, captured source and policy pins are rechecked. Inspect this task in Agent activity to see harness receipts and usage; actual tests for this exact proposal are listed below.</p>
          </section>}
          <p>
            Status: <strong>{p.status}</strong> —{" "}
            {proposalStatusLabel(p.status)}
          </p>
          <div className="cc-proposal-summary" aria-label="Proposal summary">
            <span>
              <strong>{Object.keys(p.proposed_files).length}</strong> changed
              files
            </span>
            <span>
              <strong>{impact.potentially_broken_callers.length}</strong>{" "}
              flagged callers
            </span>
            <span>
              <strong>{impact.impacted_test_files.length}</strong> candidate
              tests
            </span>
          </div>
          <details>
            <summary>Exact version &amp; approval evidence</summary>
            <p>
              Base commit <code>{p.base_revision}</code>
            </p>
            <p>
              Exact proposal hash <code>{p.proposal_hash}</code>
            </p>
            <p>
              The server rechecks captured file hashes and current rules before
              approval or execution.
            </p>
            <pre>{JSON.stringify(p.base_file_shas, null, 2)}</pre>
          </details>
          {diffError && (
            <p role="alert" className="cc-error">
              Cannot load the captured-source comparison: {diffError}. Approval
              is disabled until this is available. Refresh proposals to retry.
            </p>
          )}
          {Object.entries(p.proposed_files).map(([path, body]) => (
            <details key={path}>
              <summary>
                {path} ·{" "}
                {body === null
                  ? "Delete"
                  : p.base_file_shas[path] === null
                    ? "Add"
                    : "Replacement"}
              </summary>
              <pre>
                {diffs[path] ??
                  (diffError
                    ? "Comparison unavailable; retry before approval."
                    : "Loading captured-source comparison…")}
              </pre>
              <details>
                <summary>Complete proposed source</summary>
                <pre>{body ?? "(deleted)"}</pre>
              </details>
            </details>
          ))}
          <h3>What could be affected</h3>
          <p>
            {impact.impacted_files.length} candidate files ·{" "}
            {impact.impacted_test_files.length} candidate tests. Static
            candidates, not safe-skip proof.
          </p>
          <h4>Potentially broken callers</h4>
          <pre>
            {impact.potentially_broken_callers.join("\n") ||
              "No resolved callers flagged; not a compatibility guarantee."}
          </pre>
          <h4>Candidate pytest files</h4>
          <pre>
            {impact.recommended_pytest_command ||
              "No candidate command available"}
          </pre>
          <button
            disabled={!impact.recommended_pytest_command}
            onClick={() =>
              void navigator.clipboard
                .writeText(impact.recommended_pytest_command)
                .then(() => setNotice("Copied candidate test command."))
                .catch(() =>
                  setActionError(
                    "Clipboard unavailable; select and copy the command.",
                  ),
                )
            }
          >
            Copy candidate test command
          </button>
          <details>
            <summary>Added vs. removed dependencies</summary>
            <pre>
              {JSON.stringify(
                {
                  added: impact.added_dependencies,
                  removed: impact.removed_dependencies,
                },
                null,
                2,
              )}
            </pre>
          </details>
          <details>
            <summary>Applicable rules &amp; declared owners</summary>
            <h4>Current rules</h4>
            {impact.active_rules.length ? (
              <ul>
                {impact.active_rules.map((rule) => (
                  <li key={rule.id}>{rule.rule}</li>
                ))}
              </ul>
            ) : (
              <p>No active local rules were recorded for the changed files.</p>
            )}
            <OrganizationEvidence evidence={owners?.organizational_evidence} />
            <h4>Declared owners</h4>
            {owners?.declarations?.length ? (
              <ul>
                {owners.declarations.map((owner, i) => (
                  <li key={`${owner.file_path}:${owner.owner}:${i}`}>
                    <code>{owner.file_path}</code> —{" "}
                    <strong>{owner.owner || "No owner declared"}</strong>
                    <br />
                    <small>
                      {owner.pattern} ·{" "}
                      {owners.source_document?.path || "CODEOWNERS"}:
                      {owner.source_line}
                    </small>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No matching declared owners in this saved version.</p>
            )}
            {owners?.truncated && (
              <p>
                Additional matching declarations were omitted from this bounded
                preview.
              </p>
            )}
            <details>
              <summary>Raw rule and ownership evidence</summary>
              <pre>
                {JSON.stringify(
                  { rules: impact.active_rules, owners },
                  null,
                  2,
                )}
              </pre>
            </details>
          </details>
          {p.status === "PROPOSED" && (
            <>
              <label>
                Decision reason
                <input
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  maxLength={1000}
                />
              </label>
              <button
                className="cc-primary"
                disabled={
                  busy || !reason.trim() || !comparisonReady || !!listError
                }
                onClick={() => void decide(true)}
              >
                Approve exact proposal
              </button>
              <button
                disabled={busy || !reason.trim() || !!listError}
                onClick={() => void decide(false)}
              >
                Reject proposal
              </button>
            </>
          )}
          {p.status === "APPROVED" &&
            (runner ? (
              <>
                <label>
                  <input
                    type="checkbox"
                    checked={ack}
                    onChange={(e) => setAck(e.target.checked)}
                  />{" "}
                  Run trusted repository code on this machine. A disposable
                  worktree is not a security sandbox.
                </label>
                <button
                  disabled={busy || !ack || !!listError}
                  onClick={() => void execute()}
                >
                  Run candidate tests in disposable worktree
                </button>
              </>
            ) : (
              <p className="cc-help">
                Local test execution is not configured for this saved version.
                An operator must connect an allowlisted trusted Git checkout;
                public archive imports alone cannot run tests here.
              </p>
            ))}
          {p.executions.map((e) => (
            <article key={e.id}>
              <h4>
                {e.provenance_kind} · exit {e.exit_code}
              </h4>
              <pre>{e.output_excerpt}</pre>
              {e.finding_id && (
                <p>
                  Memory evidence: <code>{e.finding_id}</code>
                </p>
              )}
            </article>
          ))}
        </>
      )}
    </section>
  );
}
