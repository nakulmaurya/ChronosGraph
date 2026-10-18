/** Opt-in current-checkpoint read-only smoke. Real product gate NOT RUN by authoring this file. */
import assert from 'node:assert/strict';
import { chromium, expect } from '@playwright/test';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { validateConfig, installReadOnlyGuard, validateReadbacks } from './support/task-readonly.mjs';

assert.equal(process.argv[2], '--run', 'Opt in with --run CONFIG_JSON EVIDENCE_DIRECTORY, only after the measured window ends');
assert.ok(process.argv[3] && process.argv[4], 'Explicit configuration and new output directory required');
const verify = expect.configure({timeout:20000});
const c = validateConfig(JSON.parse(await readFile(process.argv[3], 'utf8')));
const out = resolve(process.argv[4]);
await mkdir(out, {recursive: false}); // Never overwrite evidence from an earlier attempt.
const result = {status: 'RUNNING', scope: 'Read-only current checkpoint; no task/proposal creation, approval, execution, override or model run',
  started_at: new Date().toISOString(), config: c, viewports: [], blocked_requests: [], errors: [], manual_screenshot_review: 'PENDING'};
let browser;
try {
  browser = await chromium.launch({executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox']});
  result.chromium_version = browser.version();
  for (const viewport of [{width:1560,height:1000}, {width:390,height:844}]) {
    const context = await browser.newContext({viewport, serviceWorkers: 'block'});
    const observed = {viewport, status:'STARTED', screenshots:[], page_errors:[], console_errors:[], request_failures:[], cancelled_requests:[]};
    result.viewports.push(observed);
    let page;
    try {
      await installReadOnlyGuard(context, [new URL(c.frontendURL).origin, new URL(c.apiURL).origin], result.blocked_requests);
      page = await context.newPage();
      page.setDefaultTimeout(20000);
      const failures = observed.request_failures, pageErrors = observed.page_errors;
      page.on('console', msg => {if (msg.type() === 'error') observed.console_errors.push(msg.text());});
      page.on('pageerror', e => pageErrors.push(e.message));
      page.on('requestfailed', req => {
        const row = {method:req.method(), path:new URL(req.url()).pathname, error:req.failure()?.errorText};
        (row.error === 'net::ERR_ABORTED' ? observed.cancelled_requests : failures).push(row);
      });
      page.on('response', response => {if (response.status() >= 400) failures.push({path: new URL(response.url()).pathname, status: response.status()});});
      // APIRequestContext is not covered by browser routing. Every call here is an explicit
      // loopback GET, has no redirects/retries and uses only prevalidated identifiers.
      async function get(path) {
        const response = await context.request.get(c.apiURL + path, {maxRedirects:0, maxRetries:0, timeout:15000});
        assert.equal(response.status(), 200, `GET ${path.split('?')[0]}`);
        return response.json();
      }
      async function readbacks() {
        const scoped = new URLSearchParams({tenant_graph:c.tenant, expected_revision:c.revision});
        return validateReadbacks(c, {
          identity: await get('/release/identity'),
          snapshot: await get(`/workspace/snapshot?${new URLSearchParams({tenant_graph:c.tenant})}`),
          task: await get(`/tasks/${c.taskId}?${scoped}`),
          proposals: await get(`/proposals?${new URLSearchParams({tenant_graph:c.tenant, revision:c.revision})}`),
        });
      }
      const before = await readbacks();
      observed.before = before;
      const target = new URL(c.frontendURL);
      target.searchParams.set('snapshot', c.tenant);
      target.searchParams.set('revision', c.revision);
      target.searchParams.set('view', '4');
      await page.goto(target.href, {waitUntil:'domcontentloaded'});
      await verify(page.getByRole('combobox', {name:'Repository', exact:true})).toHaveValue(c.tenant);
      const identity = page.getByLabel('Application and saved snapshot identity', {exact:true});
      await verify(identity).toContainText('Matched build declarations');
      await verify(identity.locator('code').nth(2)).toHaveAttribute('title', c.revision);
      assert.deepEqual(await identity.locator('code').evaluateAll(nodes => nodes.map(n => n.title)),
        [c.applicationCommit, c.applicationCommit, c.revision], 'full UI/API/snapshot declarations');
      const runtime = page.getByRole('region', {name:'Task runtime', exact:true});
      await verify(runtime).toBeVisible();
      await runtime.getByLabel('Resume task ID', {exact:true}).fill(c.taskId);
      await verify(runtime.getByText(c.planId, {exact:true})).toBeVisible();
      await runtime.getByText('Immutable plan v1 · current', {exact:true}).click();
      const handoffs = runtime.getByRole('region', {name:'Explicit worker handoffs', exact:true});
      await verify(handoffs).toBeVisible();
      for (const detail of await handoffs.locator('details').all()) await detail.locator('summary').click();
      await verify(handoffs).toContainText(c.workerAssignment);
      await verify(handoffs).toContainText(c.reviewerAssignment);
      await verify(handoffs).toContainText('verdict ACCEPTED');
      await verify(runtime.getByText('Agent idle; verification pending', {exact:true})).toHaveCount(2);
      for (const summary of await runtime.getByText('Raw harness status and identity', {exact:true}).all()) await summary.click();
      await verify(runtime).toContainText('IDLE_NOT_SUCCESS');
      await runtime.scrollIntoViewIfNeeded();
      const taskImage = `task-runtime-${viewport.width}.png`;
      await page.screenshot({path:`${out}/${taskImage}`, fullPage:true});
      observed.screenshots.push(taskImage);
      await page.getByRole('navigation', {name:'Command center views'}).getByRole('button', {name:'Changes', exact:true}).click();
      const proposal = page.getByRole('region', {name:'Pending and recent change proposals', exact:true});
      await proposal.getByLabel('Pending & recent proposals', {exact:true}).selectOption(c.proposalId);
      await verify(proposal.getByRole('region', {name:'Managed task evidence', exact:true})).toBeVisible();
      await verify(proposal).toContainText(c.candidateDigest);
      await verify(proposal.getByText('PROPOSED', {exact:true})).toBeVisible();
      await proposal.getByText('Exact version & approval evidence', {exact:true}).click();
      await verify(proposal).toContainText(c.proposalHash);
      await proposal.scrollIntoViewIfNeeded();
      const proposalImage = `pending-proposal-${viewport.width}.png`;
      await page.screenshot({path:`${out}/${proposalImage}`, fullPage:true});
      observed.screenshots.push(proposalImage);
      const overflow = await page.evaluate(() => ({width:innerWidth, scrollWidth:document.documentElement.scrollWidth}));
      assert.ok(overflow.scrollWidth <= overflow.width + 2, 'page-wide horizontal overflow');
      const after = await readbacks();
      observed.after = after;
      observed.overflow = overflow;
      assert.deepEqual(after, before, 'bound read-only metadata changed during observation');
      assert.deepEqual(result.blocked_requests, [], 'unexpected blocked request (not a clean read-only pass)');
      assert.deepEqual(pageErrors, [], 'browser page errors');
      assert.deepEqual(observed.console_errors, [], 'browser console errors');
      assert.deepEqual(failures, [], 'failed requests or HTTP errors');
      observed.status = 'AUTOMATED_PASS_MANUAL_REVIEW_PENDING';
    } catch (error) {
      observed.status = 'FAIL';
      observed.error = String(error.message);
      if (page && !page.isClosed()) {
        const name = `failure-${viewport.width}.png`;
        try {await page.screenshot({path:`${out}/${name}`,fullPage:true}); observed.screenshots.push(name);} catch {}
      }
      throw error;
    } finally {await context.close();}
  }
  result.status = 'AUTOMATED_PASS_MANUAL_REVIEW_PENDING';
} catch (error) {
  result.status = 'FAIL';
  result.errors.push(String(error.message));
  process.exitCode = 1;
} finally {
  if (browser) await browser.close();
  result.finished_at = new Date().toISOString();
  await writeFile(`${out}/results.json`, JSON.stringify(result,null,2)+'\n');
  const {readdir} = await import('node:fs/promises');
  const manifest = {};
  for (const name of (await readdir(out)).sort()) manifest[name] = createHash('sha256').update(await readFile(`${out}/${name}`)).digest('hex');
  await writeFile(`${out}/sha256-manifest.json`, JSON.stringify(manifest,null,2)+'\n');
  console.log(JSON.stringify({status:result.status, completed_viewports:result.viewports.filter(v=>v.status==='AUTOMATED_PASS_MANUAL_REVIEW_PENDING').length, blocked_requests:result.blocked_requests.length, evidence_directory:out}));
}
