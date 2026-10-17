import test from 'node:test';
import assert from 'node:assert/strict';
import { buildAgentConfig, buildSnapshotHandoff } from '../src/lib/agent-connection.ts';
const setup = { backendDirectory: '/home/user/Chronos Graph/backend', pythonExecutable: '/home/user/Chronos Graph/.venv/bin/python', databaseHost: '127.0.0.1', databasePort: '6379' };
test('agent config uses explicit executable, cwd and database without shell interpolation', () => {
  const config = JSON.parse(buildAgentConfig(setup)).mcpServers.chronosgraph;
  assert.equal(config.command, setup.pythonExecutable);
  assert.equal(config.cwd, setup.backendDirectory);
  assert.deepEqual(config.args, ['-m', 'app.mcp_server.server']);
  assert.deepEqual(config.env, { FALKORDB_HOST: '127.0.0.1', FALKORDB_PORT: '6379', CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD: '1' });
  assert.equal(config.shell, undefined);
});
for (const [key, value] of [['backendDirectory','relative/backend'], ['pythonExecutable','python -m evil'], ['databasePort','0'], ['databasePort','65536'], ['databasePort','6379; echo bad'], ['databaseHost','localhost\nX=1']]) {
  test(`invalid ${key} is refused: ${JSON.stringify(value)}`, () => assert.throws(() => buildAgentConfig({ ...setup, [key]:value })));
}
test('handoff binds both tenant and commit and refuses missing or malformed identity', () => {
  const revision = 'a'.repeat(40);
  const handoff = buildSnapshotHandoff('repo_selected', revision);
  assert.ok(handoff.includes(JSON.stringify({ tenant_graph:'repo_selected', expected_revision:revision })));
  assert.match(handoff, /every subsequent tool call/);
  assert.match(handoff, /not a live workspace/);
  for (const [tenant, rev] of [['',revision], ['repo_bad-name',revision], ['repo_selected',null], ['repo_selected','main'], ['repo_selected','A'.repeat(40)]]) assert.equal(buildSnapshotHandoff(tenant,rev),null);
  assert.notEqual(handoff, buildSnapshotHandoff('repo_other',revision));
  assert.notEqual(handoff, buildSnapshotHandoff('repo_selected','b'.repeat(40)));
});
