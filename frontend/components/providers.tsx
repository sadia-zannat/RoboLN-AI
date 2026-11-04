'use client';
import React from 'react';
import {AuthProvider} from './auth-context';
import {ThemeProvider} from './theme-provider';
import {AppShell} from './shell';
export function Providers({children}:{children:React.ReactNode}){return <ThemeProvider><AuthProvider><AppShell>{children}</AppShell></AuthProvider></ThemeProvider>;}
