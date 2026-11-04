'use client';
import React,{createContext,useContext,useEffect,useState} from 'react';
import {useParams} from 'next/navigation';
import {api,ApiError,Project} from '@/lib/api';
import {ErrorView} from './ui';
const Context=createContext<Project|null>(null);
export function useProject(){const v=useContext(Context);if(!v)throw new Error('Expected authorized project context');return v;}
export function ProjectGate({children}:{children:React.ReactNode}){
 const {projectId}=useParams<{projectId:string}>();
 return <ProjectScoped key={projectId} projectId={projectId}>{children}</ProjectScoped>;
}
function ProjectScoped({projectId,children}:{projectId:string;children:React.ReactNode}){
 const [project,setProject]=useState<Project|null>(null);const [error,setError]=useState<string>('');const [attempt,setAttempt]=useState(0);
 useEffect(()=>{let live=true;api<Project>('/projects/'+encodeURIComponent(projectId)).then(p=>{if(live){setProject(p);setError('');}}).catch((e:unknown)=>{if(live)setError(e instanceof ApiError&&e.status===404?'This project was not found or you do not have access.':e instanceof Error?e.message:'Unable to load project')});return()=>{live=false};},[projectId,attempt]);
 useEffect(()=>{const refresh=()=>setAttempt(v=>v+1);window.addEventListener('roboln:project-updated',refresh);return()=>window.removeEventListener('roboln:project-updated',refresh);},[]);
 if(error)return <ErrorView title="Project unavailable" message={error} retry={()=>{setError('');setProject(null);setAttempt(v=>v+1);}}/>;
 if(!project || project.id!==projectId)return <div className="loading-state">Checking project access…</div>;
 return <Context.Provider value={project}>{children}</Context.Provider>;
}
