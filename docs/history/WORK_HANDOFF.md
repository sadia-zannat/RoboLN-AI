# RoboLN — no-GitHub local handoff

**Use this exact source checkpoint. Do not restart or replace the foundation.** User explicitly requests manual GitHub push from VS Code after the website is finished. Never make a GitHub commit without a new explicit instruction.

## Highest-priority blocker: current frontend dependency checks

This runtime cannot resolve `registry.npmjs.org`. `npm ci --offline` gives `ENOTCACHED` for `zod-validation-error-4.0.2.tgz`. This is a missing npm tarball, **not proof of a broken Next.js application**. A fresh, normal online `npm ci` is required on the user's laptop or another *authorized* network-enabled runner. Do not bypass package integrity, disable TLS validation, download arbitrary copies from untrusted mirrors, or mislabel older GitHub CI as latest build.

### Windows PowerShell (from extracted `RoboLN` root)

Ensure Node 22 and Python 3.12 or 3.13 are installed; Python must be available to Playwright's backend process. Execute:

```powershell
py -3.12 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r backend/requirements.txt
cd backend
python -m alembic upgrade head
python -m pytest -q
cd ..\\frontend
npm ci --no-audit --no-fund
npm run lint
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

For local browser/API startup tests use a separate *test* SQLite DB via `ROBOLN_DATABASE_URL` to avoid test interactions with personal data. Playwright config starts local FastAPI and Next dev servers. Windows needs `python` and `alembic` available on PATH from the activated venv. Record actual test output; fix test failures and collect screenshots. The global bash-backed environment did not execute these commands to completion for the updated frontend.

If DNS fails on your laptop too, check normal browser access to `https://registry.npmjs.org/`, `npm config get registry`, local network DNS/firewall and any managed proxy. Do not rely on `npm cache clean` to conjure an uncached package.

## Current implementation

- FastAPI auth/RBAC/CSRF/database, Projects, hardware drafts, Settings and per-member drafts.
- Deterministic project family intake with versioned backend plans + UI; *not* a Meta AI model.
- Local consent-first getUserMedia and capture components, physically UNVERIFIED.
- Project audit activity timeline and real export, explicitly **not** physical evidence.

## What remains

1. Finish Phase 01 browser navigation/security/theme responsive gates on **this exact source**. Validate 1440x900, 768x1024, 390x844 and 320-wide, both themes and camera off by default. The existing browser tests include a potentially platform-dependent `Alt+ArrowLeft` keyboard shortcut; replace unsupported Chromium host hotkey expectations with navigation button and `page.goBack/goForward` tests without claiming an unexercised keyboard shortcut works.
2. Phase 02: authoritative source/document ingestion, safe manufacturer compatibility constraints, approved planning lifecycle, genuine Meta open-weight licensed model running and observed, code toolchain validation. Current deterministic draft is only groundwork.
3. Phase 03: source-reviewed real interactive 3D assets and project-scoped assembly constraints.
4. Phase 04: verified browser media permission + real camera, synchronized 3D, source-linked step candidates, UNKNOWN/HOLD decision logic.
5. Phase 05: authenticated real-device telemetry with correct timestamps/units and read-only truthful Digital Twin.
6. Phase 06: full QA, deployment, model/hardware/video evidence and final package. Physical tests only with hardware.

No GitHub write or production deployment occurred in this continuation. Keep failure logs and distinct dates for hackathon new work.
