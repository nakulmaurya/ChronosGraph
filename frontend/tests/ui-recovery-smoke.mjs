/** Read-only browser regression checks. Import receipts/outages are injected.
 * No POST requests or real imports are issued by this test.
 */
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
const front = process.env.FRONTEND_URL || 'http://127.0.0.1:3003';
const out = process.env.EVIDENCE_DIR || '/tmp/chronos-ui-recovery';
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium', args: ['--no-sandbox'] });
const checks = [];
const errors = [];
const mark = name => { checks.push(name); console.log(`PASS ${name}`); };
try {
  for (const width of [1560, 390]) {
    const context = await browser.newContext({ viewport: { width, height: 1000 }, reducedMotion: 'reduce' });
    const page = await context.newPage();
    page.on('pageerror', e => errors.push(e.message));
    page.on('request', req => { if (req.method() === 'POST') errors.push(`Unexpected POST: ${req.url()}`); });
    await page.goto(front + '/');
    const chooser = page.getByRole('combobox', { name: 'Repository', exact: true });
    await chooser.selectOption('repo_falkordb_py');
    await page.locator('.cc-tree-file').filter({ hasText: 'falkordb' }).click();
    await page.locator('.cc-tree-file').filter({ hasText: 'query_result.py' }).click();
    await page.locator('.cc-inspector-heading h2').filter({ hasText: 'query_result.py' }).waitFor();
    await page.getByRole('button', { name: 'Functions', exact: true }).click();
    await page.getByLabel('Search files and symbols').fill('old repository query');
    await chooser.selectOption('repo_mcp_python_sdk');
    await page.waitForFunction(() => document.querySelector('.cc-segment button:last-child')?.disabled === true && document.querySelector('input[aria-label="Search files and symbols"]')?.value === '');
    const functions = page.getByRole('button', { name: 'Functions', exact: true });
    assert.equal(await functions.evaluate(e => e.classList.contains('active')), false);
    assert.equal(await functions.isDisabled(), true);
    assert.equal(await page.locator('.cc-inspector-heading').count(), 0);
    assert.equal(await page.getByLabel('Search files and symbols').inputValue(), '');
    mark(`Repository switch resets stale functions/source/query (${width}px)`);

    let failMap = true;
    await page.route('**/api/v1/repository/map?**', route => failMap
      ? route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Injected read outage' }) })
      : route.continue());
    await chooser.selectOption('repo_falkordb_py');
    await page.getByRole('heading', { name: 'Repository map unavailable.' }).waitFor();
    assert.equal(await page.getByRole('button', { name: 'Retry map', exact: true }).isEnabled(), true);
    assert.equal(await page.getByText('No indexed files here.', { exact: true }).count(), 0);
    await page.screenshot({ path: `${out}/map-recovery-${width}.png`, fullPage: true });
    failMap = false;
    await page.getByRole('button', { name: 'Retry map', exact: true }).click();
    await page.locator('.cc-canvas .react-flow__node').first().waitFor();
    assert.equal(await page.getByRole('heading', { name: 'Repository map unavailable.' }).count(), 0);
    mark(`Map outage recovers in place without false empty result (${width}px)`);
    await page.unroute('**/api/v1/repository/map?**');

    await page.route('**/api/v1/context/locate?**', async route => {
      await new Promise(resolve => setTimeout(resolve, 650));
      await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({entry_points:[{path:'stale-result.py',symbols:[]}]})}).catch(()=>{});
    });
    await page.getByLabel('Search files and symbols').fill('delayed');
    const delayed=page.waitForRequest(r=>r.url().includes('/context/locate?'));
    await page.getByRole('button',{name:'Run repository search'}).click(); await delayed;
    await page.getByLabel('Search files and symbols').fill('');
    await page.waitForTimeout(850);
    assert.equal(await page.getByText('stale-result.py',{exact:true}).count(),0);
    mark(`Clearing search aborts and suppresses a delayed response (${width}px)`);
    await page.unroute('**/api/v1/context/locate?**');
    await page.locator('.cc-tree-file').filter({hasText:'falkordb'}).click();
    await page.locator('.cc-tree-file').filter({hasText:'query_result.py'}).click();
    await page.locator('.cc-inspector-heading h2').filter({hasText:'query_result.py'}).waitFor();
    await page.route('**/api/v1/repository/file?**',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Injected inspector outage'})}));
    await page.locator('.cc-tree-file').filter({hasText:'graph.py'}).click();
    await page.getByRole('alert').filter({hasText:'Injected inspector outage'}).waitFor();
    assert.equal(await page.locator('.cc-inspector-heading').count(),0);
    mark(`Failed file inspection never leaves a previous file attributed to the new selection (${width}px)`);
    await page.unroute('**/api/v1/repository/file?**');
    // History is isolated read-only fixture data: commit B fails after commit A succeeds.
    const commits=[{sha:'a'.repeat(40),title:'Fixture commit A',author:'Fixture',timestamp:1},{sha:'b'.repeat(40),title:'Fixture commit B',author:'Fixture',timestamp:2}];
    await page.route('**/api/v1/repository/history?**',route=> {
      const b=new URL(route.request().url()).searchParams.get('commit')==='b'.repeat(40);
      return route.fulfill({status:b?503:200,contentType:'application/json',body:JSON.stringify(b?{detail:'Injected commit B outage'}:{commits,changes:[{path:'commit-a-only.py',additions:1,deletions:0}],changes_truncated:false})});
    });
    await page.getByRole('button',{name:'History',exact:true}).last().click();
    await page.getByRole('button').filter({hasText:'Fixture commit A'}).click();
    await page.getByText('commit-a-only.py',{exact:true}).waitFor();
    await page.getByRole('button').filter({hasText:'Fixture commit B'}).click();
    await page.getByRole('alert').filter({hasText:'Injected commit B outage'}).waitFor();
    assert.equal(await page.getByText('commit-a-only.py',{exact:true}).count(),0);
    assert.equal(await page.getByText('No indexed file links for this commit.',{exact:true}).count(),0);
    mark(`Commit read failure clears prior changes instead of presenting a false empty result (${width}px)`);
    await page.getByRole('button',{name:'All indexed commits',exact:true}).click();
    await page.getByRole('button').filter({hasText:'Fixture commit A'}).waitFor();
    await page.unroute('**/api/v1/repository/history?**');
    await page.getByRole('button',{name:'Repository',exact:true}).last().click();

    // The fake receipt exists once, then expires. No server mutation occurs.
    await page.evaluate(() => localStorage.setItem('chronosgraph-import-job', 'recovery-test-receipt'));
    let reads = 0;
    let recover = false;
    await page.route('**/api/v1/imports/recovery-test-receipt', route => {
      reads++;
      return route.fulfill({ status: reads === 1 || recover ? 200 : 404, contentType: 'application/json', body: JSON.stringify(reads === 1 || recover
        ? { id: 'recovery-test-receipt', status: 'RUNNING', stage: 'Checking fixture receipt', tenant_graph: 'repo_github_fixture', error: null, result: null }
        : { detail: 'Receipt expired or API restarted' }) });
    });
    const importButton = page.getByRole('button', { name: 'Import repository', exact: true }).first();
    await importButton.click();
    const modal = page.getByRole('dialog', { name: 'Bring a repository in.' });
    await modal.waitFor();
    await page.getByRole('heading', { name: 'Import status unavailable', exact: true }).waitFor();
    const stoppedAt = reads;
    await page.waitForTimeout(3200);
    assert.equal(reads, stoppedAt, 'Expired receipt must stop automatic polling');
    assert.equal(await modal.getByRole('button', { name: 'Importing repository…', exact: true }).count(), 0);
    assert.equal(await modal.getByRole('button', { name: 'Reload indexed repositories', exact: true }).isEnabled(), true);
    await page.screenshot({ path: `${out}/receipt-recovery-${width}.png`, fullPage: true });
    mark(`Expired receipt stops polling and exposes reconciliation (${width}px)`);
    recover = true;
    await modal.getByRole('button', { name: 'Check import status again', exact: true }).click();
    await modal.getByRole('button', { name: 'Importing repository…', exact: true }).waitFor();
    assert.equal(reads, stoppedAt + 1);
    await page.getByLabel('Close repository import').click();
    const closedAt = reads;
    await page.waitForTimeout(1700);
    assert.equal(reads, closedAt, 'Closing must stop receipt reads');
    assert.equal(await importButton.evaluate(e => document.activeElement === e), true);
    mark(`Receipt retry and close/focus restoration work (${width}px)`);

    // Restoration failure must also remain actionable, not silently lose tracking.
    recover = false;
    await importButton.click();
    await page.getByRole('heading', { name: 'Import status unavailable', exact: true }).waitFor();
    await modal.getByRole('button', { name: 'Dismiss tracking', exact: true }).click();
    assert.equal(await page.evaluate(() => localStorage.getItem('chronosgraph-import-job')), null);
    await modal.getByRole('textbox', { name: 'GitHub repository', exact: true }).waitFor({ state: 'visible' });
    assert.equal(await modal.getByRole('textbox', { name: 'GitHub repository', exact: true }).isEnabled(), true);
    await page.keyboard.press('Escape');
    await modal.waitFor({ state: 'hidden' });
    assert.equal(await importButton.evaluate(e => document.activeElement === e), true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    mark(`Lost saved receipt can be dismissed; keyboard dialog works (${width}px)`);
    await page.evaluate(() => localStorage.setItem('chronosgraph-import-job', 'recovery-test-receipt'));
    await importButton.click();
    await page.getByRole('heading', { name: 'Import status unavailable', exact: true }).waitFor();
    const catalogRefresh = page.waitForResponse(r => r.url().endsWith('/api/v1/tenants') && r.request().method() === 'GET');
    await modal.getByRole('button', { name: 'Reload indexed repositories', exact: true }).click();
    assert.equal((await catalogRefresh).status(), 200);
    await modal.waitFor({ state: 'hidden' });
    assert.equal(await chooser.inputValue(), 'repo_falkordb_py');
    mark(`Reconciliation reloads the catalog without importing again (${width}px)`);
    await context.close();
  }
  assert.deepEqual(errors, []);
  await writeFile(`${out}/results.json`, JSON.stringify({ checks, errors, mutation_requests: 0 }, null, 2));
} finally {
  await browser.close();
}
