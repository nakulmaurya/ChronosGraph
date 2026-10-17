/** Native HTTP workflow against an isolated DB, not mocked success responses. */
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
const front=process.env.FRONTEND_URL||'http://127.0.0.1:3003';
const api=process.env.API_URL||'http://127.0.0.1:8005/api/v1';
const tenant=process.env.TENANT_GRAPH;
if(!tenant?.startsWith('repo_test_'))throw new Error('Use the disposable fixture created by verify-change-planning-ui.sh');
const out=process.env.EVIDENCE_DIR||'/tmp/chronos-change-planning';await mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
const checks=[],errors=[],posts=[];
try{
 for(const width of [1560,390]){
  const ctx=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});const page=await ctx.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST'){posts.push(r.url());if(r.url()!==api+'/diff/impact')errors.push('Unexpected write '+r.url());}});
  await page.goto(front);await page.getByRole('combobox',{name:'Repository',exact:true}).selectOption(tenant);
  await page.locator('.cc-tree-file').filter({hasText:'src'}).click();
  await page.locator('.cc-tree-file').filter({hasText:'pkg'}).click();
  await page.locator('.cc-tree-file').filter({hasText:'a.py'}).click();
  await page.getByRole('button',{name:'Plan a change to this file',exact:true}).click();
  const planner=page.getByRole('region',{name:'Selected file change planner'});
  assert.equal(await planner.getByLabel('Python file in selected saved version').inputValue(),'src/pkg/a.py');
  await planner.getByRole('button',{name:'Load captured file',exact:true}).click();
  const editor=planner.getByRole('textbox',{name:'Proposed source',exact:true});await editor.waitFor();
  const before=await editor.inputValue();assert.match(before,/def helper/);
  const preview=planner.getByRole('button',{name:'Preview change impact',exact:true});assert.equal(await preview.isDisabled(),true);
  await editor.fill('def renamed():\n    return 8\n');
  const response=page.waitForResponse(r=>r.url()===api+'/diff/impact'&&r.request().method()==='POST');
  await preview.click();const result=await (await response).json();
  assert.equal(result.sandbox_cleaned_up,true);assert.ok(result.potentially_broken_callers.includes('src/pkg/b.py:run'));
  const results=planner.getByRole('region',{name:'Change impact results'});await results.waitFor();
  await results.getByText('src/pkg/b.py:run',{exact:true}).waitFor();
  await results.getByRole('button',{name:'tests/test_helper.py',exact:true}).first().waitFor();
  for(const mode of ['before','after']) { const nodes=planner.locator(`[aria-label="${mode} dependency graph"] .react-flow__node`); await nodes.first().waitFor({state:'visible'}); assert.ok(await nodes.count()>0); }
  await page.screenshot({path:`${out}/impact-${width}.png`,fullPage:true});
  const snapshot=await(await fetch(`${api}/workspace/snapshot?tenant_graph=${tenant}`)).json();
  const captured=await(await fetch(`${api}/repository/file-source?tenant_graph=${tenant}&expected_revision=${snapshot.source_revision}&file_path=src/pkg/a.py`)).json();
  assert.equal(captured.source,before);
  checks.push(`Selected file → readable comparison → real impact/candidate tests; saved source unchanged (${width}px)`);
  await editor.fill('def broken(:\n');assert.equal(await results.count(),0);
  const invalid=page.waitForResponse(r=>r.url()===api+'/diff/impact');await preview.click();assert.equal((await invalid).status(),422);
  await planner.getByRole('alert').filter({hasText:'422'}).waitFor();assert.equal(await results.count(),0);
  checks.push(`Invalid Python cannot retain a previous success (${width}px)`);
  // Editing invalidates old success before a deliberately wrong-commit request.
  await editor.fill('def renamed():\n    return 9\n');assert.equal(await results.count(),0);
  await page.route('**/api/v1/diff/impact',route=>{
    const body=route.request().postDataJSON();body.expected_revision='0'.repeat(40);
    return route.continue({postData:JSON.stringify(body)});
  });
  const rejected=page.waitForResponse(r=>r.url()===api+'/diff/impact');await preview.click();assert.equal((await rejected).status(),409);
  await planner.getByRole('alert').filter({hasText:'409'}).waitFor();assert.equal(await results.count(),0);
  await page.unroute('**/api/v1/diff/impact');checks.push(`Stale success cleared and real wrong-version 409 surfaced (${width}px)`);
  await preview.click();await results.waitFor();
  await planner.getByRole('checkbox',{name:'Preview deleting this file',exact:true}).check();
  assert.equal(await editor.isDisabled(),true);assert.equal(await results.count(),0);
  const deletion=page.waitForResponse(r=>r.url()===api+'/diff/impact');await preview.click();
  const deleted=await(await deletion).json();assert.equal(deleted.sandbox_cleaned_up,true);
  assert.equal(deleted.dependency_graphs.after.paths.includes('src/pkg/a.py'),false);
  await results.waitFor();
  checks.push(`Deletion stays a preview and excludes the removed file from after-state evidence (${width}px)`);
  await results.getByRole('button',{name:'tests/test_helper.py',exact:true}).first().click();
  await page.locator('.cc-inspector-heading h2').filter({hasText:'test_helper.py'}).waitFor();
  checks.push(`Candidate test opens the repository inspector (${width}px)`);
  await page.getByRole('button',{name:'Changes',exact:true}).last().click();
  await page.getByRole('combobox',{name:'Repository',exact:true}).selectOption('repo_falkordb_py');
  await page.locator('.cc-overview h1').waitFor(); // Repository changes intentionally reset to the map.
  await page.getByRole('button',{name:'Changes',exact:true}).last().click();
  const nextPlanner=page.getByRole('region',{name:'Selected file change planner'});
  assert.equal(await nextPlanner.getByRole('textbox',{name:'Proposed source',exact:true}).count(),0);
  assert.equal(await nextPlanner.getByLabel('Python file in selected saved version').inputValue(),'');
  await nextPlanner.getByLabel('Python file in selected saved version').fill('missing.py');
  await nextPlanner.getByRole('button',{name:'Load captured file',exact:true}).click();
  await nextPlanner.getByRole('alert').filter({hasText:'404'}).waitFor();
  assert.equal(await nextPlanner.getByRole('textbox',{name:'Proposed source',exact:true}).count(),0);
  checks.push(`Missing captured file shows a read failure, not stale editor content (${width}px)`);
  checks.push(`Repository switch discards old editor and result (${width}px)`);
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
  await ctx.close();
 }
 assert.deepEqual(errors,[]);await writeFile(`${out}/results.json`,JSON.stringify({checks,errors,posts},null,2));console.log(JSON.stringify({checks,errors,post_count:posts.length}));
}finally{await browser.close();}
