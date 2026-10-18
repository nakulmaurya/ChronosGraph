"use client";
import { useEffect, useRef, useState } from 'react';
import { API_BASE, request } from '@/lib/api';

type Run = { id: string; session_id: string; plan_id: string; pack_id: string; status: string; telemetry_status: string; missing_sequences: number[];
  usage_totals: Record<string, number>; harness_reported_cost: number | null;
  events: { sequence: number; kind: string; tool_name?: string; paths: string[]; observed_at_ms: number }[] };
type Task = { task: { id: string; title: string; current_plan_id: string }; plans: { id: string; version: number; payload_json: string }[]; runs: Run[]; truncated: boolean };
export default function TaskRuntime({ tenant, revision, target }: { tenant: string; revision: string; target: string }) {
  const [title, setTitle] = useState('');
  const [acceptance, setAcceptance] = useState('');
  const [taskId, setTaskId] = useState('');
  const [detail, setDetail] = useState<Task | null>(null);
  const [pack, setPack] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
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
      const p = await post<Record<string, unknown>>(`/${d.task.id}/context-packs`, { ...scope, plan_id: d.task.current_plan_id, budget_equivalents: 2500 });
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
    <button disabled={busy || !revision || !target || !title.trim() || !acceptance.trim()} onClick={() => void create()}>Create task and bounded context pack</button>
    {!revision && <p role="status">Loading snapshot identity before task operations…</p>}
    <label>Resume task ID<input disabled={!revision} value={taskId} onChange={e => { setTaskId(e.target.value); setDetail(null); setPack(null); }} placeholder="task_…"/></label>
    {error && <p role="alert" className="wb-error">{error}</p>}
    {detail && <>
      <h4>{detail.task.title}</h4><p>Task <code>{detail.task.id}</code><br/>Current plan <code>{detail.task.current_plan_id}</code></p>
      {detail.plans.map(p => <details key={p.id}><summary>Immutable plan v{p.version}{p.id === detail.task.current_plan_id ? ' · current' : ' · historical'}</summary><pre>{JSON.stringify(JSON.parse(p.payload_json), null, 2)}</pre></details>)}
      {!detail.runs.length && <p>No bound harness run yet. Generating configuration is not proof of connection.</p>}
      {detail.runs.map(run => <article className="wb-card" key={run.id}>
        <strong>{run.status}</strong><p>{run.telemetry_status}</p><p>Session <code>{run.session_id}</code><br/>Run <code>{run.id}</code><br/>Context <code>{run.pack_id}</code></p>
        {!!run.missing_sequences.length && <p role="alert">Missing sequence receipts: {run.missing_sequences.join(', ')}</p>}
        <details><summary>OpenCode-reported usage categories · not a billing total</summary><pre>{JSON.stringify(run.usage_totals, null, 2)}</pre><p>Reported cost: {run.harness_reported_cost === null ? 'Unknown' : run.harness_reported_cost}. Cache/reasoning categories are not added again to a guessed total.</p></details>
        {run.events.slice(-30).map(e => <p key={e.sequence}>#{e.sequence} {e.kind} {e.tool_name || ''}{e.paths?.length ? ` · ${e.paths.join(', ')}` : ''}</p>)}
      </article>)}
    </>}
    {pack && <details><summary>Bounded context pack and setup identity</summary><pre>{JSON.stringify({ tenant_graph: tenant, expected_revision: revision, task_id: detail?.task.id, plan_id: detail?.task.current_plan_id, pack_id: pack.id }, null, 2)}</pre><p>{String(pack.serialized_bytes)} serialized bytes · {String(pack.estimated_token_equivalents)} estimated token equivalents, not billed tokens.</p><pre>{JSON.stringify(pack.manifest, null, 2)}</pre></details>}
  </section>;
}
