'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {ClipboardCheck,ArrowLeft,Download,AlertTriangle} from 'lucide-react';
import {useProject} from '@/components/project-context';
import {api} from '@/lib/api';
import {Heading,Panel,Notice} from '@/components/ui';
import {BuildMemoryEvidence} from '@/components/build-memory-evidence';
import {Observations} from '@/components/observations';
import {projectUrl} from '@/lib/navigation';
type EvidenceEvent={id:string;description:string;event_type:string;at:string;evidence_kind:'ACCOUNT_ACTIVITY';physical_verification:'NOT_ASSESSED'};
type EvidenceResponse={events:EvidenceEvent[];state:string;physical_observations:number;message:string};
export default function Evidence(){
 const p=useProject();const [report,setReport]=useState<EvidenceResponse|null>(null);const [error,setError]=useState('');
 useEffect(()=>{let live=true;api<EvidenceResponse>('/projects/'+encodeURIComponent(p.id)+'/evidence')
  .then(r=>{if(live)setReport(r)}).catch(e=>{if(live)setError(e instanceof Error?e.message:'Could not retrieve evidence records')});return()=>{live=false};},[p.id]);
 function exportReport(){
  if(!report)return;
  const blob=new Blob([JSON.stringify({product:'RoboLN',project:p.id,source:'authenticated-project-audit',...report},null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='RoboLN-build-activity-'+p.id+'.json';a.click();URL.revokeObjectURL(url);
 }
 return <div className="content-container"><Heading eyebrow="PROJECT / TRACEABILITY" title="Evidence & reports" description="Saved activity is shown separately from physical observations. No activity event is a hardware PASS."/>
  {error&&<div role="alert" className="inline-error">{error}</div>}
  <Panel title="Project activity timeline" aside={<span className="role-tag">{report?report.events.length+' RECORDED EVENTS':'LOADING'}</span>}>
   {!report?<div className="loading-state">Loading actual recorded events…</div>:report.events.length===0?<div className="evidence-empty"><ClipboardCheck size={32}/><h2>No saved activity yet</h2><p>There are no recorded planning or project changes available to this workspace.</p></div>
   :<ol className="evidence-timeline">{report.events.map(e=><li key={e.id}><div className="evidence-event-marker"><ClipboardCheck size={16}/></div><div><strong>{e.description}</strong><small>{new Date(e.at).toLocaleString()} · Account activity only</small></div><span className="role-tag">NOT PHYSICAL</span></li>)}</ol>}
   <Notice><AlertTriangle size={17}/> Account events record software activity. Independent hardware checks must be recorded separately as user observations.</Notice>
  </Panel>
  <Observations/><BuildMemoryEvidence/>
  <div className="button-row top-gap"><Link href={projectUrl(p.id,'build')} className="button secondary"><ArrowLeft size={17}/>Back to Build</Link><button type="button" className="button secondary" disabled={!report} onClick={exportReport}><Download size={17}/>Download activity record</button></div>
 </div>;
}
