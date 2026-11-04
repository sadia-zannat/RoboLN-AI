import type {Part} from './workbench';

const within=(v:number,low:number,high:number)=>Math.max(low,Math.min(high,v));
/** Translate a selected part with logical children. Saved coordinates remain world-space;
 * no claim of mechanically validated attachment or rotational joint behavior. */
export function translateAssembly(parts:Part[],id:string,x:number,y:number,z:number):Part[]{
 const source=parts.find(p=>p.id===id);if(!source)return parts;
 if(![x,y,z].every(Number.isFinite))return parts;
 const follows=(candidate:Part)=>{
  let parent=candidate.parent_id;const seen=new Set<string>();
  while(parent&&!seen.has(parent)){
   if(parent===id)return true;
   seen.add(parent);parent=parts.find(p=>p.id===parent)?.parent_id||null;
  }
  return false;
 };
 const group=parts.filter(c=>c.id===id||follows(c));
 // Apply one bounded delta to the whole group. Clamping each child separately
 // collapses offsets when a linked part reaches a workspace boundary.
 const bounded=(axis:'x'|'y'|'z',value:number,low:number)=>within(value-source[axis],
  Math.max(...group.map(c=>low-c[axis])),Math.min(...group.map(c=>10-c[axis])));
 const delta={x:bounded('x',x,-10),y:bounded('y',y,0),z:bounded('z',z,-10)};
 const ids=new Set(group.map(c=>c.id));
 return parts.map(c=>ids.has(c.id)?{...c,x:c.x+delta.x,y:c.y+delta.y,z:c.z+delta.z}:c);
}
/** Excludes self/descendants as parents so a new saved assembly cannot have cycles. */
export function allowedParent(parts:Part[],partId:string,candidateId:string):boolean{
 if(partId===candidateId||!parts.some(p=>p.id===partId)||!parts.some(p=>p.id===candidateId))return false;
 let current:string|null|undefined=candidateId;const visited=new Set<string>();
 while(current&&!visited.has(current)){
  if(current===partId)return false;
  visited.add(current);current=parts.find(p=>p.id===current)?.parent_id;
 }
 return !current;
}

/** Stored poses remain world-space for backward compatibility. Parent edits apply
 * a rigid world transform to every descendant, including orientation. */
export function isAssemblyVisible(parts:Part[],id:string):boolean{
 let current=parts.find(p=>p.id===id);const seen=new Set<string>();
 while(current){if(seen.has(current.id)||current.visible===false)return false;seen.add(current.id);if(!current.parent_id)return true;current=parts.find(p=>p.id===current!.parent_id);}
 return false;
}
