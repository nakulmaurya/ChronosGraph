const fs=require('node:fs/promises'),path=require('node:path'),os=require('node:os'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const ROOT=process.env.CHRONOSGRAPH_REPO||path.resolve(__dirname,'..');
const PYTHON=process.env.BACKEND_PYTHON||path.join(ROOT,'.venv/bin/python');
const {chromium}=require(path.join(ROOT,'frontend/node_modules/@playwright/test'));
const OUT=process.env.CHRONOSGRAPH_RECORDING_DIR||path.join(os.tmpdir(),'chronosgraph-t08-recording');
const BASE=process.env.FRONTEND_URL||'http://127.0.0.1:3003',API=process.env.TEST_API_URL||'http://127.0.0.1:8003/api/v1';
let browser,context,page,t0,start,policy=[],created=[],snapshotRestored=false;
const measures={},chapters=[],errors=[];
const target='falkordb/graph.py',scenario='T-08 recording policy review falkordb/graph.py';
async function at(sec){let d=t0+sec*1000-Date.now();if(d>0)await page.waitForTimeout(d);else if(d< -3000)throw new Error('Choreography overrun at '+sec+': '+d);}
async function cue(title,text){chapters.push({start:(Date.now()-t0)/1000,title,text});console.log(title,chapters.at(-1).start);}
async function click(locator){await locator.scrollIntoViewIfNeeded();let b=await locator.boundingBox();if(b)await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:8});await locator.click();}
async function track(n){await click(page.getByRole('button',{name:new RegExp('TRACK 0'+n)}));}
async function tenant(t){await page.locator('#tenant').selectOption(t);await page.waitForFunction(()=>!document.querySelector('#tenant').disabled);await page.waitForTimeout(300);}
async function action(name,endpoint){let response=page.waitForResponse(r=>r.url().endsWith(endpoint)&&r.request().method()==='POST');await click(page.getByRole('button',{name,exact:true}));let r=await response,d=await r.json();assert.ok(r.ok(),JSON.stringify(d));await page.waitForFunction(()=>!document.querySelector('#tenant').disabled);return d;}
async function selectFile(p){for(const b of await page.locator('fieldset input[type=checkbox]').all())await b.uncheck();await page.getByRole('checkbox',{name:p,exact:true}).check();}
async function shot(name){await page.screenshot({path:path.join(OUT,name+'.png')});}
async function restore(){if(!policy.length)return;const py=`import json;from app.db.client import db_manager;g=db_manager.get_graph('repo_falkordb_py');data=json.loads(${JSON.stringify(JSON.stringify(policy))});ids=json.loads(${JSON.stringify(JSON.stringify(created))});\nfor r in data:g.query('MATCH (d:Decision {id:$id}) SET d=$props',{'id':r['id'],'props':r})\nfor i in ids:g.query('MATCH (d:Decision {id:$id}) DETACH DELETE d',{'id':i})\nprint('restored')`;
execFileSync(PYTHON,['-c',py],{cwd:path.join(ROOT,'backend'),env:{...process.env,PYTHONPATH:path.join(ROOT,'backend')}});snapshotRestored=true;}
(async()=>{
 await fs.mkdir(OUT,{recursive:true});let catalog=await(await fetch(API+'/tenants')).json();assert.equal(catalog.length,4);
 measures.catalog=catalog.map(t=>({tenant:t.tenant_graph,nodes:t.node_count}));
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 context=await browser.newContext({viewport:{width:1760,height:990},recordVideo:{dir:OUT,size:{width:1760,height:990}},reducedMotion:'reduce'});
 await context.addInitScript(()=>{window.addEventListener('DOMContentLoaded',()=>{const p=document.createElement('div');Object.assign(p.style,{position:'fixed',width:'14px',height:'14px',border:'2px solid #a5f3fc',borderRadius:'50%',boxShadow:'0 0 0 4px #22d3ee22',zIndex:'2147483647',pointerEvents:'none',transform:'translate(-50%,-50%)'});document.body.append(p);document.addEventListener('mousemove',e=>{p.style.left=e.clientX+'px';p.style.top=e.clientY+'px';});});});
 start=Date.now();page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));await page.goto(BASE,{waitUntil:'networkidle'});await page.waitForFunction(()=>document.querySelector('#tenant')?.options.length===4&&!document.querySelector('#tenant').disabled);
 await page.locator('.react-flow__node').first().waitFor();t0=Date.now();
 await cue('Graph context. A connected second brain.','Four real repository graphs · live source sizes · zero product model calls');
 await at(4);await tenant('repo_graphrag_sdk');await at(9);await tenant('repo_falkordb_code_graph');await at(14);await tenant('repo_mcp_python_sdk');await shot('01-four-repos');
 await at(20);await tenant('repo_falkordb_py');await track(1);await selectFile(target);
 await page.locator('.patch-editor summary').click();await page.getByLabel('Apply Python snippet overlay').check();
 await page.locator('#python-patch').fill('from falkordb.query_result import QueryResult\n\ndef context_audit_patch(response):\n    return QueryResult(response)\n');
 await at(25);await cue('Track 1 / Copy. Parse. Trace. Clean up.','Real Python AST overlay · bounded impact and candidate tests · measured audit subset');
 const a=await action('Run GRAPH.COPY audit','/track1/sandbox-audit');assert.ok(a.sandbox_cleaned_up);measures.audit={files:a.impacted_files.length,functions:a.impacted_functions.length,missed:a.blind_agent_comparison.missed_downstream_count,tests:a.impacted_test_files.length,raw_bytes:a.context_window_savings.raw_repo_bytes,slice_bytes:a.context_window_savings.slice_bytes,saved_pct:a.context_window_savings.context_saved_pct,contributors:a.recommended_reviewers.map(x=>x.name||x.login)};
 await shot('02-ast-audit');
 await at(37);await page.getByRole('heading',{name:'Evidence-based reviewers'}).scrollIntoViewIfNeeded();await shot('03-commit-authors');
 await at(39);await page.getByText('Guy Korland',{exact:true}).first().scrollIntoViewIfNeeded();await shot('03b-guy-korland');
 await at(41);await page.getByText('Roi Lipman',{exact:true}).first().scrollIntoViewIfNeeded();await shot('03c-roi-lipman');
 await at(43);await tenant('repo_mcp_python_sdk');await track(1);await selectFile('src/mcp/shared/dispatcher.py');
 const sdk=await action('Run GRAPH.COPY audit','/track1/sandbox-audit');assert.ok(sdk.sandbox_cleaned_up);measures.sdk={files:sdk.impacted_files.length,tests:sdk.impacted_test_files.length,raw_bytes:sdk.context_window_savings.raw_repo_bytes,slice_bytes:sdk.context_window_savings.slice_bytes,saved_pct:sdk.context_window_savings.context_saved_pct};
 await at(52);await shot('04-sdk-audit');
 await at(60);await tenant('repo_falkordb_py');await track(2);await page.locator('#scenario').fill(scenario);
 await at(65);await cue('Track 2 / Keep the verified trajectory.','Five cold actions → three shortestPath actions · historical branches remain visible');
 const cold=await action('Run #1 · Cold triage','/track2/investigate');assert.equal(cold.total_steps_executed,5);await shot('05-cold');
 await at(77);const warm=await action('Run #2 · Compiled replay','/track2/investigate');assert.equal(warm.total_steps_executed,3);measures.memory={cold_ms:cold.duration_ms,warm_ms:warm.duration_ms,speedup:warm.latency_speedup_factor,context_reduction:cold.context_token_reduction_pct,snapshot_bytes:warm.resume_snapshot.snapshot_bytes};await shot('06-warm');
 await at(86);await click(page.getByRole('button',{name:'Obsidian LLM Wiki / ResumeSnapshot',exact:true}));let wiki=page.getByRole('dialog',{name:'Obsidian Second Brain'});await wiki.waitFor();await click(wiki.getByRole('button',{name:'ResumeSnapshot',exact:true}));assert.ok((await wiki.locator('.wiki-note').textContent()).includes('Target: '+target));assert.match(await wiki.locator('.wiki-note').textContent(),/Current playbook /);await shot('07-resume');
 await at(95);await click(wiki.getByRole('button',{name:'log.md',exact:true}));await wiki.locator('.wiki-note').evaluate((e,id)=>{const w=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const i=n.textContent.indexOf(id);if(i>=0){const r=document.createRange();r.setStart(n,i);r.setEnd(n,i+id.length);e.scrollTop+=r.getBoundingClientRect().top-e.getBoundingClientRect().top-100;break;}}},warm.investigation_id);await shot('08-ledger');
 await at(102);await click(wiki.getByRole('button',{name:'Close wiki',exact:true}));
 await at(105);await cue('Track 3 / Current policy guards recovered memory.','Live architect override → old rule SUPERSEDED → stale playbook HTTP 409');
 await track(3);await page.locator('#policy-file').selectOption(target);const before=await action('Read current policy','/track3/ask-brain');
 // Capture complete node properties, including embeddings, outside the recording UI.
 policy=JSON.parse(execFileSync(PYTHON,['-c',"import json;from app.db.client import db_manager;g=db_manager.get_graph('repo_falkordb_py');print(json.dumps([n[0].properties for n in g.ro_query(\"MATCH (d:Decision)-[:GOVERNS]->(:File {path:'falkordb/graph.py'}) RETURN d\").result_set]))"],{cwd:path.join(ROOT,'backend'),env:{...process.env,PYTHONPATH:path.join(ROOT,'backend')}}));
 await page.locator('.override-form>summary').click();await page.locator('#rule').fill('Demo architect update: require explicit bounded read-only graph discovery.');await page.locator('#rationale').fill('Recorded T-08 demonstration; restore original local policies after capture.');await page.locator('.confirmation input').check();
 await at(118);const override=await action('Record policy override','/track3/override-policy');created=override.active_decisions.map(d=>d.id).filter(id=>!policy.some(p=>p.id===id));assert.ok(created.length);await shot('09-override');
 await at(126);await track(2);
 // The ordinary replay stays disabled. A supported diagnostic issues the real
 // backend replay request and displays the authoritative HTTP 409 response.
 const button=page.getByRole('button',{name:'Check backend replay guard',exact:true});
 const stale=page.waitForResponse(r=>r.url().endsWith('/track2/investigate')&&r.request().method()==='POST');
 await click(button);const refusal=await stale;assert.equal(refusal.status(),409);measures.stale_http=refusal.status();await page.locator('.error-banner').waitFor();await shot('10-stale-guard');
 await at(136);await restore();
 await at(140);await cue('Export a linked wiki. Bring the workflow to your agent.','index.md · log.md · bidirectional wikilinks · portable five-tool skill');
 await click(page.getByRole('button',{name:'Obsidian LLM Wiki / ResumeSnapshot',exact:true}));wiki=page.getByRole('dialog',{name:'Obsidian Second Brain'});await wiki.waitFor();await click(wiki.getByRole('button',{name:'index.md',exact:true}));await wiki.locator('.wiki-link').first().click();await shot('11-wikilink');
 await at(145);const download=page.waitForEvent('download');await click(wiki.getByRole('button',{name:'Export Obsidian Vault',exact:true}));await(await download).saveAs(path.join(OUT,'demo-vault.zip'));
 await at(149);await click(wiki.getByRole('button',{name:'Close wiki',exact:true}));await click(page.getByRole('button',{name:'MCP config',exact:true}));const mcp=page.getByRole('dialog');await click(mcp.getByRole('tab',{name:'Cursor',exact:true}));await shot('12-skill');
 await at(154);await mcp.getByRole('heading',{name:'Five exposed tools',exact:true}).scrollIntoViewIfNeeded();await shot('12b-five-tools');
 await at(156);await mcp.getByText('find_true_code_owners',{exact:true}).scrollIntoViewIfNeeded();
 await at(158);await click(mcp.getByRole('tab',{name:'Antigravity / OpenCode',exact:true}));
 await at(163);await page.keyboard.press('Escape');
 await at(165);assert.deepEqual(errors,[]);const video=page.video();await context.close();await fs.rename(await video.path(),path.join(OUT,'raw-demo.webm'));await browser.close();
 await fs.writeFile(path.join(OUT,'recording-metadata.json'),JSON.stringify({lead_in_seconds:(t0-start)/1000,duration_seconds:165,chapters,measurements:measures,browser_errors:errors,policy_restored:snapshotRestored},null,2));console.log('SUCCESS',JSON.stringify(measures));process.exit(0);
})().catch(async e=>{console.error(e);try{await restore();if(page)await shot('FAILED');if(context)await context.close();if(browser)await browser.close();}catch(x){console.error('cleanup',x);}process.exit(1);});
