/** Harness, proposal decision and test verification are intentionally separate. */
export function runStatusLabel(status:string){return ({IDLE_NOT_SUCCESS:'Agent idle; verification pending',BOUND_NOT_COMPLETED:'Agent run bound; completion not established'} as Record<string,string>)[status]??'Agent status requires inspection';}
export function telemetryLabel(status:string){return status==='GAPS'?'Telemetry incomplete — missing sequence receipts':'Telemetry incomplete — end-to-end completeness not proven';}
export function usageBasisLabel(basis?:string){return basis==='OPENCODE_COMPLETED_STEP_PART'?'Completed step categories':basis==='LEGACY_MESSAGE_SNAPSHOTS_NOT_COMPLETED_STEP_TOTALS'?'Historical message snapshots — not a completed-step total':'Usage not yet observed';}

/** Human decisions and harness telemetry are never inferred from a returned handoff. */
export function handoffStatusLabel(role:string,status:string,reportsJson:string){
  if(status==='RETURNED') {
    if(role==='REVIEWER') {
      let reports:unknown;try{reports=JSON.parse(reportsJson);}catch{return 'Reviewer returned · Inspect report';}
      const rows=Array.isArray(reports)?reports:[];
      const latest=[...rows].reverse().find(x=>x&&x.action==='RETURN');
      const report=typeof latest?.report==='string'?latest.report:'';
      if(/verdict:?\s+ACCEPTED\b/.test(report))return 'Agent review complete · Acceptance recorded';
      return 'Reviewer returned · Inspect verdict';
    }
    return 'Worker candidate returned · Review separate';
  }
  return ({CLAIMED:'Working under current claim',CORRECTION_REQUESTED:'Correction requested',CLOSED:'Handoff closed · Verification separate'} as Record<string,string>)[status]??'Awaiting claim';
}

export function declaredReturnReport(reportsJson:string):string {
  try {const rows=JSON.parse(reportsJson);if(!Array.isArray(rows))return '';const row=[...rows].reverse().find(x=>x?.action==='RETURN');return typeof row?.report==='string'?row.report:'';}catch{return '';}
}

export function isCurrentContextPack(pack:Record<string,unknown>|null,taskId:string,planId?:string,runPackId?:string):boolean {
 return !!pack && !!taskId && !!planId && pack.task_id===taskId && pack.plan_id===planId && (!runPackId || pack.id===runPackId);
}
