import test from 'node:test';
import assert from 'node:assert/strict';
import { readDraft, saveDraft } from '../src/lib/change-drafts.ts';
const revision='a'.repeat(40);
const draft={path:'pkg/a.py',revision,sha256:'b'.repeat(64),proposed:'def renamed():\n    return 42\n',deleted:false};
function storage(){const m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,v)};}
test('proposal survives navigation only within the selected tenant and commit',()=>{
 const s=storage();assert.equal(saveDraft(s,'repo_one',draft),true);assert.deepEqual(readDraft(s,'repo_one',revision),draft);
 assert.equal(readDraft(s,'repo_two',revision),null);assert.equal(readDraft(s,'repo_one','c'.repeat(40)),null);
 saveDraft(s,'repo_one',{...draft,path:'pkg/other.py',proposed:'OTHER'});
 assert.equal(readDraft(s,'repo_one',revision).path,'pkg/other.py');
 assert.deepEqual(readDraft(s,'repo_one',revision,'pkg/a.py'),draft);
 saveDraft(s,'repo_one',{...draft,deleted:true});assert.equal(readDraft(s,'repo_one',revision).deleted,true);
});
test('invalid or unavailable tab storage fails safely',()=>{
 const broken={getItem(){throw Error('blocked')},setItem(){throw Error('quota')}};
 assert.equal(saveDraft(broken,'repo_one',draft),false);assert.equal(readDraft(broken,'repo_one',revision),null);
 for(const invalid of [{...draft,path:'../outside.py'},{...draft,sha256:'bad'},{...draft,deleted:'yes'},{...draft,proposed:null}]){
  const s=storage();saveDraft(s,'repo_one',invalid);assert.equal(readDraft(s,'repo_one',revision),null);
 }
 assert.equal(readDraft({getItem:()=>'{oops'},'repo_one',revision),null);
});
