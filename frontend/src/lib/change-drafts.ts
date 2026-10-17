/** Tab-local proposals only. Never persist preview results or cross snapshot identity. */
export type ChangeDraft = { path:string; revision:string; sha256:string; proposed:string; deleted:boolean };
type StorageLike = Pick<Storage,'getItem'|'setItem'>;
const key=(tenant:string,revision:string)=>`chronosgraph-change-draft:${tenant}:${revision}`;
export function readDraft(storage:StorageLike,tenant:string,revision:string,path?:string):ChangeDraft|null {
  try {
    const selected=path||JSON.parse(storage.getItem(key(tenant,revision)+':latest')||'null');
    if(typeof selected!=='string'||!selected)return null;
    const value=JSON.parse(storage.getItem(key(tenant,revision)+':'+encodeURIComponent(selected))||'null');
    if(!value||value.revision!==revision||value.path!==selected||typeof value.path!=='string'||!value.path||value.path.startsWith('/')||value.path.split('/').includes('..')||!/^.+\.py$/.test(value.path)||! /^[0-9a-f]{64}$/.test(value.sha256)||typeof value.proposed!=='string'||value.proposed.length>1000000||typeof value.deleted!=='boolean')return null;
    return value;
  }catch{return null;}
}
export function saveDraft(storage:StorageLike,tenant:string,draft:ChangeDraft):boolean {
  try {storage.setItem(key(tenant,draft.revision)+':'+encodeURIComponent(draft.path),JSON.stringify(draft));storage.setItem(key(tenant,draft.revision)+':latest',JSON.stringify(draft.path));return true;}catch{return false;}
}
