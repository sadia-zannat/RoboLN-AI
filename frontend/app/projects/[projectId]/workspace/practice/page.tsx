'use client';
import {useProject} from '@/components/project-context';import {Heading} from '@/components/ui';import {WorkspaceTabs} from '@/components/workspace-tabs';import {AssemblyWorkspace} from '@/components/assembly-workspace';
export default function Practice(){const p=useProject();return <div className="content-container wide-content"><Heading eyebrow="WORKSPACE / VIRTUAL PRACTICE" title="Practice in 3D" description="Inspect your project components, practice layout, and record manual connection declarations."/><WorkspaceTabs id={p.id}/><AssemblyWorkspace/></div>;}
