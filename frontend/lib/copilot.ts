export type BuildStatus='NOT_STARTED'|'IN_PROGRESS'|'WAITING_FOR_EVIDENCE'|'NEEDS_MORE_EVIDENCE'|'NEEDS_REVIEW'|'USER_CONFIRMED'|'COMPLETED'|'BLOCKED';
export type Media={id:string;filename:string;step_id:string|null;equipment_id:string|null;sha256:string;media_type:string;created_at:string;origin:'USER_REPORTED'};
export type Equipment={id:string;name:string;manufacturer:string;model:string;category:string;quantity:number;description:string;known_specs:string;unknown_specs:string;proposed_function:string;status:string;bom_component_id:string|null;source_ids:string[];revision:number;photos:Media[]};
export type Progress={status:BuildStatus;notes:string;checks_confirmed:boolean;confirmed_at:string|null;completed_at:string|null;physical_verification:string};
export type Step={id:string;ordinal:number;objective:string;instruction:string;component_ids:string[];checks:string[];mistakes:string[];safety:string;evidence_required:boolean;progress:Progress};
export type BuildMessage={id:string;question:string;answer:string;model:string;provider_id:string;created_at:string;build_step_id:string|null;equipment_id:string|null;media_ids:string[];intent:string;image_included:boolean;sources:Array<{source_id:string;filename:string;version:number;page:number|null;text:string;citation:string}>};
export type BuildState={goal:string;plan_revision:number;plan_origin:string|null;steps:Step[];session:{revision:number;current_step_id:string|null;status:BuildStatus;experience:'beginner'|'advanced';selected_component_id:string|null;unresolved_issues:string[];workspace_revision:number;last_checkpoint:string|null};equipment:Equipment[];media:Media[];missing_parts:Array<{component_id:string;name:string;required:number;available:number;missing:number}>;messages:BuildMessage[];completed_steps:number;checkpoints:Array<{id:string;created_at:string;snapshot:Record<string,unknown>}>;next_action:string;physical_verification:string;states:BuildStatus[]};
export const statusLabel=(status:string)=>status.toLowerCase().replaceAll('_',' ').replace(/^./,s=>s.toUpperCase());
export const lines=(text:string)=>text.split('\n').map(s=>s.trim()).filter(Boolean);
export const activeStep=(build:BuildState)=>build.steps.find(s=>s.id===build.session.current_step_id)||build.steps[0];
export function speechText(text:string):string{return text.replace(/```[\s\S]*?```/g,'Code is available in the written instructions.').replace(/\[([^\]]+)\]\([^)]+\)/g,'$1').replace(/[#*_`>|]/g,'').replace(/\s+/g,' ').trim().slice(0,5000);}
export function validatePhoto(file:{type:string;size:number}):string|null{return !['image/png','image/jpeg','image/webp'].includes(file.type)?'Choose a PNG, JPEG or WebP image.':file.size<=0||file.size>3*1024*1024?'Each photo must contain 1 byte to 3 MiB.':null;}
export type StepDraft={objective:string;instruction:string;component_ids:string[];checks:string[];mistakes:string[];safety:string;evidence_required:boolean};
export function proposalSteps(answer:string):StepDraft[]|null{
 try{
  const parsed=JSON.parse(answer.trim().replace(/^```(?:json)?\s*|\s*```$/g,'')) as {steps?:unknown[]};
  if(!parsed||!Array.isArray(parsed.steps)||!parsed.steps.length||parsed.steps.length>60)return null;
  const result:StepDraft[]=[];
  for(const value of parsed.steps){
   if(!value||typeof value!=='object')return null;const s=value as Record<string,unknown>;
   if(typeof s.objective!=='string'||typeof s.instruction!=='string')return null;
   const array=(v:unknown):string[]|null=>v===undefined?[]:Array.isArray(v)&&v.every(x=>typeof x==='string')?v:null;
   const components=array(s.component_ids),checks=array(s.checks),mistakes=array(s.mistakes);
   if(!components||!checks||!mistakes||s.safety!==undefined&&typeof s.safety!=='string')return null;
   const flag=s.evidence_required;const normalized=String(flag).toLowerCase();
   const required=flag===undefined?false:typeof flag==='boolean'?flag:['1','true','t','yes','y','on'].includes(normalized)?true:['0','false','f','no','n','off'].includes(normalized)?false:null;
   if(required===null)return null;
   result.push({objective:s.objective,instruction:s.instruction,component_ids:components,checks,mistakes,safety:typeof s.safety==='string'?s.safety:'',evidence_required:required});
  }
  return result;
 }catch{return null;}
}
