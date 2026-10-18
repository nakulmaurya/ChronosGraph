/** Actual local Chromium network-guard fixture, NOT a ChronosGraph browser gate. */
import {createServer} from 'node:http';
import assert from 'node:assert/strict';
import {chromium} from '@playwright/test';
import {installReadOnlyGuard} from './task-readonly.mjs';
const seen=[];let upgrades=0;
const server=createServer((req,res)=>{seen.push({method:req.method,path:req.url});res.writeHead(200,{'Content-Type':'text/plain'});res.end('Local guard fixture, not the product');});
server.on('upgrade',(_req,socket)=>{upgrades++;socket.destroy();});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const origin=`http://127.0.0.1:${server.address().port}`;
let browser;
const blocked=[];
try {
 browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
 const context=await browser.newContext({serviceWorkers:'block'});
 await installReadOnlyGuard(context,[origin],blocked);
 const page=await context.newPage();await page.goto(origin+'/fixture');
 const outcomes=await page.evaluate(async()=>{
  const get=await fetch('/read');
  let postBlocked=false,foreignBlocked=false;
  try {await fetch('/must-not-arrive',{method:'POST',body:'synthetic fixture'});} catch {postBlocked=true;}
  try {await fetch('http://127.0.0.1:1/foreign');} catch {foreignBlocked=true;}
  const websocketClosed=await new Promise(resolve=>{
   const ws=new WebSocket(location.origin.replace('http:','ws:')+'/must-not-upgrade');
   const timer=setTimeout(()=>{ws.close();resolve(false);},2000);
   ws.onclose=()=>{clearTimeout(timer);resolve(true);};
  });
  return {get:get.status,postBlocked,foreignBlocked,websocketClosed};
 });
 assert.deepEqual(outcomes,{get:200,postBlocked:true,foreignBlocked:true,websocketClosed:true});
 assert.ok(seen.every(r=>r.method==='GET'));
 assert.ok(!seen.some(r=>r.path==='/must-not-arrive'));
 assert.equal(upgrades,0);
 assert.deepEqual(blocked.map(r=>r.kind).sort(),['mutation_method','unexpected_origin','websocket_disabled']);
 console.log(JSON.stringify({status:'PASS_GUARD_FIXTURE_ONLY',browser:browser.version(),get_succeeded:true,post_blocked_before_server:true,foreign_origin_blocked:true,websocket_blocked_before_server:true,
  product_browser_verification:'NOT_RUN',vm_calls:0,provider_calls:0}));
 await context.close();
} finally {if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
