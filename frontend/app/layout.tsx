import type {Metadata} from 'next';
import './globals.css';
import {Providers} from '@/components/providers';
export const metadata:Metadata={title:{default:'RoboLN | Engineering Workspace',template:'%s | RoboLN'},description:'Your AI Engineering Copilot for Building Real Machines. Design. Practice. Build. Verify. Monitor.'};
const initialTheme=`(function(){try{var m=localStorage.getItem('roboln-theme')||'system';var t=m==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):m;document.documentElement.dataset.theme=t;document.documentElement.dataset.themePreference=m;}catch(e){document.documentElement.dataset.theme='light';}})()`;
export default function RootLayout({children}:{children:React.ReactNode}){
 return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{__html:initialTheme}} /></head><body><Providers>{children}</Providers></body></html>;
}
