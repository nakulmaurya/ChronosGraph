import { API_BASE, ApiError } from './api';
/** Explicit loopback operator intent; not authentication or a remote-host boundary. */
export async function operatorRequest<T>(path:string,body:unknown,signal:AbortSignal):Promise<T>{
  const response=await fetch(`${API_BASE}${path}`,{method:'POST',signal:AbortSignal.any([signal,AbortSignal.timeout(65000)]),
    headers:{'Content-Type':'application/json','X-ChronosGraph-Action':'proposal-operator'},body:JSON.stringify(body),cache:'no-store'});
  const payload=await response.json();
  if(!response.ok)throw new ApiError(`HTTP ${response.status}: ${typeof payload.detail==='string'?payload.detail:JSON.stringify(payload.detail)}`,response.status);
  return payload as T;
}
