"use client";
import { useEffect, useRef, useState } from 'react';
import { runStatusLabel, telemetryLabel, usageBasisLabel } from '@/lib/task-runtime';
import { API_BASE, request } from '@/lib/api';

type Run = { id: string; session_id: string; plan_id: string; pack_id: string; status: string; telemetry_status: string; missing_sequences: number[];
  usage_totals: Record<string, number>; usage_basis?:string;usage_integrity?:string;cost_reconciliation_mismatches?:string[]; harness_reported_cost: number | null;
  events: { sequence: number; kind: string; tool_name?: string; paths: string[]; observed_at_ms: number }[] };
type Assignment = { id:string; owner:string; role:string; status:string; version:number; claim_version:number; deliverable:string; allowed_paths:string[]; predecessor_id?:string; reports_json:string; path_boundary:string };
type Task = { assignments?:Assignment[]; task: { id: string; title: string; current_plan_id: string }; plans: { id: string; version: number; payload_json: string }[]; runs: Run[]; truncated: boolean };
export default function TaskRuntime({ tenant, revision, target }: { tenant: string; revision: string; target: string }) {
  const [title, setTitle] = useState('');
  const [acceptance, setAcceptance] = useState('');
  const [taskId, setTaskId] = useState('');
  const [detail, setDetail] = useState<Task | null>(null);
  const [pack, setPack] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [pathLimit, setPathLimit] = useState(100);
  const selection = useRef('');
  selection.current = `${tenant}:${revision}`;
  useEffect(() => { setTaskId(''); setDetail(null); setPack(null); setError(''); setBusy(false); }, [tenant, revision]);
  const scope = { tenant_graph: tenant, expected_revision: revision };
  useEffect(() => {
    if (!taskId || !revision) return;
    const ctrl = new AbortController(); let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const d = await request<Task>(`/tasks/${encodeURIComponent(taskId)}?${new URLSearchParams({ tenant_graph: tenant, expected_revision: revision })}`, ctrl.signal);
        if (!ctrl.signal.aborted) { setDetail(d); setError(''); }
      } catch (e) { if (!ctrl.signal.aborted) setError(e instanceof Error ? e.message : 'Task unavailable'); }
      if (!ctrl.signal.aborted) timer = setTimeout(poll, 3000);
    }
    void poll(); return () => { ctrl.abort(); clearTimeout(timer); };
  }, [tenant, revision, taskId]);
  async function post<T>(path: string, body: unknown): Promise<T> {
    const response = await fetch(`${API_BASE}/tasks${path}`, { method: 'POST', signal: AbortSignal.timeout(65000),
      headers: { 'Content-Type': 'application/json', 'X-ChronosGraph-Action': 'task-runtime' }, body: JSON.stringify(body) });
    const value = await response.json();
    if (!response.ok) throw Error(typeof value.detail === 'string' ? value.detail : JSON.stringify(value.detail));
    return value as T;
  }
  async function create() {
    const selected = selection.current; setBusy(true); setError('');
    try {
      const d = await post<Task>('', { ...scope, title, objective: title, target,
        acceptance: acceptance.split('\n').map(x => x.trim()).filter(Boolean), request_key: crypto.randomUUID() });
      if (selection.current !== selected) return;
      setTaskId(d.task.id); setDetail(d);
      const p = await post<Record<string, unknown>>(`/${d.task.id}/context-packs`, { ...scope, plan_id: d.task.current_plan_id, budget_equivalents: 2500, analysis_path_limit: pathLimit });
      if (selection.current === selected) setPack(p);
    } catch (e) { if (selection.current === selected) setError(e instanceof Error ? e.message : 'Task creation failed'); }
    finally { if (selection.current === selected) setBusy(false); }
  }
  return <section className="wb-card" aria-label="Task runtime">
    <h3>Task → plan → context → agent run</h3>
    <p>Local trusted-client integration for OpenCode 1.19.3. An idle agent is not a successful task. MCP-only activity remains separate below.</p>
    <label>Task objective<input value={title} onChange={e => setTitle(e.target.value)} maxLength={300}/></label>
    <label>Acceptance checks (one per line)<textarea value={acceptance} onChange={e => setAcceptance(e.target.value)} maxLength={4000}/></label>
    <p>Exact context target: <code>{target || 'Select a file first'}</code></p>
    <label>Analysis path limit (1–100)<input type="number" min={1} max={100} value={pathLimit} onChange={e => setPathLimit(Number(e.target.value))}/></label>
    <p>Lower limits explicitly narrow analyzed scope; omitted relationships remain unproven. Mandatory rules inside that scope are never silently dropped.</p>
    <button disabled={busy || !Number.isInteger(pathLimit) || pathLimit < 1 || pathLimit > 100 || !revision || !target || !title.trim() || !acceptance.trim()} onClick={() => void create()}>Create task and bounded context pack</button>
    {!revision && <p role="status">Loading snapshot identity before task operations…</p>}
    <label>Resume task ID<input disabled={!revision} value={taskId} onChange={e => { setTaskId(e.target.value); setDetail(null); setPack(null); }} placeholder="task_…"/></label>
    {error && <p role="alert" className="wb-error">{error}</p>}
    {detail && <>
      <h4>{detail.task.title}</h4><p>Task <code>{detail.task.id}</code><br/>Current plan <code>{detail.task.current_plan_id}</code></p>
      {detail.plans.map(p => <details key={p.id}><summary>Immutable plan v{p.version}{p.id === detail.task.current_plan_id ? ' · current' : ' · historical'}</summary><pre>{JSON.stringify(JSON.parse(p.payload_json), null, 2)}</pre></details>)}
      {!!detail.assignments?.length && <section aria-label="Explicit worker handoffs"><h4>Explicit worker handoffs</h4><p>One active assignment per task. Writing workers use separate owned worktrees. Path limits are advisory outside captured proposals; these records are not worker leases or approval.</p>{detail.assignments.map(a => <details key={a.id}><summary>{a.role.toLowerCase()} · {a.owner} · {a.status === 'CLAIMED' ? 'Working under current claim' : a.status === 'RETURNED' ? 'Candidate returned; review pending' : a.status === 'CORRECTION_REQUESTED' ? 'Correction requested' : a.status === 'CLOSED' ? 'Handoff closed; verification separate' : 'Awaiting claim'}</summary><p>{a.deliverable}</p><p>Allowed paths: {a.allowed_paths.join(', ')}</p><p>Claim version {a.claim_version}; record version {a.version}.</p><pre>{JSON.stringify({assignment:a.id, predecessor:a.predecessor_id, reports:JSON.parse(a.reports_json)},null,2)}</pre></details>)}</section>}
      {!detail.runs.length && <p>No bound harness run yet. Generating configuration is not proof of connection.</p>}
      {detail.runs.map(run => <article className="wb-card" key={run.id}>
        <strong>{runStatusLabel(run.status)}</strong><p>{telemetryLabel(run.telemetry_status)}</p><details><summary>Raw harness status and identity</summary><code>{run.status} · {run.telemetry_status}</code></details><p>Session <code>{run.session_id}</code><br/>Run <code>{run.id}</code><br/>Context <code>{run.pack_id}</code></p>
        {!!run.missing_sequences.length && <p role="alert">Missing sequence receipts: {run.missing_sequences.join(', ')}</p>}
        <details><summary>OpenCode-reported usage categories · not a billing total</summary><p>{usageBasisLabel(run.usage_basis)}. {run.usage_integrity}</p><pre>{JSON.stringify(run.usage_totals, null, 2)}</pre><p>Provider retry usage remains unknown. Message cumulative costs are reconciliation only, never added again.</p>{!!run.cost_reconciliation_mismatches?.length&&<p role="alert">Usage/cost reconciliation has unresolved messages.</p>}<p>Reported cost: {run.harness_reported_cost === null ? 'Unknown' : run.harness_reported_cost}. Cache/reasoning categories are not added again to a guessed total.</p></details>
        {run.events.slice(-30).map(e => <p key={e.sequence}>#{e.sequence} {e.kind} {e.tool_name || ''}{e.paths?.length ? ` · ${e.paths.join(', ')}` : ''}</p>)}
      </article>)}
    </>}
    {pack && <details><summary>Bounded context pack and setup identity</summary><pre>{JSON.stringify({ tenant_graph: tenant, expected_revision: revision, task_id: detail?.task.id, plan_id: detail?.task.current_plan_id, pack_id: pack.id }, null, 2)}</pre><p>{String(pack.serialized_bytes)} serialized bytes · {String(pack.estimated_token_equivalents)} estimated token equivalents, not billed tokens.</p><pre>{JSON.stringify(pack.manifest, null, 2)}</pre></details>}
  </section>;
}
