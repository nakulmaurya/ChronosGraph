import test from 'node:test';
import assert from 'node:assert/strict';
import {breadcrumbParent,boundedMapNotice} from '../src/lib/command-center.ts';
test('folder breadcrumbs remain inside the repository',()=>{
 assert.equal(breadcrumbParent('src/pkg/'),'src/');assert.equal(breadcrumbParent('src/'),'');assert.equal(breadcrumbParent(''),'');
});
test('map omissions are made visible',()=>{
 const coverage={files_truncated:false,groups_truncated:false,import_edges_truncated:false};
 assert.equal(boundedMapNotice({coverage}),false);
 for(const flag of Object.keys(coverage))assert.equal(boundedMapNotice({coverage:{...coverage,[flag]:true}}),true);
});
