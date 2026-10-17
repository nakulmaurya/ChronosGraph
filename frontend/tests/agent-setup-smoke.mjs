/** Setup usability only; actual stdio behavior is tested in test_agent_workflow.py. */
import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
const front = process.env.FRONTEND_URL || 'http://127.0.0.1:3003';
const api = process.env.API_URL || 'http://127.0.0.1:8004/api/v1';
const out = process.env.EVIDENCE_DIR || '/tmp/chronos-agent-setup';
await mkdir(out, {recursive:true});
const browser = await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',args:['--no-sandbox']});
const checks = [], errors = [];
try {
  for (const width of [1560,390]) {
    const ctx = await browser.newContext({viewport:{width,height:1000},permissions:['clipboard-read','clipboard-write']});
    const page = await ctx.newPage();
    page.on('pageerror',e=>errors.push(e.message));
    page.on('request',r=>{if(r.method()==='POST')errors.push('Unexpected mutation '+r.url());});
    await page.goto(front);
    const chooser = page.getByRole('combobox',{name:'Repository',exact:true});
    for (const tenant of ['repo_falkordb_py','repo_mcp_python_sdk']) {
      await chooser.selectOption(tenant);
      const snapshot = await (await fetch(`${api}/workspace/snapshot?tenant_graph=${tenant}`)).json();
      await page.waitForFunction(rev=>document.querySelector('.cc-revision code')?.textContent===rev.slice(0,8),snapshot.source_revision);
      const opener = page.getByRole('button',{name:'Connect agent',exact:true});
      await opener.click();
      const modal = page.getByRole('dialog',{name:'Bring the graph to your agent.'});
      await modal.waitFor();
      await modal.getByLabel('Absolute backend directory').fill('/home/dev/Chronos Graph/backend');
      await modal.getByLabel('Python executable on agent machine').fill('/home/dev/Chronos Graph/.venv/bin/python');
      await modal.getByLabel('FalkorDB port',{exact:true}).fill('65536');
      assert.equal(await modal.getByRole('button',{name:'Copy config',exact:true}).isDisabled(),true);
      await modal.getByLabel('FalkorDB port',{exact:true}).fill('6379');
      await modal.getByRole('button',{name:'Copy config',exact:true}).click();
      const config=JSON.parse(await page.evaluate(()=>navigator.clipboard.readText())).mcpServers.chronosgraph;
      assert.equal(config.command,'/home/dev/Chronos Graph/.venv/bin/python');
      assert.equal(config.cwd,'/home/dev/Chronos Graph/backend');
      assert.equal(config.env.FALKORDB_PORT,'6379');
      assert.equal(config.env.CHRONOSGRAPH_REQUIRE_SNAPSHOT_GUARD,'1');
      await modal.getByRole('button',{name:'Copy selected snapshot handoff',exact:true}).click();
      const handoff=await page.evaluate(()=>navigator.clipboard.readText());
      assert.ok(handoff.includes(JSON.stringify({tenant_graph:tenant,expected_revision:snapshot.source_revision})));
      assert.match(handoff,/every subsequent tool call/);
      await page.screenshot({path:`${out}/setup-${tenant}-${width}.png`,fullPage:true});
      await page.keyboard.press('Escape');
      await modal.waitFor({state:'hidden'});
      assert.equal(await opener.evaluate(e=>document.activeElement===e),true);
      checks.push(`Explicit config and selected snapshot copied; keyboard restores focus: ${tenant} ${width}px`);
    }
    await ctx.close();
  }
  assert.deepEqual(errors,[]);
  await writeFile(`${out}/results.json`,JSON.stringify({checks,errors,mutation_requests:0},null,2));
  console.log(JSON.stringify({checks,errors}));
} finally { await browser.close(); }
