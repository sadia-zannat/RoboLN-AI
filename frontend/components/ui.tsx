'use client';
import {ReactNode} from 'react';
import Link from 'next/link';
import {ArrowRight,Info} from 'lucide-react';
export function Heading({eyebrow,title,description,action}:{eyebrow?:string;title:string;description?:string;action?:ReactNode}){
 return <div className="page-heading"><div><div className="eyebrow">{eyebrow||'ROBOLN / WORKSPACE'}</div><h1 tabIndex={-1}>{title}</h1>{description&&<p>{description}</p>}</div>{action&&<div className="heading-action">{action}</div>}</div>;
}
export function Panel({title,children,aside,className=''}:{title?:string;children:ReactNode;aside?:ReactNode;className?:string}){
 return <section className={'panel '+className}>{title&&<div className="panel-header"><h2>{title}</h2>{aside}</div>}{children}</section>;
}
export function Unavailable({title,why,next}:{title:string;why:string;next?:string}){
 return <div className="unavailable-state"><div className="unavailable-icon"><Info size={23}/></div><h3>{title}</h3><p>{why}</p>{next&&<small>{next}</small>}<div className="availability-label">NOT YET AVAILABLE</div></div>;
}
export function ErrorView({title='Unable to load',message,back='/projects',retry}:{title?:string;message:string;back?:string;retry?:()=>void}){
 return <div className="error-state" role="alert"><h2>{title}</h2><p>{message}</p><div className="button-row">{retry&&<button className="button primary" onClick={retry}>Retry</button>}<Link className="button secondary" href={back}>Go to Projects <ArrowRight size={16}/></Link></div></div>;
}
export function Notice({children}:{children:ReactNode}){return <div className="notice" role="note"><Info size={17}/><span>{children}</span></div>;}
export function AIWarning(){return <p className="ai-warning">RoboLN AI can make mistakes. Verify important details before building or operating devices.</p>;}
