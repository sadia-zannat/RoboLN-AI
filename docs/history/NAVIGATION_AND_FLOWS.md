# Implemented route contract and flows — Phase 01 (source, not browser verified)

- `/` → `/projects` server redirect.
- `/register`, `/login?next=...` → account registration/login; password ≥12 characters, session HttpOnly, safe internal return redirect.
- `/projects` → authorized list, search, create, archive and delete (role owner). Main logo/Home.
- `/projects/:id` → authorized context detail; owner/editor can edit and draft hardware profile; owner can grant viewer/editor to existing registered member.
- `/projects/:id/workspace/plan` → source-independent saved per-user per-project prompt draft; no live AI call. Contextual Sources/BOM/TaskPack/Code cards truthfully unavailable.
- `/projects/:id/workspace/practice` → no fake CAD, Phase 03 capability disclosure.
- `/projects/:id/workspace/build` → Photo/Live Text/3D Voice selector without camera or mic capture; Phase 04 disclosure.
- `/projects/:id/twin` → NOT_ENROLLED; no fake metrics.
- `/projects/:id/evidence` → empty real evidence timeline, future export disabled with reason.
- `/settings` → name/profile, light/dark/system, consent toggles, JSON account export and irreversible account deletion.
- Invalid Next.js route → `not-found.tsx`; unknown/inaccessible project → non-leaking project not found; viewer write → server 403; unauthenticated request → server 401 + app login redirect.

**Four top-level destinations:** Projects, Workspace, Digital Twin, Evidence. Settings/Logout/Search/Theme in global header or navigation drawer. On 320–767px phone use bottom four-item navigation. On tablet use menu drawer. On desktop sidebar. Browser native Back/Forward and direct-link logical parent implemented in `components/nav-history.tsx`, BUT NOT BROWSER VERIFIED; do not call navigation gate PASS.

All future-stage UI actions are either functional navigation to a truthful unavailable page, or explicit disabled controls with a reason. No automatic camera/mic or device actuation.
