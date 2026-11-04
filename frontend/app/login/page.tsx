import type {Metadata} from 'next';import {AuthForm} from '@/components/auth-form';
export const metadata:Metadata={title:'Sign in'};
export default function Login(){return <AuthForm register={false}/>}
