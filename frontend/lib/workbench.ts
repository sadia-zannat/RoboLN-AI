import {flagshipParts} from './component-library';
import type {VisualKey} from './component-library';
export type Part={visual?:VisualKey|'auto';rx?:number;ry?:number;rz?:number;visible?:boolean;parent_id?:string|null;geometry_provenance?:'PROCEDURAL_PROVISIONAL';id:string;name:string;kind:'board'|'sensor'|'actuator'|'chassis'|'wheel'|'other'|'motor'|'camera'|'power'|'mount';quantity:number;specification:string;source_id:string|null;x:number;y:number;z:number;state:'UNKNOWN'|'REVIEW'|'USER_CONFIRMED'|'HOLD'};
export type BuildTask={id:string;title:string;state:'TODO'|'REVIEW'|'DONE'};
export type Connection={start:string;end:string;state:'UNKNOWN'|'USER_CONFIRMED'|'DISCONNECTED'|'HOLD'};
export type Pin={component_id?:string|null;pin:string;signal:string;source_id:string|null};
export type WorkspaceData={requirements:string;constraints:string;software_notes:string;parts:Part[];tasks:BuildTask[];connections:Connection[];pins:Pin[]};
export type Workspace={revision:number;data:WorkspaceData;geometry:string;physical_verification:string};
export type Source={id:string;filename:string;version:number;sha256:string;chunks:number;size:number};
export const freshData=():WorkspaceData=>({requirements:'',constraints:'',software_notes:'',parts:[],tasks:[],connections:[],pins:[]});
export function roverDraft():WorkspaceData{
 const parts=flagshipParts();
 return {...freshData(),requirements:'Supervised rover inspection with calibrated moisture observations. No autonomous actuation.',parts,connections:[{start:'board',end:'sensor',state:'UNKNOWN'},{start:'board',end:'camera',state:'UNKNOWN'}],tasks:[{id:'identify',title:'Identify exact board and component revisions',state:'TODO'},{id:'datasheets',title:'Review datasheets, ratings, wiring and independent cutoff',state:'TODO'},{id:'calibrate',title:'Calibrate sensor against measured soil samples',state:'TODO'}]};
}
export function downloadJson(value:unknown,name:string){const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
