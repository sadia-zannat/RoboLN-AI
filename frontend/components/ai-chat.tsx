'use client';
import {FormEvent,useEffect,useState} from 'react';
import {api} from '@/lib/api';
import {useProject} from './project-context';
import {Panel,AIWarning} from './ui';
import {AIProposals} from './ai-proposals';
import {RichAnswer} from './rich-answer';
import Image from 'next/image';
import type {Source} from '@/lib/workbench';
type Ref=Source&{source_id:string;index:number;page:number|null;text:string;citation:string};
type Message={selected_component_id?:string|null;id:string;question:string;answer:string;model:string;provider_id:string;sources:Ref[];created_at:string;image_included:boolean};
type Status={status:string;model:string;image_supported:boolean;message:string};
const suggestions=[
 'Explain my project in simple steps and identify what is missing.',
 'Review this design: which components and evidence do I still need?',
 'Show the next safe virtual assembly step and explain why.',
 'Summarize our previous decisions and the top three open questions.'
];
export function AIChat({selectedComponentId,selectedComponentName,buildContext=false}:{selectedComponentId?:string;selectedComponentName?:string;buildContext?:boolean}={}){
 const p=useProject();const base='/projects/'+p.id;
 const [status,setStatus]=useState<Status|null>(null);const [messages,setMessages]=useState<Message[]>([]);
 const [question,setQuestion]=useState('');const [consent,setConsent]=useState(false);const [consentBusy,setConsentBusy]=useState(false);const [imageConsent,setImageConsent]=useState(false);const [image,setImage]=useState<string|null>(null);const [imageName,setImageName]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [openAnswer,setOpenAnswer]=useState<string>('');
 useEffect(()=>{let active=true;Promise.all([api<Status>('/ai/status'),api<Message[]>(base+'/ai/messages'),api<Record<string,boolean>>('/consents')]).then(([s,m,c])=>{if(active){setStatus(s);setMessages(m);setConsent(!!c.cloud_ai);setOpenAnswer(m[m.length-1]?.id||'');}}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[base]);
 async function changeConsent(enabled:boolean){const previous=consent;setConsent(enabled);setConsentBusy(true);try{await api('/consents/cloud_ai',{method:'PUT',body:JSON.stringify({enabled})});}catch(e){setConsent(previous);setError(e instanceof Error?e.message:'Consent update failed');}finally{setConsentBusy(false);}}
 async function attach(file:File|undefined){if(!file)return;if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>3*1024*1024){setError('Choose a PNG, JPEG or WebP image up to 3 MiB.');return;}const r=new FileReader();r.onload=()=>{setImage(String(r.result));setImageName(file.name);setImageConsent(false);setError('');};r.readAsDataURL(file);}
 async function send(e:FormEvent){e.preventDefault();if(busy)return;setBusy(true);setError('');try{const m=await api<Message>(base+'/ai/ask',{method:'POST',body:JSON.stringify({copilot:buildContext,selected_component_id:selectedComponentId||null,question:question.trim(),consent,image_data_url:image,image_consent:imageConsent})});setMessages(xs=>[...xs,m]);setOpenAnswer(m.id);setQuestion('');setImage(null);setImageName('');setImageConsent(false);}catch(e){setError(e instanceof Error?e.message:'AI request failed');}finally{setBusy(false);}}
 return <Panel title="RoboLN AI engineering guide" aside={<span className="status-pill amber">{messages.some(m=>!!m.provider_id)?'META RESPONDED · REVIEW REQUIRED':status?.status||'CHECKING'}</span>} className="ai-guide">
  <p className="panel-description">Ask about your current project, parts, or the next assembly step. Answers are suggestions, not verified wiring instructions. {status?.model||'Meta Model API'}.</p>
  {selectedComponentId&&<div className="ai-context-label">Discussing: <strong>{selectedComponentName||selectedComponentId}</strong> · Project part</div>}
  {error&&<div role="alert" className="inline-error">{error}</div>}
  <div className="ai-guide-layout">
   <section className="ai-conversation" aria-label="AI conversation"><div className="ai-conversation-title"><strong>Conversation</strong><small>{messages.length} saved {messages.length===1?'answer':'answers'} · project-specific</small></div>
    {messages.length===0?<div className="ai-empty"><strong>No provider responses yet. Start with a project question</strong><p>The assistant can review your saved project, but cannot certify physical safety or change the 3D model without your approval.</p></div>:messages.map(m=><article className="ai-turn" key={m.id}>
     <div className="ai-question"><small>You · {new Date(m.created_at).toLocaleString()}</small><p>{m.question}</p>{m.image_included&&<small>Engineering image was shared with consent</small>}</div>
     <div className="ai-response"><button type="button" className="ai-answer-toggle" aria-expanded={openAnswer===m.id} onClick={()=>setOpenAnswer(v=>v===m.id?'':m.id)}><span><strong>Meta response</strong><small>{m.model} · Needs engineering review</small></span><span aria-hidden>{openAnswer===m.id?'−':'+'}</span></button>
      {openAnswer===m.id&&<div className="ai-answer-body"><RichAnswer text={m.answer}/><small>Provider ID: {m.provider_id||'not returned'}</small>{m.sources.length>0&&<details><summary>Source excerpts used ({m.sources.length})</summary>{m.sources.map((s,j)=><div className="source-excerpt" key={j}><a href={'/api'+base+'/sources/'+s.source_id+'/download'}>{s.filename} · v{s.version} · {s.page?`PDF page ${s.page} · `:''}chunk {s.index}</a><code>[{s.citation}]</code><p>{s.text}</p></div>)}</details>}{selectedComponentId&&m.selected_component_id===selectedComponentId&&<AIProposals componentId={selectedComponentId} messageId={m.id}/>}</div>}
     </div>
    </article>)}
   </section>
   <section className="ai-compose-section" aria-label="Ask Meta AI"><h3>Ask your next question</h3><p>Choose a starter or type your own question. Earlier messages are retained for context.</p><div className="ai-suggestions">{suggestions.map(s=><button key={s} type="button" className="ai-suggestion" disabled={busy} onClick={()=>setQuestion(s)}>{s}</button>)}</div>
    <form className="stack-form" onSubmit={send}><label>Ask a project question<textarea required minLength={3} maxLength={8000} rows={5} value={question} disabled={busy||p.archived||p.role==='viewer'} onChange={e=>setQuestion(e.target.value)} placeholder="e.g. Explain in simple words how to attach my camera to the controller in the 3D assembly."/></label>
     <label className="check-label"><input type="checkbox" checked={consent} disabled={consentBusy} onChange={e=>void changeConsent(e.target.checked)}/>Allow my project context and question to be sent to Meta Model API</label>
     {status?.image_supported&&<label>Optional engineering photo (PNG/JPEG/WebP, max 3 MiB)<input type="file" accept="image/png,image/jpeg,image/webp" disabled={busy} onChange={e=>void attach(e.target.files?.[0])}/></label>}
     {image&&<div className="image-attachment"><p>Selected: {imageName}. Not yet sent.</p><Image src={image} width={480} height={300} unoptimized alt="Preview of local engineering attachment"/><label className="check-label"><input type="checkbox" checked={imageConsent} onChange={e=>setImageConsent(e.target.checked)}/>I agree to share this image with Meta for unverified analysis</label><button type="button" className="button secondary" onClick={()=>{setImage(null);setImageName('');}}>Remove image</button></div>}
     <button className="button primary" disabled={busy||consentBusy||!consent||!question.trim()||!!image&&!imageConsent||p.archived||p.role==='viewer'}>{busy?'Receiving Meta response…':'Ask Meta AI'}</button>
    </form><AIWarning/></section>
  </div>
 </Panel>;
}
