/** Lifecycle + read-only recovery/setup + legacy demo, on one owned DB.
 * Proposal failure-injection MUST run on a separate fresh fixture: it approves. */
import { spawnSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
const root = process.env.EVIDENCE_DIR;
if (!root || !process.env.HERO_FIXTURE) throw new Error('Owned fixture/evidence required');
const suites = ['final-lifecycle-smoke.mjs', 'ui-recovery-smoke.mjs', 'agent-setup-smoke.mjs', 'live-smoke.mjs'];
const results = [];
for (const suite of suites) {
  const out = path.join(root, suite.replace('.mjs', ''));
  await mkdir(out, { recursive: true });
  const result = spawnSync(process.execPath, [path.join('tests', suite)], {
    env: { ...process.env, EVIDENCE_DIR: out }, encoding: 'utf8', timeout: 240000,
  });
  await writeFile(path.join(out, 'run.log'), (result.stdout || '') + (result.stderr || ''));
  results.push({ suite, exit_code: result.status, error: result.error?.message || null });
  console.log(suite, result.status);
  if (result.status !== 0) {
    await writeFile(path.join(root, 'suite-results.json'), JSON.stringify(results, null, 2));
    throw new Error(`${suite} failed; inspect its run.log`);
  }
}
await writeFile(path.join(root, 'suite-results.json'), JSON.stringify(results, null, 2));
