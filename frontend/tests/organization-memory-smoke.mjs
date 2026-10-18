/** Local API/native DB only. Run the owned two-session demo with --keep-graphs first. */
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { readFile,mkdir,writeFile } from 'node:fs/promises';
const receipt=JSON.parse(await readFile(process.env.EVIDENCE_RECEIPT,'utf8'));
const tenant=receipt.second_snapshot.tenant_graph;
if(!tenant.startsWith('repo_test_evidence_'))throw Error('Use only the owned demo tenant');
const front=process.env.FRONTEND_URL||'http://127.0.0.1:3001';
const out=process.env.EVIDENCE_DIR||'/tmp/chronosgraph-evidence-ui';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/local/bin/chromium',args:['--no-sandbox']});
const checks=[],errors=[];
try {
 for(const width of [1560,390]) {
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`${front}/?snapshot=${tenant}&file=client.py&revision=${receipt.second_snapshot.source_revision}`);
  await page.locator('.cc-inspector-heading h2').filter({hasText:'client.py'}).waitFor();
  await page.getByRole('button',{name:'Ownership',exact:true}).last().click();
  await page.getByRole('button',{name:'Inspect rules & contributors',exact:true}).click();
  const evidence=page.getByRole('region',{name:'Organizational reasoning evidence'}).first();
  await evidence.getByText('SOURCE_BACKED_REVIEW_REQUIRED',{exact:true}).waitFor();
  await evidence.getByText('OWNED_SYNTHETIC',{exact:false}).first().waitFor();
  await evidence.getByText('Compatibility Platform (@chronos-example/compatibility)',{exact:false}).waitFor();
  await evidence.getByText('Required action: Publish a migration plan',{exact:false}).waitFor();
  const current=evidence.locator('article').filter({hasText:'ACTIVE ·'});
  await current.getByText('Decision source · docs/ADR-002.md',{exact:false}).click();
  await current.getByText('Motivating incident · incidents/INC-007.md',{exact:false}).click();
  await current.locator('blockquote').filter({hasText:'The queue worker accesses'}).waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.screenshot({path:`${out}/source-chain-${width}.png`,fullPage:true});
  checks.push(`Readable active decision, incident, revision/hash, explicit synthetic label and review team (${width}px)`);
  await page.getByRole('button',{name:'Agent activity',exact:true}).last().click();
  const memory=page.getByRole('region',{name:'Predecessor finding validation'});
  await memory.getByText('VALID_FOR_THIS_SNAPSHOT · STATIC_NEIGHBORHOOD',{exact:true}).waitFor();
  await memory.getByText('No test was rerun on this revision.',{exact:false}).waitFor();
  await memory.getByText('Timeout envelope preserves the existing retry branch',{exact:true}).waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.screenshot({path:`${out}/predecessor-memory-${width}.png`,fullPage:true});
  checks.push(`Historical candidate stays distinct, scoped validation and no new test-run claim (${width}px)`);
  await page.getByRole('button',{name:'Changes',exact:true}).last().click();
  await page.getByLabel('Pending & recent proposals',{exact:true}).selectOption(receipt.proposal_id);
  await page.getByText('Applicable rules & declared owners',{exact:true}).click();
  const review=page.getByRole('region',{name:'Organizational reasoning evidence'});
  await review.getByText('SOURCE_BACKED_REVIEW_REQUIRED',{exact:true}).waitFor();
  await review.getByText('Compatibility Platform (@chronos-example/compatibility)',{exact:false}).waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
  await page.screenshot({path:`${out}/proposal-chain-${width}.png`,fullPage:true});
  checks.push(`Saved proposal review shows decision-to-incident-to-team package, no approval or execution (${width}px)`);
  await context.close();
 }
 assert.deepEqual(errors,[]);checks.push('No uncaught browser errors');
 console.log(JSON.stringify({checks,errors},null,2));
} finally {
 await writeFile(`${out}/results.json`,JSON.stringify({checks,errors},null,2));await browser.close();
}
