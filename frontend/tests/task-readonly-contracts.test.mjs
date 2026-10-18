/** Synthetic test data exercises the test runner, not product backend endpoints. */
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateConfig, requestVerdict, validateReadbacks} from './support/task-readonly.mjs';

const config = {frontendURL:'http://127.0.0.1:3015/workbench',apiURL:'http://127.0.0.1:8015/api/v1',
 applicationCommit:'a'.repeat(40),revision:'b'.repeat(40),candidateDigest:'c'.repeat(64),proposalHash:'d'.repeat(64),
 tenant:'repo_test_fixture',taskId:'task_fixture',planId:'plan_fixture',packId:'pack_fixture',workerAssignment:'assignment_worker',
 reviewerAssignment:'assignment_reviewer',workerRun:'run_worker',reviewerRun:'run_reviewer',proposalId:'prop_fixture'};
const data = () => ({identity:{application_commit:config.applicationCommit},snapshot:{tenant_graph:config.tenant,source_revision:config.revision},
 task:{task:{id:config.taskId,current_plan_id:config.planId},plans:[{id:config.planId}],
  assignments:[['WORKER',config.workerAssignment,config.workerRun],['REVIEWER',config.reviewerAssignment,config.reviewerRun]].map(([role,id,run_id])=>({role,id,run_id,
   task_id:config.taskId,plan_id:config.planId,pack_id:config.packId,expected_revision:config.revision,status:'RETURNED',claim_version:1,
   predecessor_id:role==='REVIEWER'?config.workerAssignment:undefined,reports_json:JSON.stringify([{action:'RETURN',report:'Bounded reviewer verdict ACCEPTED'}])})),
  runs:[config.workerRun,config.reviewerRun].map(id=>({id,plan_id:config.planId,pack_id:config.packId,status:'IDLE_NOT_SUCCESS',missing_sequences:[],event_count:1}))},
 proposals:{proposals:[{id:config.proposalId,tenant_graph:config.tenant,base_revision:config.revision,task_id:config.taskId,plan_id:config.planId,pack_id:config.packId,
  agent_run_id:config.workerRun,assignment_id:config.workerAssignment,candidate_digest:config.candidateDigest,proposal_hash:config.proposalHash,status:'PROPOSED',executions:[]}]}});

test('configuration requires explicit loopback identities',()=>{
 assert.equal(validateConfig(config).taskId,config.taskId);
 for (const change of [{apiURL:'https://example.com/api/v1'},{frontendURL:'http://example.com/workbench'},
  {apiURL:'http://user:pass@localhost:8015/api/v1'},{revision:'short'},{candidateDigest:'short'}, {taskId:'task_x?bad'}])
  assert.throws(()=>validateConfig({...config,...change}));
});
test('guard rejects mutation verbs and foreign origins without logging query values',()=>{
 for (const method of ['POST','PUT','PATCH','DELETE']) assert.equal(requestVerdict(method,config.apiURL, ['http://127.0.0.1:8015']).allowed,false);
 for (const method of ['GET','HEAD','OPTIONS']) assert.equal(requestVerdict(method,config.apiURL, ['http://127.0.0.1:8015']).allowed,true);
 const denied=requestVerdict('GET','http://example.com/path?token=redact',['http://127.0.0.1:8015']);
 assert.equal(denied.allowed,false);assert.ok(!JSON.stringify(denied).includes('redact'));
});
test('matching metadata remains explicitly unapproved and idle',()=>{
 const result=validateReadbacks(config,data());assert.equal(result.proposal.execution_count,0);
 assert.ok(result.runs.every(r=>r.status==='IDLE_NOT_SUCCESS'));
 assert.match(result.caveat,/not human approval/);
});
test('mixed revisions, candidate digests and run bindings are rejected',()=>{
 for (const mutate of [d=>d.snapshot.source_revision='e'.repeat(40),d=>d.identity.application_commit='e'.repeat(40),
  d=>d.proposals.proposals[0].candidate_digest='e'.repeat(64),d=>d.task.assignments[1].run_id='run_other',
  d=>d.task.runs[1].pack_id='pack_other']) {const d=data();mutate(d);assert.throws(()=>validateReadbacks(config,d));}
});
test('approval, execution, telemetry gaps and unrelated predecessor are not clean passes',()=>{
 for (const mutate of [d=>d.proposals.proposals[0].status='APPROVED',d=>d.proposals.proposals[0].executions=[{id:'execution_fixture'}],
  d=>d.task.runs[0].missing_sequences=[2],d=>d.task.assignments[1].predecessor_id='assignment_other']) {
   const d=data();mutate(d);assert.throws(()=>validateReadbacks(config,d));}
});
test('CLAIM acceptance instructions do not substitute for actual reviewer RETURN',()=>{
 const d=data();d.task.assignments[1].reports_json=JSON.stringify([{action:'CLAIM',report:'reviewer verdict ACCEPTED'},{action:'RETURN',report:'verdict BLOCKED'}]);
 assert.throws(()=>validateReadbacks(config,d));
});
test('runner requires explicit execution and never invokes mutating APIRequest methods',async()=>{
 const source=await readFile(new URL('./task-checkpoint-readonly-smoke.mjs',import.meta.url),'utf8');
 assert.match(source,/process\.argv\[2\], '--run'/);
 assert.doesNotMatch(source,/context\.request\.(post|put|patch|delete|fetch)\(/);
 assert.doesNotMatch(source,/(Approve exact proposal|execute-disposable-worktree|Create task and bounded context pack).*\.click/);
});
