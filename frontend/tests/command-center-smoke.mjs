/** Real browser/API/FalkorDB workflow. Native fixture and optional public import.
 * Persona checks are sequential self-review perspectives, not independent users.
 */
import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir,writeFile} from 'node:fs/promises';
const front=process.env.FRONTEND_URL||'http://127.0.0.1:3004';
const api=process.env.TEST_API_URL||'http://localhost:8004/api/v1';
const tenant=process.env.T09_TEST_TENANT;
if(!tenant?.startsWith('repo_test_'))throw new Error('Own disposable fixture required');
const out=process.env.EVIDENCE_DIR||'/tmp/t09-command-center-ui';await mkdir(out,{recursive:true});
const checks=[],errors=[],created=[];
const mark=(persona,check)=>{checks.push({persona,check,status:'PASS'});console.log(`PASS [${persona}] ${check}`);};
const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
let page;
try{
 const context=await browser.newContext({viewport:{width:1560,height:1050},reducedMotion:'reduce'});page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 page.on('response',async response=>{if(response.request().method()==='POST'&&response.url()===api+'/imports'&&response.status()===202){const job=await response.json();created.push(job.tenant_graph);await writeFile(out+'/owned-imports.json',JSON.stringify(created));}});
 await page.goto(front+'/workbench');await page.getByRole('combobox',{name:'Repository',exact:true}).selectOption(tenant);
 await page.locator('.cc-stats>div').first().getByText('5',{exact:true}).waitFor();
 await page.getByRole('heading',{name:'Your codebase. Connected.'}).waitFor();
 await page.locator('.cc-canvas .react-flow__node').first().waitFor();
 assert.ok((await page.locator('.cc-canvas .react-flow__node').count())>=2);
 mark('vibe coder','Graph and simple navigation are visible before opening any technical details');
 await page.locator('.cc-tree-file').filter({hasText:'src'}).click();await page.locator('.cc-tree-file').filter({hasText:'pkg'}).click();
 await page.locator('.cc-tree-file').filter({hasText:'a.py'}).click();
 await page.locator('.cc-inspector-heading h2').filter({hasText:'a.py'}).waitFor();
 assert.match(await page.locator('.cc-inspector').innerText(),/src\/pkg\/b.py/);
 await page.getByRole('button',{name:'Functions',exact:true}).click();
 await page.locator('.cc-definition').filter({hasText:'helper'}).click();
 await page.locator('.cc-inspector pre').filter({hasText:'return 1'}).waitFor();
 mark('junior developer','Folder → file → function drill-down exposes exact captured source and importers');
 await page.screenshot({path:out+'/repository-desktop.png',fullPage:true});
 // Keyboard-accessible search supports a developer entering the project cold.
 await page.getByLabel('Search files and symbols').fill('helper');await page.getByLabel('Run repository search').click();await page.locator('.cc-tree-caption').waitFor();
 assert.match(await page.locator('.cc-tree-scroll').innerText(),/src\/pkg\/a.py/);
 mark('junior developer','Symbol search locates a real path without knowledge of tenant IDs or graph query syntax');
 await page.locator('.cc-tabs').getByRole('button',{name:'Changes',exact:true}).click();
 await page.getByLabel('Input format').selectOption('bodies');await page.getByLabel('Path → final source text; null deletes',{exact:true}).fill(JSON.stringify({'src/pkg/b.py':'def run():\n    return 42\n'}));
 await page.getByRole('button',{name:'Preview replacement impact',exact:true}).click();await page.getByText(/Cleanup VERIFIED/).waitFor();
 await page.getByText(/Removed dependencies \(2\)/).click();assert.match(await page.locator('.cc-tools').innerText(),/IMPORTS/);
 mark('senior developer','Replacement preview removes actual import/call relationships and verifies clone cleanup');
 await page.screenshot({path:out+'/changes-desktop.png',fullPage:true});
 await page.locator('.cc-tabs').getByRole('button',{name:'Repository',exact:true}).click();await page.locator('.cc-inspector-heading h2').waitFor();
 await page.locator('.cc-tabs').getByRole('button',{name:'Changes',exact:true}).click();assert.equal(await page.getByLabel('Input format').inputValue(),'bodies');assert.match(await page.getByLabel('Path → final source text; null deletes',{exact:true}).inputValue(),/return 42/);
 mark('senior developer','Draft change and result survive map navigation; no silent editor reset');
 await page.getByLabel('Path → final source text; null deletes',{exact:true}).fill('{"../outside.py":"x=1"}');
 await page.getByRole('button',{name:'Preview replacement impact',exact:true}).click();await page.getByRole('alert').filter({hasText:'HTTP 422'}).waitFor();assert.equal(await page.getByText(/Cleanup VERIFIED/).count(),0);
 mark('senior developer','Unsafe paths are rejected and stale successful impact results are invalidated');
 await page.locator('.cc-tabs').getByRole('button',{name:'History',exact:true}).click();await page.locator('.cc-commit').first().click();await page.locator('.cc-changed-file').first().waitFor();assert.match(await page.locator('.cc-history').innerText(),/not the historical commit/);
 mark('maintainer','Commit-linked file changes are navigable with historical-versus-indexed source clearly separated');
 await page.screenshot({path:out+'/history-desktop.png',fullPage:true});
 await page.locator('.cc-tabs').getByRole('button',{name:'Ownership',exact:true}).click();await page.getByLabel('Target file',{exact:true}).fill('src/pkg/a.py');await page.getByRole('button',{name:'Trace declared owners',exact:true}).click();await page.getByText('@fixture-reviewer',{exact:true}).waitFor();
 mark('maintainer','Declared CODEOWNERS remain separate from Git authors and current policy');
 await page.locator('.cc-tabs').getByRole('button',{name:'Agent activity',exact:true}).click();await page.locator('.wb-card strong').filter({hasText:'get_symbol_source'}).first().waitFor();await page.getByText('Workflow helper evidence',{exact:true}).waitFor();
 assert.match(await page.locator('.cc-tools').innerText(),/Browser REST reads are not agent events/);
 await page.getByRole('button',{name:'Inspect src/pkg/a.py →',exact:true}).first().click();await page.locator('.cc-inspector-heading h2').filter({hasText:'a.py'}).waitFor();
 mark('vibe coder','Actual separate stdio MCP tool activity and saved evidence are visible and link back to the file');
 for(const width of [390,768,1560]){
   await page.setViewportSize({width,height:width===390?844:1050});await page.waitForTimeout(350);
   for(const name of ['Repository','Changes','History','Ownership','Agent activity']){
     await page.locator('.cc-tabs').getByRole('button',{name,exact:true}).click();await page.waitForTimeout(150);
     assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`${name} page overflow at ${width}`);
   }
   await page.locator('.cc-tabs').getByRole('button',{name:'Repository',exact:true}).click();await page.waitForTimeout(450);
   const graph=page.locator('.cc-canvas');const nodes=graph.locator('.react-flow__node');let visible=0;const box=await graph.boundingBox();const flowBox=await graph.locator('.react-flow').boundingBox();assert.ok(flowBox&&flowBox.height>=350,`React Flow has no usable height at ${width}`);
   for(const n of await nodes.all()){const b=await n.boundingBox();if(b&&flowBox&&b.x+b.width>flowBox.x&&b.x<flowBox.x+flowBox.width&&b.y+b.height>flowBox.y&&b.y<flowBox.y+flowBox.height)visible++;}
   assert.ok(visible>0,`graph blank after resizing to ${width}`);
   await page.screenshot({path:out+`/repository-${width}.png`,fullPage:true});
 }
 mark('all four','All five views fit 390/768/1560px and the graph refits with visible nodes after resize');
 await page.getByLabel('Import repository',{exact:true}).click();const dialog=page.getByRole('dialog');await dialog.getByRole('heading',{name:'Bring a repository in.'}).waitFor();await dialog.getByLabel('GitHub repository',{exact:true}).fill('file:///tmp/nope');await dialog.getByRole('button',{name:'Import repository',exact:true}).click();await dialog.getByRole('alert').waitFor();
 mark('maintainer','Browser intake refuses unsafe URLs before launching a worker');
 await dialog.getByLabel('GitHub repository',{exact:true}).fill('https://github.com/pallets/click');
 if(process.env.RUN_PUBLIC_IMPORT==='1'){
   await dialog.getByRole('button',{name:'Import repository',exact:true}).click();await dialog.getByText(/Downloading and indexing/).waitFor();await page.screenshot({path:out+'/import-progress.png',fullPage:true});
   // Successful import automatically returns to the new repository; no CLI required.
   await page.getByRole('combobox',{name:'Repository',exact:true}).locator('option').filter({hasText:'pallets/click'}).last().waitFor({state:'attached',timeout:300000});
   await dialog.waitFor({state:'hidden',timeout:300000});assert.ok(created.includes(await page.getByRole('combobox',{name:'Repository',exact:true}).inputValue()));
   await page.getByLabel('Search files and symbols').fill('Command');await page.getByLabel('Run repository search').click();await page.locator('.cc-tree-file').filter({hasText:'src/click/core.py'}).first().waitFor();
   await page.locator('.cc-tree-file').filter({hasText:'src/click/core.py'}).first().click();await page.locator('.cc-inspector-heading h2').filter({hasText:'core.py'}).waitFor();
   mark('vibe coder','One-click real public GitHub import completes, auto-selects saved version, and locates Click Command source');
   await page.screenshot({path:out+'/public-click-imported.png',fullPage:true});
   await page.locator('.cc-tabs').getByRole('button',{name:'History',exact:true}).click();await page.getByText('No commit history in this saved version.',{exact:true}).waitFor();
   mark('maintainer','Public archive view does not fabricate unavailable commit history');
 }else{await page.getByLabel('Close repository import').click();}
 const denied=await fetch(api+'/imports',{method:'POST',headers:{'Content-Type':'application/json','Origin':'https://evil.example','X-ChronosGraph-Action':'public-import'},body:JSON.stringify({url:'https://github.com/pallets/click'})});assert.equal(denied.status,403);
 mark('maintainer','Cross-origin job creation is refused');
 assert.deepEqual(errors,[]);mark('all four','No browser runtime errors');
}finally{await writeFile(out+'/checks.json',JSON.stringify({checks,errors,owned_imports:created,review_kind:'SEQUENTIAL_SELF_REVIEW_NOT_INDEPENDENT_USERS'},null,2));if(page)await page.screenshot({path:out+'/last-state.png',fullPage:true}).catch(()=>{});await browser.close();}
