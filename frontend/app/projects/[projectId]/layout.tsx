import type { Metadata } from 'next';
export const metadata: Metadata = { title: 'Project workspace' };
import {ProjectGate} from '@/components/project-context';
export default function ProjectLayout({children}:{children:React.ReactNode}){return <ProjectGate>{children}</ProjectGate>;}
