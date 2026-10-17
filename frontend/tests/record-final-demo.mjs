/** Reproducible 200-second real UI recording on an owned native fixture. */
import {chromium} from '@playwright/test';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const fixture=JSON.parse(await readFile(process.env.HERO_FIXTURE,'utf8')),out=process.env.EVIDENCE_DIR;
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const videoStart=Date.now();
const ctx=await browser.newContext({viewport:{width:1560,height:1000},reducedMotion:'reduce',recordVideo:{dir:out+'/video',size:{width:1560,height:1000}}});
const page=await ctx.newPage();page.setDefaultTimeout(15000);const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:3003');await page.getByRole('combobox',{name:'Repository',exact:true}).selectOption(fixture.tenant);
await page.locator('.cc-overview h1').waitFor();const start=Date.now(),chapters=[];
async function chapter(title,fn){const i=chapters.length;chapters.push({title,start:(Date.now()-start)/1000});await fn();await page.screenshot({path:`${out}/chapter-${i}.png`});await page.waitForTimeout(Math.max(0,(i+1)*25000-(Date.now()-start)));}
const tab=name=>page.getByRole('button',{name,exact:true}).last().click();
const region=page.getByRole('region',{name:'Pending and recent change proposals'});
try{
 await chapter('Connected code, not isolated files',async()=>{
   await page.getByRole('button',{name:'Table',exact:true}).click();await page.getByRole('table').getByRole('button',{name:'core/',exact:true}).click();await page.getByRole('table').getByRole('button',{name:'core/pricing.py',exact:true}).click();await page.getByRole('button',{name:'Graph',exact:true}).click();await page.getByRole('button',{name:'Functions',exact:true}).click();await page.waitForTimeout(1000);await page.locator('.cc-definition').filter({hasText:'calculate_discount'}).click();
 });
 await chapter('Catch the incomplete change',async()=>{
   await tab('Changes');await region.getByRole('combobox').selectOption(fixture.broken);await region.getByText('services/checkout.py:checkout',{exact:true}).waitFor();await region.locator('summary').filter({hasText:'core/pricing.py · Replacement'}).click();await region.getByRole('heading',{name:'What could be affected',exact:true}).scrollIntoViewIfNeeded();
 });
 await chapter('Approve exact contents',async()=>{
   await region.getByRole('combobox').selectOption(fixture.fixed);await region.locator('summary').filter({hasText:'core/pricing.py · Replacement'}).click();await region.locator('summary').filter({hasText:'Applicable rules & declared owners'}).click();await region.getByLabel('Decision reason').fill('Reviewed exact coordinated bodies, owners, rules, and candidate order test');await region.getByRole('button',{name:'Approve exact proposal',exact:true}).click();await region.getByText('Exact proposal approved. Nothing has been applied.',{exact:true}).waitFor();await region.locator('summary').filter({hasText:'Applicable rules & declared owners'}).click();await region.getByRole('heading',{name:'What could be affected',exact:true}).scrollIntoViewIfNeeded();
 });
 await chapter('Observe the real test',async()=>{
   await region.getByRole('checkbox').check();await region.getByRole('button',{name:'Run candidate tests in disposable worktree',exact:true}).click();await region.getByRole('heading',{name:'LOCAL_WORKTREE_OBSERVED · exit 0',exact:true}).waitFor();await region.locator('article').filter({hasText:'LOCAL_WORKTREE_OBSERVED · exit 0'}).evaluate(el=>el.scrollIntoView({block:'center'}));
 });
 await chapter('Remember the useful path',async()=>{
   await tab('Agent activity');await page.getByText('CURRENT_AT_INDEXED_SNAPSHOT',{exact:false}).waitFor();await page.getByText('Why this context was selected',{exact:true}).first().click();await page.getByRole('button',{name:'Run policy investigation',exact:true}).click();await page.getByRole('button',{name:'Replay verified path',exact:true}).click();await page.getByText('5 cold actions → 3 actions this run',{exact:false}).waitFor();await page.getByRole('heading',{name:'Remember the useful path.',exact:true}).scrollIntoViewIfNeeded();
 });
 await chapter('Keep decisions portable',async()=>{
   await page.getByRole('button',{name:'Prepare recovery note',exact:true}).click();await page.getByRole('button',{name:'Copy ResumeSnapshot.md',exact:true}).waitFor();await tab('Ownership');await page.getByRole('button',{name:'Inspect rules & contributors',exact:true}).click();await page.getByRole('button',{name:'Trace declared owners',exact:true}).click();await page.getByText('@platform-team',{exact:true}).waitFor();await page.getByRole('button',{name:'Preview [[Wikilink]] note',exact:true}).click();const wait=page.waitForEvent('download');await page.getByRole('button',{name:'Download Obsidian vault (.zip)',exact:true}).click();await(await wait).saveAs(out+'/demo-obsidian.zip');await page.getByRole('heading',{name:'Declared CODEOWNERS',exact:true}).scrollIntoViewIfNeeded();
 });
 await chapter('Invalidate stale confidence',async()=>{
   await page.getByLabel('New rule',{exact:true}).fill('DEMO: finance review now required for discount contract changes');await page.getByLabel('Why this replaces the old decision',{exact:true}).fill('A new architecture decision invalidates the old approval and finding');await page.getByRole('checkbox',{name:'Confirm this file-wide local policy change.',exact:true}).check();await page.getByRole('button',{name:'Record policy override',exact:true}).click();await page.getByText('Policy recorded. Dependent evidence must be rechecked.',{exact:true}).waitFor();await tab('Agent activity');await page.getByText('STALE ·',{exact:false}).waitFor();await page.getByText('Candidate test result: Coordinate pricing and checkout rename',{exact:true}).scrollIntoViewIfNeeded();
 });
 await chapter('A graph-native developer workflow',async()=>{
   for(const tenant of ['repo_falkordb_py',fixture.click_tenant,'repo_mcp_python_sdk'].filter(Boolean)){
     await page.getByRole('combobox',{name:'Repository',exact:true}).selectOption(tenant);await page.locator('.cc-overview h1').waitFor();await page.locator('.react-flow__node').first().waitFor();await page.waitForTimeout(4500);
   }
 });
 assert.deepEqual(errors,[]);await writeFile(out+'/recording.json',JSON.stringify({chapters,lead_in_seconds:(start-videoStart)/1000,seconds:(Date.now()-start)/1000,errors,provenance:'Recorded real UI actions; scripted real MCP proposals; trusted owned pytest; not a hosted model agent'},null,2));
}finally{await ctx.close();await browser.close();}
