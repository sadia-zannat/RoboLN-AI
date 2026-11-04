'use client';
import React,{createContext,useContext,useEffect,useState,useCallback} from 'react';
import {useRouter,usePathname} from 'next/navigation';
import {api,User} from '@/lib/api';

type AuthContext={user:User|null;loading:boolean;reload:()=>Promise<void>;setUser:(u:User|null)=>void};
const Context=createContext<AuthContext|null>(null);
export function useAuth(){const c=useContext(Context);if(!c)throw new Error('Auth provider required');return c;}
export function AuthProvider({children}:{children:React.ReactNode}){
  const [user,setUser]=useState<User|null>(null);
  const [loading,setLoading]=useState(true);
  const router=useRouter();const path=usePathname();
  const reload=useCallback(async()=>{try{setUser(await api<User>('/auth/me'));}catch{setUser(null);}finally{setLoading(false);}},[]);
  useEffect(()=>{let live=true;api<User>('/auth/me').then(u=>{if(live)setUser(u)}).catch(()=>{if(live)setUser(null)}).finally(()=>{if(live)setLoading(false)});return()=>{live=false};},[]);
  useEffect(()=>{if(!loading && !user && path!=='/login' && path!=='/register'){
    const destination=path.startsWith('/')?path:'/projects';
    router.replace('/login?next='+encodeURIComponent(destination));
  }},[user,loading,path,router]);
  if(loading)return <div className="loading-state" role="status">Opening RoboLN workspace…</div>;
  if(!user && path!=='/login' && path!=='/register')return <div className="loading-state">Redirecting to sign in…</div>;
  return <Context.Provider value={{user,loading,reload,setUser}}>{children}</Context.Provider>;
}
