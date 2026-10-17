import test from 'node:test';
import assert from 'node:assert/strict';
import {changedRegion,dependencyMap} from '../src/lib/change-planning.ts';
test('changed region shows removed and added source without mutating inputs',()=>{
  const before='import a\ndef run():\n    return 1\n';const after=before.replace('return 1','return 2');
  const diff=changedRegion(before,after);
  assert.match(diff.text,/-     return 1/);assert.match(diff.text,/\+     return 2/);
  assert.equal(diff.unchanged,false);assert.equal(diff.truncated,false);
  assert.equal(changedRegion(before,before).unchanged,true);
  assert.match(changedRegion(before,'').text,/- import a/);
});
test('large changed-region display reports truncation instead of hiding it',()=>{
  const diff=changedRegion('old',Array.from({length:500},(_,i)=>`x${i}`).join('\n'));
  assert.equal(diff.truncated,true);assert.equal(diff.text.split('\n').length,240);
});
test('dependency rendering preserves only API evidence, including isolated files',()=>{
  const view={paths:['a.py','b.py','isolated.py'],edges:[{source:'b.py',target:'a.py'}],nodes_total:3,nodes_truncated:false,edges_truncated:false,scope:'imports'};
  const map=dependencyMap(view);
  assert.deepEqual(map.nodes.map(n=>n.id),view.paths);
  assert.deepEqual(map.edges,[{source:'b.py',target:'a.py',count:1}]);
  assert.equal(map.edges.some(e=>e.source==='isolated.py'||e.target==='isolated.py'),false);
  assert.deepEqual(view.edges,[{source:'b.py',target:'a.py'}]);
});
