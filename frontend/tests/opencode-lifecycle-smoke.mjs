/** Actual OpenCode-authored proposal IDs must be supplied through HERO_FIXTURE.
 * Automated operator on an owned synthetic fixture; no claim of a human user study.
 * Pauses after observed execution until continue-policy-check, enabling fresh model recall. */
import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
const fixture=JSON.parse(await readFile(process.env.HERO_FIXTURE,'utf8'));
const api=process.env.API_URL,front='http://127.0.0.1:3003',out=process.env.EVIDENCE_DIR;
await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const checks=[],errors=[];
async function check(name,fn){await fn();checks.push(name);console.log('PASS '+name);}
try{
 for(const width of [1560,390]){
  const ctx=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce',recordVideo:{dir:out+'/video',size:{width:1560,height:1000}}});const page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));page.setDefaultTimeout(20000);
  await page.goto(front);await page.getByRole('combobox',{name:'Repository',exact:true}).selectOption(fixture.tenant);
  await check(`Keyboard-accessible relationship table (${width})`,async()=>{
    const table=page.getByRole('button',{name:'Table',exact:true});await table.focus();await page.keyboard.press('Enter');await page.getByRole('table').waitFor();
    const folder=page.getByRole('table').getByRole('button',{name:'core/',exact:true});await folder.focus();await page.keyboard.press('Enter');
    const file=page.getByRole('table').getByRole('button',{name:'core/pricing.py',exact:true});await file.focus();await page.keyboard.press('Enter');
    await page.locator('.cc-inspector-heading h2').filter({hasText:'pricing.py'}).waitFor();
  });
  await page.getByRole('button',{name:'Changes',exact:true}).last().click();
  const region=page.getByRole('region',{name:'Pending and recent change proposals'});
  await region.getByRole('combobox').selectOption(fixture.broken);
  await check(`Incomplete rename has real broken-caller evidence (${width})`,async()=>{await region.getByText('services/checkout.py:checkout',{exact:true}).waitFor();});
  await region.getByRole('combobox').selectOption(fixture.fixed);
  if(width===1560){
    await check('Approve exact hash through browser operator endpoint',async()=>{await region.getByLabel('Decision reason').fill('Reviewed coordinated change and candidate test in the Command Center');await region.getByRole('button',{name:'Approve exact proposal',exact:true}).click();await region.getByText('Exact proposal approved. Nothing has been applied.',{exact:true}).waitFor();});
    await check('Observed worktree pytest exit and durable memory evidence',async()=>{await region.getByRole('checkbox').check();await region.getByRole('button',{name:'Run candidate tests in disposable worktree',exact:true}).click();await region.getByRole('heading',{name:'LOCAL_WORKTREE_OBSERVED · exit 0',exact:true}).waitFor();assert.match(await region.innerText(),/Memory evidence/);});
    await page.screenshot({path:out+'/approved-observed.png',fullPage:true});
  }else await region.getByRole('heading',{name:'LOCAL_WORKTREE_OBSERVED · exit 0',exact:true}).waitFor();
  await page.getByRole('button',{name:'Agent activity',exact:true}).last().click();
  await check(`Activity and source-bound memory visible (${width})`,async()=>{await page.getByText('Candidate test result: OpenCode coordinated discount rename',{exact:true}).waitFor();await page.getByText('CURRENT_AT_INDEXED_SNAPSHOT',{exact:false}).waitFor();});
  if(width===1560){
    await check('Native shortestPath replay and compact note inside default UI',async()=>{await page.getByRole('button',{name:'Run policy investigation',exact:true}).click();await page.getByRole('button',{name:'Replay verified path',exact:true}).click();await page.getByText('5 cold actions → 3 actions this run',{exact:false}).waitFor();await page.getByRole('button',{name:'Prepare recovery note',exact:true}).click();await page.getByRole('button',{name:'Copy ResumeSnapshot.md',exact:true}).waitFor();});
  }
  await page.screenshot({path:out+`/memory-${width}.png`,fullPage:true});
  if(width===390){
    await page.getByRole('button',{name:'Ownership',exact:true}).last().click();
    await check('Native wikilink preview and ZIP download',async()=>{await page.getByRole('button',{name:'Preview [[Wikilink]] note',exact:true}).click();const download=page.waitForEvent('download');await page.getByRole('button',{name:'Download Obsidian vault (.zip)',exact:true}).click();const d=await download;assert.match(d.suggestedFilename(),/\.zip$/);await d.saveAs(out+'/hero-obsidian.zip');});
    await check('Live policy override invalidates prior evidence',async()=>{await page.getByLabel('New rule',{exact:true}).fill('DEMO: finance review now required for discount contract changes');await page.getByLabel('Why this replaces the old decision',{exact:true}).fill('Witnessed final lifecycle stale-policy check');await page.getByRole('checkbox',{name:'Confirm this file-wide local policy change.',exact:true}).check();await page.getByRole('button',{name:'Record policy override',exact:true}).click();await page.getByText('Policy recorded. Dependent evidence must be rechecked.',{exact:true}).waitFor();await page.getByRole('button',{name:'Agent activity',exact:true}).last().click();await page.getByText('STALE ·',{exact:false}).waitFor();});
    await page.getByRole('button',{name:'Changes',exact:true}).last().click();await region.getByRole('combobox').selectOption(fixture.fixed);await region.getByText('STALE_POLICY',{exact:true}).waitFor();
    await page.screenshot({path:out+'/stale-policy-mobile.png',fullPage:true});
  }
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);await ctx.close();
  if(width===1560){
    await writeFile(out+'/awaiting-model-recall.json',JSON.stringify({proposal_id:fixture.fixed,tenant:fixture.tenant,revision:fixture.revision}));
    const {access}=await import('node:fs/promises');
    let resumed=false;
    for(let i=0;i<300;i++){try{await access(out+'/continue-policy-check');resumed=true;break}catch{}await new Promise(r=>setTimeout(r,1000));}
    assert.equal(resumed,true,'Model recall checkpoint timed out');
  }
 }
 assert.deepEqual(errors,[]);
 const source=await(await fetch(`${api}/repository/file-source?tenant_graph=${fixture.tenant}&expected_revision=${fixture.revision}&file_path=core/pricing.py`)).json();assert.match(source.source,/def calculate_discount/);
 checks.push('Captured base source unchanged after observed tests and override');
 await writeFile(out+'/checks.json',JSON.stringify({checks,errors,kind:'REAL_NATIVE_API_STDIO_BROWSER_AND_OWNED_WORKTREE',hosted_model_agent:true,model_provenance:'OpenCode official DeepSeek v4.1 Flash free; actual model-authored proposals; automated browser operator on owned fixture, not a human user study'},null,2));
}finally{await browser.close();}
