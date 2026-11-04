'use client';
import React,{createContext,useContext,useEffect,useState} from 'react';
type Mode='light'|'dark'|'system';
const Context=createContext<{mode:Mode;setMode:(mode:Mode)=>void}>({mode:'system',setMode:()=>{}});
export const useTheme=()=>useContext(Context);
function apply(mode:Mode){const actual=mode==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):mode;document.documentElement.dataset.theme=actual;document.documentElement.dataset.themePreference=mode;}
export function ThemeProvider({children}:{children:React.ReactNode}){
  const [mode,setCurrent]=useState<Mode>('system');
  useEffect(()=>{
    const stored=localStorage.getItem('roboln-theme');const initial=(stored==='light'||stored==='dark'||stored==='system')?stored:'system';queueMicrotask(()=>setCurrent(initial));apply(initial);
    const mq=matchMedia('(prefers-color-scheme: dark)');const update=()=>apply((localStorage.getItem('roboln-theme') as Mode)||'system');mq.addEventListener('change',update);return()=>mq.removeEventListener('change',update);
  },[]);
  const setMode=(value:Mode)=>{localStorage.setItem('roboln-theme',value);setCurrent(value);apply(value);};
  return <Context.Provider value={{mode,setMode}}>{children}</Context.Provider>;
}
