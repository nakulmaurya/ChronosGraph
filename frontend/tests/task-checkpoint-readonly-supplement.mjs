/** Scoped keyboard/GET-only ownership/verdict-scroll supplement; never a policy override. */
import assert from 'node:assert/strict';
import {chromium, expect} from '@playwright/test';
import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {validateConfig,installReadOnlyGuard} from './support/task-readonly.mjs';
assert.equal(process.argv[2],'--run','Explicit --run CONFIG_JSON NEW_OUTPUT_DIRECTORY required');
assert.ok(process.argv[3] && process.argv[4]);
const c=validateConfig(JSON.parse(await readFile(process.argv[3],'utf8')));
const out=process.argv[4];await mkdir(out,{recursive:false});
const verify=expect.configure({timeout:20000});
const result={status:'STARTED',started_at:new Date().toISOString(),scope:'GET ownership chain, keyboard modal, scroll retained reviewer report; no model or mutation',rows:[],blocked_requests:[],manual_screenshot_review:'PENDING'};
let browser;
try {
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
 for(const viewport of [{width:1560,height:1000},{width:390,height:844}]){
  const row={viewport,status:'STARTED',page_errors:[],console_errors:[],http_errors:[],screenshots:[]};result.rows.push(row);
  const context=await browser.newContext({viewport,serviceWorkers:'block'});
  let page;
  try{
   await installReadOnlyGuard(context,[new URL(c.frontendURL).origin,new URL(c.apiURL).origin],result.blocked_requests);
   page=await context.newPage();page.setDefaultTimeout(20000);
   page.on('pageerror',e=>row.page_errors.push(e.message));
   page.on('console',m=>{if(m.type()==='error')row.console_errors.push(m.text());});
   page.on('response',r=>{if(r.status()>=400)row.http_errors.push({path:new URL(r.url()).pathname,status:r.status()});});
   const url=new URL(c.frontendURL);url.search=new URLSearchParams({snapshot:c.tenant,revision:c.revision,view:'3'}).toString();
   await page.goto(url.href,{waitUntil:'domcontentloaded'});
   await verify(page.getByLabel('Application and saved snapshot identity').locator('code').nth(2)).toHaveAttribute('title',c.revision);
   await page.getByLabel('Target file',{exact:true}).fill('client.py');
   await page.getByRole('button',{name:'Trace declared owners',exact:true}).click();
   const owners=page.getByRole('region',{name:'Declared owner evidence',exact:true});
   await verify(owners).toBeVisible();
   const org=owners.getByRole('region',{name:'Organizational reasoning evidence',exact:true});
   await verify(org).toContainText('OWNED_SYNTHETIC');
   await verify(org).toContainText('Compatibility Platform');
   await verify(org).toContainText('ACTIVE ·');
   await verify(org).toContainText('SUPERSEDED ·');
   for(const detail of await org.locator('details').all())await detail.locator('summary').click();
   await verify(org).toContainText('docs/ADR-002.md');
   await verify(org).toContainText('incidents/INC-007.md');
   await verify(org).toContainText(c.revision);
   await owners.scrollIntoViewIfNeeded();
   const image=`ownership-${viewport.width}.png`;await page.screenshot({path:`${out}/${image}`,fullPage:true});row.screenshots.push(image);
   const opener=page.getByRole('button',{name:'Connect agent',exact:true});
   await opener.focus();await page.keyboard.press('Enter');
   const modal=page.getByRole('dialog',{name:'Bring the graph to your agent.',exact:true});
   await verify(modal).toBeVisible();await page.keyboard.press('Escape');await verify(modal).toBeHidden();
   assert.equal(await opener.evaluate(e=>document.activeElement===e),true,'keyboard focus restored');row.keyboard_modal='PASS';
   await page.getByRole('navigation',{name:'Command center views'}).getByRole('button',{name:'Agent activity',exact:true}).click();
   const runtime=page.getByRole('region',{name:'Task runtime',exact:true});
   await runtime.getByLabel('Resume task ID',{exact:true}).fill(c.taskId);
   const handoffs=runtime.getByRole('region',{name:'Explicit worker handoffs',exact:true});await verify(handoffs).toBeVisible();
   const reviewer=handoffs.locator('details').filter({has:page.locator('summary').filter({hasText:/^reviewer ·/})});
   await reviewer.locator('summary').click();const pre=reviewer.locator('pre');
   await verify(pre).toContainText('verdict ACCEPTED');
   row.report_scroll=await pre.evaluate(el=>{
    const marker='verdict ACCEPTED',text=el.firstChild;
    const offset=text.textContent.indexOf(marker);if(offset<0)throw Error('Missing actual verdict marker');
    const range=document.createRange();range.setStart(text,offset);range.setEnd(text,offset+marker.length);
    const box=el.getBoundingClientRect();el.scrollTop+=range.getBoundingClientRect().top-box.top-el.clientHeight/4;
    const visible=range.getBoundingClientRect();
    return {scrollTop:el.scrollTop,clientHeight:el.clientHeight,scrollHeight:el.scrollHeight,
     verdict_visible:visible.top>=box.top && visible.bottom<=box.bottom};
   });
   assert.equal(row.report_scroll.verdict_visible,true,'verdict visible within independently scrollable report');
   const reviewImage=`reviewer-return-scrolled-${viewport.width}.png`;await reviewer.screenshot({path:`${out}/${reviewImage}`});row.screenshots.push(reviewImage);
   assert.deepEqual(row.page_errors,[]);assert.deepEqual(row.console_errors,[]);assert.deepEqual(row.http_errors,[]);assert.deepEqual(result.blocked_requests,[]);
   row.status='AUTOMATED_PASS_MANUAL_REVIEW_PENDING';
  }catch(error){row.status='FAIL';row.error=String(error.message);if(page){try{const image=`failure-${viewport.width}.png`;await page.screenshot({path:`${out}/${image}`,fullPage:true});row.screenshots.push(image);}catch{}}throw error;}
  finally{await context.close();}
 }
 result.status='AUTOMATED_PASS_MANUAL_REVIEW_PENDING';
}catch(error){result.status='FAIL';result.error=String(error.message);process.exitCode=1;}
finally{
 if(browser)await browser.close();result.finished_at=new Date().toISOString();await writeFile(`${out}/results.json`,JSON.stringify(result,null,2)+'\n');
 const manifest={};for(const name of(await readdir(out)).sort())manifest[name]=createHash('sha256').update(await readFile(`${out}/${name}`)).digest('hex');
 await writeFile(`${out}/sha256-manifest.json`,JSON.stringify(manifest,null,2)+'\n');console.log(JSON.stringify({status:result.status,error:result.error,viewports:result.rows.map(r=>({viewport:r.viewport,status:r.status}))}));
}
