/** Read-only smoke-test contracts. No application endpoint or policy is changed. */
import assert from 'node:assert/strict';

export function validateConfig(value) {
  const c = structuredClone(value);
  for (const key of ['frontendURL', 'apiURL']) {
    const u = new URL(c[key]);
    assert.equal(u.protocol, 'http:', `${key}: trusted local HTTP only`);
    assert.ok(['127.0.0.1', 'localhost', '[::1]'].includes(u.hostname), `${key}: loopback only`);
    assert.ok(!u.username && !u.password && !u.search && !u.hash, `${key}: credentials/query/fragment forbidden`);
    c[key] = u.href.replace(/\/$/, '');
  }
  assert.equal(new URL(c.apiURL).pathname, '/api/v1', 'API base must end in /api/v1');
  for (const key of ['applicationCommit', 'revision']) assert.match(c[key] || '', /^[0-9a-f]{40}$/, key);
  for (const key of ['candidateDigest', 'proposalHash']) assert.match(c[key] || '', /^[0-9a-f]{64}$/, key);
  for (const [key, prefix] of Object.entries({tenant: 'repo_', taskId: 'task_', planId: 'plan_', packId: 'pack_',
    workerAssignment: 'assignment_', reviewerAssignment: 'assignment_', workerRun: 'run_', reviewerRun: 'run_', proposalId: 'prop_'})) {
    assert.ok(typeof c[key] === 'string' && c[key].startsWith(prefix) && /^[a-z0-9_]+$/.test(c[key]), key);
  }
  return c;
}

export function requestVerdict(method, url, origins) {
  const u = new URL(url);
  const kind = !['GET', 'HEAD', 'OPTIONS'].includes(method.toUpperCase()) ? 'mutation_method'
    : !origins.includes(u.origin) ? 'unexpected_origin' : null;
  return {allowed: kind === null, method: method.toUpperCase(), origin: u.origin, path: u.pathname, kind};
}

export async function installReadOnlyGuard(context, origins, blocked) {
  await context.route('**/*', async route => {
    const req = route.request();
    const verdict = requestVerdict(req.method(), req.url(), origins);
    if (!verdict.allowed) { blocked.push(verdict); await route.abort('blockedbyclient'); }
    else await route.continue();
  });
  await context.routeWebSocket('**/*', ws => {
    blocked.push({kind: 'websocket_disabled', path: new URL(ws.url()).pathname});
    ws.close();
  });
}

export function validateReadbacks(c, {identity, snapshot, task, proposals}) {
  assert.equal(identity.application_commit, c.applicationCommit, 'API application identity');
  assert.equal(snapshot.tenant_graph, c.tenant, 'selected tenant');
  assert.equal(snapshot.source_revision, c.revision, 'selected revision');
  assert.equal(task.task.id, c.taskId, 'task identity');
  assert.equal(task.task.current_plan_id, c.planId, 'current plan');
  assert.ok(task.plans.some(p => p.id === c.planId), 'immutable plan present');
  const assignments = [];
  for (const [id, role] of [[c.workerAssignment, 'WORKER'], [c.reviewerAssignment, 'REVIEWER']]) {
    const a = task.assignments.find(row => row.id === id);
    assert.ok(a, `${role} assignment missing`);
    assert.equal(a.role, role);
    assert.equal(a.status, 'RETURNED');
    assert.equal(a.task_id, c.taskId);
    assert.equal(a.plan_id, c.planId);
    assert.equal(a.pack_id, c.packId);
    assert.equal(a.expected_revision, c.revision);
    assert.equal(a.run_id, role === 'WORKER' ? c.workerRun : c.reviewerRun);
    if (role === 'REVIEWER') {
      assert.equal(a.predecessor_id, c.workerAssignment);
      const returns = JSON.parse(a.reports_json).filter(row => row.action === 'RETURN');
      assert.ok(returns.length, 'reviewer RETURN report');
      // Inspect the actual RETURN, never match acceptance instructions in a CLAIM.
      assert.match(returns.at(-1).report, /\bverdict ACCEPTED\b/);
    }
    assignments.push({id: a.id, role, status: a.status, claim_version: a.claim_version});
  }
  const runs = [c.workerRun, c.reviewerRun].map(id => {
    const run = task.runs.find(row => row.id === id);
    assert.ok(run, 'bound run missing');
    assert.equal(run.plan_id, c.planId);
    assert.equal(run.pack_id, c.packId);
    assert.equal(run.status, 'IDLE_NOT_SUCCESS');
    assert.deepEqual(run.missing_sequences, []);
    return {id, status: run.status, telemetry_status: run.telemetry_status,
      event_count: run.event_count, missing_sequences: run.missing_sequences};
  });
  const p = proposals.proposals.find(row => row.id === c.proposalId);
  assert.ok(p, 'expected proposal not found (including possible list truncation)');
  for (const [key, expected] of Object.entries({tenant_graph: c.tenant, base_revision: c.revision,
    task_id: c.taskId, plan_id: c.planId, pack_id: c.packId, agent_run_id: c.workerRun, assignment_id: c.workerAssignment, candidate_digest: c.candidateDigest,
    proposal_hash: c.proposalHash, status: 'PROPOSED'})) assert.equal(p[key], expected, `proposal ${key}`);
  assert.ok(Array.isArray(p.executions), 'execution records must be explicit');
  assert.equal(p.executions.length, 0, 'proposal must remain unexecuted');
  return {application_commit: identity.application_commit, revision: snapshot.source_revision,
    task_id: task.task.id, plan_id: task.task.current_plan_id, assignments, runs,
    proposal: {id: p.id, status: p.status, candidate_digest: p.candidate_digest,
      proposal_hash: p.proposal_hash, execution_count: p.executions.length},
    caveat: 'Observed local metadata and a declared review report; not human approval, test re-execution, build attestation or end-to-end task success.'};
}
