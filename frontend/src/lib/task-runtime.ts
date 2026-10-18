/** Harness, proposal decision and test verification are intentionally separate. */
export function runStatusLabel(status:string){return ({IDLE_NOT_SUCCESS:'Agent idle; verification pending',BOUND_NOT_COMPLETED:'Agent run bound; completion not established'} as Record<string,string>)[status]??'Agent status requires inspection';}
export function telemetryLabel(status:string){return status==='GAPS'?'Telemetry incomplete — missing sequence receipts':'Telemetry incomplete — end-to-end completeness not proven';}
export function usageBasisLabel(basis?:string){return basis==='OPENCODE_COMPLETED_STEP_PART'?'Completed step categories':basis==='LEGACY_MESSAGE_SNAPSHOTS_NOT_COMPLETED_STEP_TOTALS'?'Historical message snapshots — not a completed-step total':'Usage not yet observed';}
