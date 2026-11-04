"use client";
import {Heading} from '@/components/ui';
import {LiveBuildCopilot} from '@/components/live-build-copilot';
export default function CopilotPage(){return <div className="content-container copilot-content"><Heading eyebrow="WORKSPACE / LIVE BUILD COPILOT" title="Live Build Copilot" description="Identify your equipment, follow a saved step, inspect a snapshot and resume where you stopped."/><LiveBuildCopilot/></div>;}
