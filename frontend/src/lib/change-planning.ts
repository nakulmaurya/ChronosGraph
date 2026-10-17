import type { RepositoryMap } from './command-center';
export type DependencyView = { paths: string[]; edges: {source:string;target:string}[]; nodes_total:number; nodes_truncated:boolean; edges_truncated:boolean; scope:string };
export type ChangeImpact = { changed_files:string[]; impacted_files:string[]; impacted_test_files:string[];
  potentially_broken_callers:string[]; recommended_pytest_command:string; sandbox_cleaned_up:boolean;
  dependency_graphs:{before:DependencyView;after:DependencyView}; unresolved_calls:number;
  parse_coverage:{before_failed_files:string[];after_failed_files:string[]};
  added_dependencies:{relationship:string;source:string;target:string}[];
  removed_dependencies:{relationship:string;source:string;target:string}[];
};
export function dependencyMap(view:DependencyView):RepositoryMap {
  return { prefix:'',counts:{File:view.nodes_total},nodes:view.paths.map(path=>({id:path,path,kind:'file',files:1})),
    edges:view.edges.map(e=>({...e,count:1})),inventory:[],execution_time_ms:0,
    coverage:{files_truncated:view.nodes_truncated,groups_total:view.nodes_total,groups_truncated:view.nodes_truncated,
      inventory_truncated:false,import_edges_truncated:view.edges_truncated} };
}
/** Bounded contiguous changed-region display, not an LCS/minimal patch generator. */
export function changedRegion(before:string, after:string, limit=240):{text:string;truncated:boolean;unchanged:boolean} {
  if(before===after)return {text:'No source changes.',truncated:false,unchanged:true};
  const a=before.split('\n'),b=after.split('\n');
  let prefix=0,suffix=0;
  while(prefix<a.length && prefix<b.length && a[prefix]===b[prefix])prefix++;
  while(suffix<a.length-prefix && suffix<b.length-prefix && a[a.length-1-suffix]===b[b.length-1-suffix])suffix++;
  const rows=[...a.slice(Math.max(0,prefix-2),prefix).map(x=>'  '+x),
    ...a.slice(prefix,a.length-suffix).map(x=>'- '+x),...b.slice(prefix,b.length-suffix).map(x=>'+ '+x),
    ...a.slice(a.length-suffix,a.length-suffix+2).map(x=>'  '+x)];
  return {text:rows.slice(0,limit).join('\n'),truncated:rows.length>limit,unchanged:false};
}
