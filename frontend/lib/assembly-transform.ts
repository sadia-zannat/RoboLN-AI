import {Euler,Matrix4,Quaternion,Vector3,MathUtils} from 'three';
import type {Part,WorkspaceData} from './workbench';
import {translateAssembly} from './assembly-placement.ts';
function descendants(parts:Part[],id:string){return new Set(parts.filter(p=>{let at:string|null|undefined=p.id;const seen=new Set<string>();while(at&&!seen.has(at)){if(at===id)return true;seen.add(at);at=parts.find(c=>c.id===at)?.parent_id;}return false;}).map(p=>p.id));}
const pose=(p:Part)=>new Matrix4().compose(new Vector3(p.x,p.y,p.z),new Quaternion().setFromEuler(new Euler(MathUtils.degToRad(p.rx||0),MathUtils.degToRad(p.ry||0),MathUtils.degToRad(p.rz||0),'XYZ')),new Vector3(1,1,1));
/** Reject a rotation that would place a descendant outside backend coordinate bounds. */
export function transformAssembly(parts:Part[],id:string,patch:Partial<Part>):Part[]{
 const root=parts.find(p=>p.id===id);if(!root)return parts;
 const proposed={...root,...patch};
 if(![proposed.x,proposed.y,proposed.z,proposed.rx??0,proposed.ry??0,proposed.rz??0].every(Number.isFinite))return parts;
 if([proposed.rx??0,proposed.ry??0,proposed.rz??0].some(x=>Math.abs(x)>360))return parts;
 const moved=['x','y','z'].some(a=>a in patch)?translateAssembly(parts,id,proposed.x,proposed.y,proposed.z):parts;
 const source=moved.find(p=>p.id===id)!;
 const target={...source,...patch,x:source.x,y:source.y,z:source.z};
 if(!['rx','ry','rz'].some(a=>a in patch))return moved.map(p=>p.id===id?target:p);
 const delta=pose(target).multiply(pose(source).invert()),group=descendants(moved,id);
 const result=moved.map(p=>{if(p.id===id)return target;if(!group.has(p.id))return p;const position=new Vector3(),rotation=new Quaternion(),scale=new Vector3();delta.clone().multiply(pose(p)).decompose(position,rotation,scale);const e=new Euler().setFromQuaternion(rotation,'XYZ');return {...p,x:position.x,y:position.y,z:position.z,rx:MathUtils.radToDeg(e.x),ry:MathUtils.radToDeg(e.y),rz:MathUtils.radToDeg(e.z)};});
 if(result.some(p=>![p.x,p.y,p.z,p.rx||0,p.ry||0,p.rz||0].every(Number.isFinite)||p.x < -10-1e-7||p.x>10+1e-7||p.y < -1e-7||p.y>10+1e-7||p.z < -10-1e-7||p.z>10+1e-7))return parts;
 return result.map(p=>group.has(p.id)?({...p,x:Math.max(-10,Math.min(10,p.x)),y:Math.max(0,Math.min(10,p.y)),z:Math.max(-10,Math.min(10,p.z))}):p);
}
export type SceneHistory={past:WorkspaceData[];future:WorkspaceData[]};
export const emptyHistory=():SceneHistory=>({past:[],future:[]});
export function recordEdit(history:SceneHistory,current:WorkspaceData):SceneHistory{return {past:[...history.past,current].slice(-50),future:[]};}
export function undoEdit(history:SceneHistory,current:WorkspaceData):{history:SceneHistory;data:WorkspaceData}|null{const data=history.past.at(-1);return data?{history:{past:history.past.slice(0,-1),future:[current,...history.future]},data}:null;}
export function redoEdit(history:SceneHistory,current:WorkspaceData):{history:SceneHistory;data:WorkspaceData}|null{const data=history.future[0];return data?{history:{past:[...history.past,current],future:history.future.slice(1)},data}:null;}
