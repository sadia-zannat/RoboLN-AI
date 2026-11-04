'use client';
import {FormEvent,useEffect,useState} from 'react';
import {AlertTriangle,CheckCircle2,ClipboardList,Download,Layers3,Plus} from 'lucide-react';
import {api,Project} from '@/lib/api';

type Family={key:string;name:string;risk_class:string};
type Document={family:string;title:string;goal:string;board:string|null;board_revision:string|null;context_version:number;mode:string;risk_class:string;candidate_parts:string[];questions:string[];steps:string[];blockers:string[];verification:string;disclaimer:string;model_provenance:{provider:string;meta_model_inference:boolean}};
type Plan={id:string;project_id:string;revision:number;context_version:number;status:string;created_at:string;document:Document};
const why='This creates a versioned, deterministic engineering draft. No AI inference, component compatibility, circuit wiring or physical checks are claimed.';
export function EngineeringIntake({project}:{project:Project}){
 const [families,setFamilies]=useState<Family[]>([]);
 const [family,setFamily]=useState('generic');
 const [goal,setGoal]=useState(project.goal||'');
 const [parts,setParts]=useState('');
 const [plans,setPlans]=useState<Plan[]>([]);
 const [chosen,setChosen]=useState<string>('');
 const [busy,setBusy]=useState(false);
 const [loading,setLoading]=useState(true);
 const [error,setError]=useState('');
 const canWrite=project.role!=='viewer'&&!project.archived;
 useEffect(()=>{
  let active=true;
  Promise.all([api<{families:Family[]}>('/planning/families'),api<{plans:Plan[]}>('/projects/'+encodeURIComponent(project.id)+'/engineering-plans')])
   .then(([f,p])=>{if(active){setFamilies(f.families);setPlans(p.plans);setChosen(p.plans[0]?.id||'');setLoading(false);}})
   .catch((e:unknown)=>{if(active){setError(e instanceof Error?e.message:'Could not load engineering plans');setLoading(false);}});
  return()=>{active=false;};
 },[project.id]);
 async function create(e:FormEvent){
  e.preventDefault();if(!canWrite||busy)return;
  setBusy(true);setError('');
  try{
   const p=await api<Plan>('/projects/'+encodeURIComponent(project.id)+'/engineering-plans',{
    method:'POST',body:JSON.stringify({family,goal,available_parts:parts})
   });
   setPlans(xs=>[p,...xs]);setChosen(p.id);
  }catch(e){setError(e instanceof Error?e.message:'Unable to create a safe draft');}
  finally{setBusy(false);}
 }
 const current=plans.find(p=>p.id===chosen) || plans[0];
 function download(){
  if(!current)return;
  const data=JSON.stringify({product:'RoboLN',kind:'unverified-engineering-draft',...current},null,2);
  const url=URL.createObjectURL(new Blob([data],{type:'application/json'}));
  const a=document.createElement('a');a.href=url;a.download='RoboLN-engineering-draft-revision-'+current.revision+'.json';a.click();
  URL.revokeObjectURL(url);
 }
 return <section className="panel engineering-intake" aria-label="Engineering intake and revisioned plans">
  <div className="panel-header"><h2><ClipboardList size={19} aria-hidden="true"/> Engineering planner</h2><span className="status-pill amber">NO AI INFERENCE</span></div>
  <p className="panel-description">{why}</p>
  {error&&<div role="alert" className="inline-error">{error}</div>}
  {loading?<p role="status">Loading saved plan revisions…</p>:<>
   <form className="stack-form" onSubmit={create}>
    <div className="form-grid">
     <label>Project family
      <select aria-label="Project family" value={family} onChange={e=>setFamily(e.target.value)} disabled={!canWrite}>
       {families.map(f=><option key={f.key} value={f.key}>{f.name}</option>)}
      </select>
     </label>
     <label>Available exact parts (optional)
      <input aria-label="Available exact parts" value={parts} maxLength={1600} placeholder="e.g. Board revision and sensor model; do not guess" disabled={!canWrite} onChange={e=>setParts(e.target.value)}/>
     </label>
    </div>
    <label>Engineering goal
     <textarea aria-label="Engineering goal" rows={3} value={goal} minLength={5} maxLength={1200} required disabled={!canWrite} onChange={e=>setGoal(e.target.value)} placeholder="Describe the measurable engineering task…"/>
    </label>
    <button type="submit" className="button primary" disabled={!canWrite||busy||goal.trim().length<5}><Plus size={16}/>{busy?'Saving…':'Generate reviewable draft'}</button>
    {project.archived&&<p role="status">Restore this archived project before creating another revision.</p>}
   </form>
   {current&&<div className="engineering-plan-result">
     <div className="engineering-plan-toolbar">
      <label>Saved revision
       <select aria-label="Saved plan revision" value={current.id} onChange={e=>setChosen(e.target.value)}>
        {plans.map(p=><option key={p.id} value={p.id}>Revision {p.revision} — {p.document.title}</option>)}
       </select>
      </label>
      <button className="button secondary" type="button" onClick={download}><Download size={17}/> Export draft</button>
     </div>
     <div className="engineering-plan-status"><Layers3 size={18}/><strong>{current.document.title}</strong><span>{current.document.mode.replaceAll('_',' ')}</span></div>
     {current.context_version!==project.context_version&&<p role="alert" className="inline-error">Hardware/project context changed after this plan was generated. Create a new revision before review.</p>}
     <p>{current.document.goal}</p>
     <div className="engineering-checks"><div><CheckCircle2 size={18}/><span>Saved: revision {current.revision}</span></div><div><AlertTriangle size={18}/><span>Hardware verification: NOT VERIFIED</span></div></div>
     <h3>Missing facts and safety blockers</h3><ul>{current.document.blockers.map((x,i)=><li key={i}>{x}</li>)}</ul>
     {current.document.candidate_parts.length>0&&<><h3>Candidate component categories</h3><ul>{current.document.candidate_parts.map((x,i)=><li key={i}>{x}</li>)}</ul></>}
     <h3>Review steps (not approved instructions)</h3><ol>{current.document.steps.map((x,i)=><li key={i}>{x}</li>)}</ol>
     <p className="engineering-disclaimer">{current.document.disclaimer}</p>
     <div className="notice">Physical actuation remains HOLD. Review this draft and record independent build evidence; software planning does not authorize physical actions.</div>
    </div>}
  </>}
 </section>;
}
