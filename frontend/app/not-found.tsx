import Link from 'next/link';
export default function NotFound(){return <main className="standalone-state"><p className="eyebrow">404 · NOT FOUND</p><h1>That page doesn’t exist</h1><p>The link may be incorrect or the page was moved.</p><Link href="/projects" className="button primary">Go to Projects</Link></main>}
