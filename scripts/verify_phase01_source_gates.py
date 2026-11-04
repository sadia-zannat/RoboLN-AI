"""Structural checks only: do not mistake these for Next.js or browser tests."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
read=lambda p:(root/p).read_text(encoding='utf-8')

routes=[
 'frontend/app/login/page.tsx', 'frontend/app/register/page.tsx',
 'frontend/app/projects/page.tsx', 'frontend/app/projects/[projectId]/page.tsx',
 'frontend/app/projects/[projectId]/workspace/plan/page.tsx',
 'frontend/app/projects/[projectId]/workspace/practice/page.tsx',
 'frontend/app/projects/[projectId]/workspace/build/page.tsx',
 'frontend/app/projects/[projectId]/twin/page.tsx',
 'frontend/app/projects/[projectId]/evidence/page.tsx',
 'frontend/app/settings/page.tsx',
]
checks={
 'all canonical routes present':all((root/p).is_file() for p in routes),
 'mobile project search real handler': 'setDrawer(false);setSearch(true)' in read('frontend/components/shell.tsx'),
 'home points to projects': 'href="/projects"' in read('frontend/components/shell.tsx'),
 'project draft guarded from loading race': 'disabled={!canEdit||!draftReady}' in read('frontend/app/projects/[projectId]/workspace/plan/page.tsx'),
 'explicit project isolation': 'key={p.id}' in read('frontend/app/projects/[projectId]/workspace/plan/page.tsx'),
 'browser tests in frontend package scope':(root/'frontend/tests/e2e/navigation.spec.ts').is_file() and not(root/'tests/e2e/navigation.spec.ts').exists(),
 'real browser back and forward exercised': 'await page.goBack()' in read('frontend/tests/e2e/navigation.spec.ts') and 'await page.goForward()' in read('frontend/tests/e2e/navigation.spec.ts'),
 'responsive workspace tabs configured': 'grid-template-columns:repeat(3,minmax(0,1fr))' in read('frontend/app/globals.css'),
 'development indicator disabled': 'devIndicators: false' in read('frontend/next.config.ts'),
 'dependency lockfile exists': (root/'frontend/package-lock.json').stat().st_size>100_000,
 'archived project overview controls are read-only': "const editable=p.role!=='viewer' && !p.archived" in read('frontend/app/projects/[projectId]/page.tsx'),
 'archived plan draft editor is read-only': "const canEdit=p.role!=='viewer'&&!p.archived" in read('frontend/app/projects/[projectId]/workspace/plan/page.tsx'),
 'malformed project path is handled': 'catch {return null;}' in read('frontend/lib/navigation.ts'),
 'navigation helper test exists':(root/'scripts/test_navigation_logic.cjs').is_file(),
}
for label,success in checks.items():
 print(f"{'PASS' if success else 'FAIL'} [SOURCE ONLY] {label}")
if not all(checks.values()):raise SystemExit(1)
print(f'All {len(checks)} source invariants passed. Runtime Next.js/Playwright is NOT tested here.')
