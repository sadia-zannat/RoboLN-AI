'use client';
import Link from 'next/link';import {usePathname} from 'next/navigation';
import {projectUrl} from '@/lib/navigation';
export function WorkspaceTabs({id}:{id:string}){const path=usePathname();return <nav aria-label="Workspace tabs" className="workspace-tabs">{(['plan','practice','build'] as const).map((t,i)=><Link key={t} href={projectUrl(id,t)} aria-current={path.endsWith('/'+t)?'page':undefined} className={path.endsWith('/'+t)?'selected':''}>{['Plan','Practice in 3D','Live Build'][i]}</Link>)}</nav>}
