/** Live REST/FalkorDB preview check. No network stubs or external model calls.
 * T09_TEST_TENANT must be a caller-owned disposable native Git/AST fixture.
 */
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
const FRONTEND = process.env.FRONTEND_URL || 'http://127.0.0.1:3004';
const API = process.env.TEST_API_URL || 'http://localhost:8004/api/v1';
const tenant = process.env.T09_TEST_TENANT;
if (!tenant?.startsWith('repo_test_')) throw new Error('Explicit disposable T09_TEST_TENANT required');
const output = process.env.EVIDENCE_DIR || '/tmp/t09-workbench-evidence';
await mkdir(output, {recursive:true});
const checks = [], errors = [];
const mark = name => {checks.push({check:name,status:'PASS'});console.log(`PASS ${name}`);};
const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',headless:true,args:['--no-sandbox']});
let page;
try {
  const context = await browser.newContext({viewport:{width:1560,height:1050},reducedMotion:'reduce'});
  page = await context.newPage();
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(FRONTEND+'/workbench');
  await page.getByLabel('Workbench repository').selectOption(tenant);
  await page.getByRole('heading',{name:'Repo map & search',exact:true}).waitFor();
  const snapshotEvidence=page.getByRole('region',{name:'Snapshot connection evidence',exact:true});
  await snapshotEvidence.getByText(/MATCHED AT CHECK/).waitFor();
  assert.match(await snapshotEvidence.innerText(),/Branch:/);
  assert.match(await snapshotEvidence.innerText(),/not live workspace monitoring/);
  await snapshotEvidence.getByText('Branch & freshness evidence',{exact:true}).click();
  assert.match(await snapshotEvidence.innerText(),/ALLOWLISTED_LOCAL_GIT/);
  assert.ok(await snapshotEvidence.locator('pre').evaluate(el => el.clientHeight <= 242),'Snapshot details must remain bounded');
  mark('Selected branch and timestamped CLI freshness are visible without claiming live sync');
  await page.screenshot({path:output+'/workbench-snapshot-desktop.png',fullPage:true});
  await snapshotEvidence.getByText('Branch & freshness evidence',{exact:true}).click();
  await page.getByLabel('Search repository').fill('helper');
  await page.getByRole('button',{name:'Locate context',exact:true}).click();
  await page.locator('.wb-symbol').first().waitFor();
  await page.getByRole('button',{name:'Read src/pkg/a.py:helper',exact:true}).click();
  await page.getByRole('heading',{name:'Focused symbol source',exact:true}).waitFor();
  assert.match(await page.locator('.wb-evidence').innerText(),/return 1/);
  mark('Native compact context and exact symbol source render');
  await page.screenshot({path:output+'/workbench-search-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'Diff & impact',exact:true}).click();
  await page.getByLabel('Input format').selectOption('bodies');
  await page.getByLabel('Path → final source text; null deletes', {exact:true}).fill(JSON.stringify({'src/pkg/b.py':'def run():\n    return 42\n'}));
  await page.getByRole('button',{name:'Preview replacement impact',exact:true}).click();
  await page.getByText(/Cleanup VERIFIED/).waitFor();
  const removed = page.getByText(/Removed dependencies \(/);
  assert.match(await removed.innerText(),/\(2\)/);
  await removed.click();
  assert.match(await page.locator('.wb-panel').first().innerText(),/IMPORTS/);
  mark('Full replacement preview removes native import and call edges; cleanup verified');
  await page.screenshot({path:output+'/workbench-diff-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'Rules & contributors',exact:true}).click();
  await page.getByLabel('Target file',{exact:true}).fill('src/pkg/a.py');
  await page.getByRole('button',{name:'Inspect rules & contributors',exact:true}).click();
  await page.getByRole('heading',{name:'ACTIVE local rules',exact:true}).waitFor();
  assert.match(await page.locator('.wb-panel').first().innerText(),/separate from declared CODEOWNERS/);
  mark('Native rule lineage and bounded contributors remain distinct from declared owners');
  await page.getByRole('button',{name:'Trace declared owners',exact:true}).click();
  const owners = page.getByRole('region',{name:'Declared owner evidence',exact:true});
  await owners.getByText('@fixture-reviewer',{exact:true}).waitFor();
  assert.match(await owners.innerText(),/CODEOWNERS:2/);
  await owners.getByText('Pinned CODEOWNERS source',{exact:true}).click();
  assert.match(await owners.innerText(),/sha256/);
  mark('Declared owner is traced through native graph rules to pinned source evidence');
  await page.screenshot({path:output+'/workbench-rules-desktop.png',fullPage:true});
  await page.getByRole('button',{name:'Activity & memory',exact:true}).click();
  await page.locator('.wb-card strong').filter({hasText:'locate_context'}).first().waitFor();
  assert.match(await page.locator('.wb-panel').first().innerText(),/Browser REST reads are not agent events/);
  mark('Real FastMCP protocol event is visible in a separate API/browser process');
  await page.getByText('Record a finding from the last context lookup',{exact:true}).click();
  await page.getByLabel('Finding summary',{exact:true}).fill('UI fixture helper evidence');
  await page.getByLabel('Verification evidence',{exact:true}).fill('Read the captured helper signature and body. No test command was executed.');
  await page.getByRole('button',{name:'Save source-bound finding',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Finding recorded'}).waitFor();
  await page.getByText('UI fixture helper evidence',{exact:true}).waitFor();
  mark('Browser saves and recalls explicitly agent-reported source-hash-bound findings');
  await page.screenshot({path:output+'/workbench-memory-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  for (const view of ['Repo map & search','Diff & impact','Rules & contributors','Activity & memory']) {
    await page.getByRole('button',{name:view,exact:true}).click();
    await page.waitForTimeout(150);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),true,`${view} overflows mobile`);
    await page.screenshot({path:output+'/workbench-'+view.split(' ')[0].toLowerCase()+'-mobile.png',fullPage:true});
  }
  mark('All four preview views fit 390px without horizontal page overflow');
  await page.getByRole('button',{name:'Diff & impact',exact:true}).click();
  await page.getByRole('heading',{name:'Diff & impact sandbox',exact:true}).waitFor();
  await page.screenshot({path:output+'/workbench-before-error-mobile.png',fullPage:true});
  assert.equal(await page.getByLabel('Input format',{exact:true}).inputValue(),'bodies','Diff input mode must survive view navigation');
  await page.getByLabel('Path → final source text; null deletes',{exact:true}).fill('{"../outside.py":"x=1"}');
  assert.equal(await page.getByText(/Cleanup VERIFIED/).count(),0,'Editing invalidates prior diff results');
  await page.getByRole('button',{name:'Preview replacement impact',exact:true}).click();
  await page.getByRole('alert').filter({hasText:'HTTP 422'}).waitFor();
  await page.screenshot({path:output+'/workbench-error-mobile.png',fullPage:true});
  mark('Unsafe replacement paths fail closed with an actionable browser error');
  const graphsBefore = await fetch(API+'/tenants').then(r=>r.json());
  const row = graphsBefore.find(r=>r.tenant_graph===tenant);
  assert.ok(row);
  assert.deepEqual(errors,[]);
  mark('No browser runtime errors');
  await writeFile(output+'/workbench-checks.json',JSON.stringify({checks,errors},null,2));
} catch (error) {
  if (page) {
    await page.screenshot({path:output+'/workbench-failure.png',fullPage:true});
    console.error((await page.locator('.wb-panel').first().innerText()).slice(0,1600));
  }
  throw error;
} finally {await browser.close();}
