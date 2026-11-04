'use client';
import {ErrorView} from '@/components/ui';
export default function ErrorPage({reset}:{error:Error;reset:()=>void}){return <ErrorView title="Something went wrong" message="The page could not be rendered. Your projects remain stored in the backend." retry={reset}/>;}
