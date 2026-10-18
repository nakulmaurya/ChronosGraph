import {test} from 'node:test';import assert from 'node:assert/strict';
import {runStatusLabel,telemetryLabel,usageBasisLabel} from '../src/lib/task-runtime.ts';
test('Task statuses never equate idle with verified success',()=>{assert.equal(runStatusLabel('IDLE_NOT_SUCCESS'),'Agent idle; verification pending');assert.match(telemetryLabel('GAPS'),/incomplete/);assert.match(usageBasisLabel('LEGACY_MESSAGE_SNAPSHOTS_NOT_COMPLETED_STEP_TOTALS'),/not a completed-step total/);assert.match(usageBasisLabel('OPENCODE_COMPLETED_STEP_PART'),/Completed step/);});
