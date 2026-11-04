export type Role = 'owner' | 'editor' | 'viewer';
export type User = {id:string; email:string; full_name:string; theme:'light'|'dark'|'system'};
export type Project = {id:string;name:string;description:string;goal:string;role:Role;archived:boolean;context_version:number;created_at:string};
export type Hardware = {id:string;board_model:string;board_revision:string;device_class:'MCU'|'SBC'|'OTHER';profile_review_state:string;pin_map:Record<string,string>;sensor_inventory:unknown[]} | null;
export class ApiError extends Error {constructor(public status:number, message:string){super(message);}}
function readCookie(name:string):string {
  if(typeof document==='undefined') return '';
  const part=document.cookie.split('; ').find(x=>x.startsWith(name+'='));
  return part ? decodeURIComponent(part.slice(name.length+1)) : '';
}
export async function api<T>(path:string,options:RequestInit={}):Promise<T> {
  const method=(options.method||'GET').toUpperCase();
  const mutation=!['GET','HEAD','OPTIONS'].includes(method);
  const headers=new Headers(options.headers);
  if(options.body && typeof options.body==='string') headers.set('Content-Type','application/json');
  if(mutation && !['/auth/login','/auth/register'].includes(path)) headers.set('x-csrf-token',readCookie('roboln_csrf'));
  let response:Response;const controller=new AbortController();const cancel=()=>controller.abort();options.signal?.addEventListener('abort',cancel,{once:true});if(options.signal?.aborted)controller.abort();const timer=setTimeout(()=>controller.abort(),path.includes('/ai/')?90000:15000);
  try {response=await fetch('/api'+path,{...options,signal:controller.signal,method,headers,credentials:'same-origin',cache:'no-store'});}
  catch(e) {if(options.signal?.aborted)throw e;throw new ApiError(0,controller.signal.aborted?'Backend request timed out. Inspect the API process.':'Backend is unreachable. Check that the RoboLN API is running.');}finally{clearTimeout(timer);options.signal?.removeEventListener('abort',cancel);}
  if(!response.ok){let message=response.statusText;
    try {const body=await response.json() as {detail?:string | {msg:string}[]};
      if(typeof body.detail==='string')message=body.detail;
      else if(Array.isArray(body.detail))message=body.detail.map(x=>x.msg).join(', ');
    }catch{} throw new ApiError(response.status,message || 'Request failed');}
  if(response.status===204)return undefined as T;
  return await response.json() as T;
}
