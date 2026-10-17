/** Real inventory/link reads; injected lost-ack transport, never a real GitHub POST. */
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir,writeFile } from 'node:fs/promises';
const front=process.env.FRONTEND_URL||'http://127.0.0.1:3003';
const tenant=process.env.TENANT_GRAPH;
const out=process.env.EVIDENCE_DIR||'/tmp/chronos-bulk-ui';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const checks=[],errors=[];const mark=n=>{checks.push(n);console.log('PASS '+n);};
try {
 for(const width of [1560,390]) {
  const context=await browser.newContext({viewport:{width,height:1050},reducedMotion:'reduce'});
  await context.grantPermissions(['clipboard-read','clipboard-write']);
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(front+'/');
  await page.getByRole('combobox',{name:'Repository',exact:true}).selectOption(tenant);
  await page.locator('.cc-tree-file').filter({hasText:'README.md'}).click();
  await page.locator('.cc-inspector-heading').getByText('Markdown · inventory only',{exact:true}).waitFor();
  assert.equal(await page.getByRole('button',{name:'Plan a change to this file',exact:true}).isDisabled(),true);
  assert.equal(await page.getByRole('button',{name:'Functions',exact:true}).isDisabled(),true);
  mark(`Non-Python file is visible without claiming semantic analysis (${width}px)`);
  await page.getByRole('button',{name:'Copy workspace link',exact:true}).click();
  await page.getByRole('status').filter({hasText:'Workspace link copied'}).waitFor();
  const link=await page.evaluate(()=>navigator.clipboard.readText());
  assert.equal(new URL(link).searchParams.get('snapshot'),tenant);
  assert.equal(new URL(link).searchParams.get('file'),'README.md');
  assert.equal(new URL(link).searchParams.get('revision').length,40);
  await page.goto(link);
  await page.locator('.cc-inspector-heading').getByText('README.md',{exact:true}).first().waitFor();
  mark(`Exact saved-version link restores the selected file (${width}px)`);
  await page.getByLabel('Search files and symbols').fill('helper');
  await page.getByRole('button',{name:'Run repository search'}).click();
  await page.locator('.cc-search-results .cc-tree-file').filter({hasText:'src/pkg/a.py'}).waitFor();
  mark(`Developer search uses indexed files and definitions (${width}px)`);
  await page.screenshot({path:`${out}/inventory-${width}.png`,fullPage:true});
  await page.route('**/api/v1/imports/capabilities',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({enabled:true})}));
  let firstPayload=null,posts=0;
  await page.route('**/api/v1/imports',async route=>{
   if(route.request().method()!=='POST')return route.continue();
   const payload=route.request().postDataJSON();posts++;
   if(posts===1){firstPayload=payload;return route.abort('failed');}
   assert.deepEqual(payload,firstPayload);
   return route.fulfill({status:202,contentType:'application/json',body:JSON.stringify({id:payload.request_id,tenant_graph:tenant,status:'COMPLETE',stage:'Fixture transport reconciliation',result:{source_revision:'a'.repeat(40)},error:null})});
  });
  await page.route(/\/api\/v1\/imports\/[a-f0-9]{32}$/,route=>route.fulfill({status:404,contentType:'application/json',body:JSON.stringify({detail:'Injected missing acknowledgement'})}));
  await page.getByRole('button',{name:'Import repository',exact:true}).first().click();
  const modal=page.getByRole('dialog',{name:'Bring a repository in.'});
  await modal.getByLabel('GitHub repository',{exact:true}).fill('https://github.com/pallets/click');
  await modal.getByRole('button',{name:'Import repository',exact:true}).click();
  await modal.getByRole('button',{name:'Retry same saved import request',exact:true}).waitFor();
  const stored=await page.evaluate(()=>JSON.parse(localStorage.getItem('chronosgraph-import-request')));
  assert.deepEqual(stored,firstPayload);assert.match(stored.request_id,/^[a-f0-9]{32}$/);
  await page.reload();
  await page.getByRole('button',{name:'Import repository',exact:true}).first().click();
  await modal.getByRole('button',{name:'Retry same saved import request',exact:true}).click();
  await modal.waitFor({state:'hidden'});
  assert.equal(posts,2);
  assert.equal(await page.evaluate(()=>localStorage.getItem('chronosgraph-import-request')),null);
  mark(`Lost acknowledgement preserves exact request across reload and retries same ID (${width}px)`);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  mark(`Workspace fits without horizontal overflow (${width}px)`);
  await context.close();
 }
 assert.deepEqual(errors,[]);
} finally {await writeFile(out+'/checks.json',JSON.stringify({checks,errors},null,2));await browser.close();}
