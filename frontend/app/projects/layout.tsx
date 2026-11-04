import type { Metadata } from 'next';

// Declarative metadata prevents the root default title from winning a hydration race.
export const metadata: Metadata = { title: 'Projects' };

export default function ProjectsLayout({ children }: { children: React.ReactNode }) {
  return children;
}
