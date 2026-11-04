'use client';
import Link from 'next/link';
import {usePathname,useRouter} from 'next/navigation';
import {useEffect,useMemo,useState} from 'react';
import {ArrowLeft,ArrowRight,House,FolderKanban,Layers,RadioTower,ClipboardCheck,Settings,Sun,Moon,Monitor,LogOut,Menu,X,ChevronRight,Search,Wrench} from 'lucide-react';
import {useAuth} from './auth-context';
import {useTheme} from './theme-provider';
import {useNavHistory} from './nav-history';
import {api,Project} from '@/lib/api';
import {projectIdFromPath,projectUrl} from '@/lib/navigation';

const menu=[{label:'Projects',key:'projects',Icon:FolderKanban},{label:'Workspace',key:'plan',Icon:Layers},{label:'Build Copilot',key:'copilot',Icon:Wrench},{label:'Digital Twin',key:'twin',Icon:RadioTower},{label:'Evidence',key:'evidence',Icon:ClipboardCheck}] as const;
const pageSegment=(path:string)=>path.includes('/workspace/copilot')?'Build Copilot':path.includes('/workspace/practice')?'Practice in 3D':path.includes('/workspace/build')?'Live Build':path.includes('/workspace/plan')?'Plan':path.endsWith('/twin')?'Digital Twin':path.endsWith('/evidence')?'Evidence':path==='/settings'?'Settings':'Project overview';
function Navigation({pid,path,onNavigate}:{pid:string|null;path:string;onNavigate?:()=>void}){
 return <nav aria-label="Main navigation" className="primary-links">{menu.map(({label,key,Icon})=>{
 const href=key==='projects'?'/projects':pid?projectUrl(pid,key):null;
 const active=key==='projects'?path==='/projects':key==='plan'?path.includes('/workspace/')&&!path.endsWith('/copilot'):path.endsWith('/'+key);
 return href?<Link onClick={onNavigate} key={key} href={href} className={'nav-link '+(active?'active':'')} aria-current={active?'page':undefined}><Icon aria-hidden="true" size={19}/><span>{label}</span></Link>
 :<span key={key} className="nav-link unavailable" title="Open a project to use this section" aria-disabled="true"><Icon size={19}/><span>{label}</span></span>;
 })}</nav>;
}
export function AppShell({children}:{children:React.ReactNode}){
 const {user,setUser}=useAuth();const {mode,setMode}=useTheme();const path=usePathname();const router=useRouter();
 const nav=useNavHistory();const pid=projectIdFromPath(path);
 const [projectCache,setProjectCache]=useState<{userId:string;items:Project[]}|null>(null);const projects=projectCache && user && projectCache.userId===user.id?projectCache.items:[];const [drawer,setDrawer]=useState(false);const [search,setSearch]=useState(false);const [term,setTerm]=useState('');const [logoutError,setLogoutError]=useState('');
 useEffect(()=>{let live=true;if(user)api<Project[]>('/projects').then(items=>{if(live)setProjectCache({userId:user.id,items})}).catch(()=>{if(live)setProjectCache({userId:user.id,items:[]})});return()=>{live=false};},[user,path]);
 useEffect(()=>{queueMicrotask(()=>{setDrawer(false);setSearch(false);});},[path]);
 useEffect(()=>{
  const titles:Record<string,string>={'/projects':'Projects','/settings':'Settings','/login':'Sign in','/register':'Create account'};
  const section=titles[path]||(pid?pageSegment(path):'Not found');
  document.title=`${section} | RoboLN`;
  const heading=document.querySelector<HTMLElement>('.main-area h1');
  if(heading){heading.focus({preventScroll:true});}
 },[path,pid]);
 useEffect(()=>{
  if(!drawer&&!search)return;
  const previous=document.activeElement as HTMLElement|null;
  const dialog=document.querySelector<HTMLElement>('[role="dialog"]');
  const elements=()=>Array.from(dialog?.querySelectorAll<HTMLElement>('button:not([disabled]),a[href],input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex="0"]')||[]).filter(e=>e.getClientRects().length>0);
  const first=dialog?.querySelector<HTMLElement>('input')||elements()[0];first?.focus();
  const onKey=(event:KeyboardEvent)=>{
   if(event.key==='Escape'){setDrawer(false);setSearch(false);}
   if(event.key==='Tab'){const items=elements();if(!items.length)return;const first=items[0],last=items[items.length-1];
    if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
    else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
   }
  };
  window.addEventListener('keydown',onKey);
  return()=>{window.removeEventListener('keydown',onKey);if(previous?.isConnected)previous.focus();};
 },[drawer,search]);
 const active=projects.find(p=>p.id===pid);
 const crumbs=useMemo(()=>{
  if(path==='/projects')return [{label:'Projects',href:'/projects'}];
  if(path==='/settings')return [{label:'Projects',href:'/projects'},{label:'Settings',href:'/settings'}];
  const base=[{label:'Projects',href:'/projects'}];
  if(!pid)return base;
  base.push({label:active?.name||'Project',href:projectUrl(pid)});
  if(path.includes('/workspace/')){base.push({label:'Workspace',href:projectUrl(pid,'plan')});const name=pageSegment(path);base.push({label:name,href:path});}
  else if(path.endsWith('/twin')||path.endsWith('/evidence'))base.push({label:pageSegment(path),href:path});
  return base;
 },[active?.name,path,pid]);
 if(path==='/login'||path==='/register'||!user)return <>{children}</>;
 const signout=async()=>{try{await api('/auth/logout',{method:'POST'});setProjectCache(null);setUser(null);router.replace('/login');}catch(e){setLogoutError(e instanceof Error?e.message:'Could not sign out');}};
 const switchProject=(id:string)=>{if(id)router.push(projectUrl(id,'plan'));};
 return <div className="app-frame"><a className="skip-link" href="#main-content">Skip to content</a>
  <aside className="sidebar">
   <Link href="/projects" className="brand" aria-label="RoboLN — Go to Projects"><span className="brand-mark"><Layers size={23}/></span><span><strong>RoboLN</strong><small>ENGINEERING WORKSPACE</small></span></Link>
   <div className="side-caption">WORKSPACE</div>
   <Navigation pid={pid} path={path}/>
   <div className="sidebar-spacer"/>
   <div className="side-note"><div className="presence-dot"/> Engineering workspace<br/><small>Provider and device status shown in each project</small></div>
   <Link className="nav-link settings-link" href="/settings"><Settings size={19}/>Settings</Link>
  </aside>
  <div className="work-area">
   <header className="topbar">
    <button className="icon-button mobile-menu" aria-label="Open navigation" onClick={()=>setDrawer(true)}><Menu size={21}/></button>
    <div className="history-controls">
     <button className="icon-button" onClick={nav.back} aria-label="Back" title="Go back (or logical parent)"><ArrowLeft size={19}/></button>
     <button className="icon-button" onClick={nav.forward} disabled={!nav.canForward} aria-label={nav.canForward?'Forward':'Forward unavailable — no next history entry'} title={nav.canForward?'Go forward':'No forward history'}><ArrowRight size={19}/></button>
     <Link className="icon-button" href="/projects" aria-label="Home — Projects" title="Projects home"><House size={19}/></Link>
    </div>
    <nav className="breadcrumbs" aria-label="Breadcrumbs">{crumbs.map((crumb,i)=><span key={crumb.href+'-'+i} className="crumb">{i>0&&<ChevronRight size={15} aria-hidden/>}{i===crumbs.length-1?<span aria-current="page" className="current-crumb">{crumb.label}</span>:<Link href={crumb.href}>{crumb.label}</Link>}</span>)}</nav>
    <div className="top-actions">
     {projects.length>0&&<select className="project-picker" aria-label="Switch project" value={pid||''} onChange={e=>switchProject(e.target.value)}><option value="" disabled>Choose project</option>{projects.filter(p=>!p.archived).map(p=><option key={p.id} value={p.id}>{p.name} · {p.id.slice(0,6)}</option>)}</select>}
     <button className="icon-button desktop-only" aria-label="Search your projects" title="Search projects" onClick={()=>setSearch(true)}><Search size={19}/></button>
     <button className="icon-button" aria-label="Change theme" title={'Theme: '+mode} onClick={()=>setMode(mode==='system'?'light':mode==='light'?'dark':'system')}>{mode==='light'?<Sun size={19}/>:mode==='dark'?<Moon size={19}/>:<Monitor size={19}/>}</button>
     <Link className="icon-button desktop-only" href="/settings" aria-label="Settings"><Settings size={19}/></Link>
     <button className="avatar-button" onClick={signout} title={'Sign out '+user.email} aria-label="Sign out"><LogOut size={18}/></button>
    </div>
   </header>
   {logoutError&&<div role="alert" className="inline-error">{logoutError}</div>}
   <main id="main-content" className="main-area" tabIndex={-1}>{children}</main>
   <footer className="footer">RoboLN • Design. Practice. Build. Verify. Monitor. <span>Local workspace</span></footer>
  </div>
  <nav className="mobile-bottom" aria-label="Mobile navigation"><Navigation pid={pid} path={path}/></nav>
  {drawer&&<div className="drawer-backdrop" onClick={()=>setDrawer(false)}><div className="drawer" role="dialog" aria-modal="true" aria-label="Navigation" onClick={e=>e.stopPropagation()}><div className="drawer-top"><strong>RoboLN</strong><button className="icon-button" onClick={()=>setDrawer(false)} aria-label="Close navigation"><X/></button></div><Navigation pid={pid} path={path} onNavigate={()=>setDrawer(false)}/><button type="button" className="nav-link" aria-label="Search your projects" onClick={()=>{setDrawer(false);setSearch(true);}}><Search size={19}/>Search projects</button><Link href="/settings" className="nav-link" onClick={()=>setDrawer(false)}><Settings size={19}/>Settings</Link><button className="nav-link" onClick={signout}><LogOut size={19}/>Sign out</button></div></div>}
  {search&&<div className="drawer-backdrop" onClick={()=>setSearch(false)}><div className="search-dialog" role="dialog" aria-modal="true" aria-label="Find project" onClick={e=>e.stopPropagation()}><div className="drawer-top"><h2>Find a project</h2><button className="icon-button" onClick={()=>setSearch(false)} aria-label="Close search"><X/></button></div><label htmlFor="project-search-modal">Search by name</label><input id="project-search-modal" autoFocus value={term} onChange={e=>setTerm(e.target.value)} placeholder="Project name…"/><div className="search-results">{projects.filter(p=>p.name.toLowerCase().includes(term.toLowerCase())).map(p=><Link key={p.id} href={projectUrl(p.id)} onClick={()=>setSearch(false)}>{p.name}<span>{p.id.slice(0,8)}</span></Link>)}</div></div></div>}
 </div>;
}
