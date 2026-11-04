'use client';
import Link from 'next/link';
import {FormEvent,useState} from 'react';
import {useRouter} from 'next/navigation';
import {Layers,ArrowRight,ShieldCheck} from 'lucide-react';
import {api,User} from '@/lib/api';
import {useAuth} from './auth-context';
export function AuthForm({register}:{register:boolean}){
 const router=useRouter();const {setUser}=useAuth();
 const [email,setEmail]=useState('');const [fullName,setName]=useState('');const [password,setPassword]=useState('');
 const [error,setError]=useState('');const [busy,setBusy]=useState(false);
 async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{
  const u=await api<User>(register?'/auth/register':'/auth/login',{method:'POST',body:JSON.stringify(register?{email,password,full_name:fullName}:{email,password})});
  setUser(u);const next=new URLSearchParams(window.location.search).get('next');
  router.replace(next&&next.startsWith('/')&&!next.startsWith('//')&&!next.startsWith('/\\')?next:'/projects');
 }catch(e){setError(e instanceof Error?e.message:'Sign in failed');}finally{setBusy(false);}}
 return <main className="auth-screen"><div className="auth-aside"><Link href="/projects" className="auth-brand"><span className="brand-mark"><Layers size={26}/></span> RoboLN</Link><div className="auth-position"><span className="eyebrow">YOUR ENGINEERING WORKSPACE</span><h1>Build what you can <em>verify.</em></h1><p>Plan your machine, review the exact hardware, and keep a clear engineering record. No invented device results.</p><div className="auth-proof"><ShieldCheck size={21}/> Private project spaces and reviewed evidence</div></div><span className="auth-footer">Design. Practice. Build. Verify. Monitor.</span></div>
 <div className="auth-card-area"><div className="auth-card"><div className="auth-mobile-logo">RoboLN</div><div className="eyebrow">{register?'NEW ACCOUNT':'WELCOME BACK'}</div><h2>{register?'Create your account':'Sign in to RoboLN'}</h2><p>{register?'Start with a private, editable robotics project.':'Continue your work on actual projects and hardware profiles.'}</p><form onSubmit={submit} className="stack-form">
 {register&&<label>Full name<input autoComplete="name" placeholder="Your name" required minLength={1} maxLength={100} value={fullName} onChange={e=>setName(e.target.value)}/></label>}
 <label>Email address<input type="email" autoComplete="email" placeholder="you@example.com" required value={email} onChange={e=>setEmail(e.target.value)}/></label>
 <label>Password<input type="password" autoComplete={register?'new-password':'current-password'} placeholder={register?'At least 12 characters':'Your password'} minLength={12} required value={password} onChange={e=>setPassword(e.target.value)}/></label>
 {error&&<div className="inline-error" role="alert">{error}</div>}
 <button className="button primary wide" disabled={busy}>{busy?'Checking…':register?'Create account':'Sign in'}<ArrowRight size={18}/></button></form>
 <p className="auth-switch">{register?'Already have an account?':'New to RoboLN?'} <Link href={register?'/login':'/register'}>{register?'Sign in':'Create account'}</Link></p><div className="auth-security"><ShieldCheck size={17}/> Your device and camera are not connected by default.</div></div></div></main>;
}
