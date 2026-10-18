import {test} from 'node:test';import assert from 'node:assert/strict';
import {runStatusLabel,telemetryLabel,usageBasisLabel} from '../src/lib/task-runtime.ts';
test('Task statuses never equate idle with verified success',()=>{assert.equal(runStatusLabel('IDLE_NOT_SUCCESS'),'Agent idle; verification pending');assert.match(telemetryLabel('GAPS'),/incomplete/);assert.match(usageBasisLabel('LEGACY_MESSAGE_SNAPSHOTS_NOT_COMPLETED_STEP_TOTALS'),/not a completed-step total/);assert.match(usageBasisLabel('OPENCODE_COMPLETED_STEP_PART'),/Completed step/);});

import {handoffStatusLabel} from '../src/lib/task-runtime.ts';
test('Returned handoffs separate agent review from human approval',()=>{
 assert.equal(handoffStatusLabel('WORKER','RETURNED','[]'),'Worker candidate returned · Review separate');
 assert.equal(handoffStatusLabel('REVIEWER','RETURNED',JSON.stringify([{action:'RETURN',report:'Fresh independent OpenCode reviewer verdict ACCEPTED for this bounded candidate only.'}])),'Agent review complete · Acceptance recorded');
 assert.equal(handoffStatusLabel('REVIEWER','RETURNED','broken'),'Reviewer returned · Inspect report');
 assert.equal(handoffStatusLabel('REVIEWER','RETURNED',JSON.stringify([{action:'RETURN',report:'Not accepted; incomplete'}])),'Reviewer returned · Inspect verdict');
 assert.equal(handoffStatusLabel('REVIEWER','CLAIMED','[]'),'Working under current claim');
});

import {declaredReturnReport} from '../src/lib/task-runtime.ts';
test('Declared review report remains explicit plain evidence',()=>{
 assert.equal(declaredReturnReport('bad'),'');assert.equal(declaredReturnReport('{}'),'');
 assert.equal(declaredReturnReport('[{"action":"RETURN","report":"39 checks passed; not approval"}]'),'39 checks passed; not approval');
});
