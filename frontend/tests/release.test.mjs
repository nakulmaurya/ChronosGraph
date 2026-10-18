import test from 'node:test';
import assert from 'node:assert/strict';
import {pinnedCommit,buildPairing} from '../src/lib/release.ts';
test('build identity never guesses missing or malformed commits',()=>{
 for(const value of [undefined,null,'short','A'.repeat(40),'/host/path'])assert.equal(pinnedCommit(value),null);
 assert.equal(pinnedCommit('a'.repeat(40)),'a'.repeat(40));
});
test('UI and API declarations distinguish match, mismatch and unknown',()=>{
 assert.equal(buildPairing('a'.repeat(40),'a'.repeat(40)),'MATCHED_DECLARATIONS');
 assert.equal(buildPairing('a'.repeat(40),'b'.repeat(40)),'MISMATCH');
 assert.equal(buildPairing('a'.repeat(40),null),'UNRECORDED');
});
