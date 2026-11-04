# RoboLN local execution evidence — 2026-10-29

All results below are from the actual source in this archive. No unchecked gate is reported as passed.

| Gate | Result | Evidence |
| --- | --- | --- |
| Backend pytest | **19/19 PASS** | `logs/2026-10-29_local_execution.txt` |
| Alembic upgrade → downgrade → upgrade | **PASS** (new head `e239a8f21029`) | Same log; isolated SQLite |
| Existing Uvicorn HTTP smoke | **12 PASS** | Same log; real loopback TCP |
| New planning Uvicorn HTTP smoke | **7 PASS** | Same log; migrated independent SQLite, real loopback TCP |
| Navigation logic unit assertions | **17 PASS** | Same log; not browser |
| Phase 01 source invariants | **14 PASS** | Same log; source-only |
| TS/TSX syntax-only parsing | **34 files; zero parse errors** | Same log; not typecheck |
| `npm ci --offline` | **FAIL: ENOTCACHED** | `logs/npmci_confirm.txt` (`zod-validation-error-4.0.2.tgz`) |
| DNS `registry.npmjs.org` | **FAIL: resolution** | `logs/npm_registry_diagnostic.txt` |
| npm normal install / TypeScript strict / ESLint / Next production build **for this archive** | **NOT VERIFIED** | Mandatory deps missing in this runtime |
| Actual Chromium Playwright **for this archive** | **NOT EXECUTED** | npm package install blocked |
| Browser-based local camera permission/capture/stop | **NOT EXECUTED** | No actual camera test |
| Live Meta Llama / Muse inference | **NOT EXECUTED** | No licensed model weights/working provider |
| Physical power, circuit, motor, moisture, camera alignment, authenticated telemetry | **NOT EXECUTED** | No real device attached |

Historical GitHub CI passes of earlier code cannot certify this changed archive. The new authored browser scenarios in `frontend/tests/e2e/engineering-intake.spec.ts` are **not executed**. Stronger runtime claims require fresh evidence.
