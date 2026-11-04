> **ARCHIVED BASELINE — not this UX-modified release.** The results below were measured on the earlier recovered build. For the new archive, read [UPDATED_RELEASE_TEST_REPORT.md](UPDATED_RELEASE_TEST_REPORT.md). Its browser, build, and locked-environment checks are still pending.

# RoboLN Ultimate recovery test report — October 30, 2026

This report describes the recovered consolidated source, not the removed workspace. See `docs/RECOVERY_STATUS.md`. The earlier 78-backend/96-browser results cannot certify this package; their source/log tree was removed by workspace maintenance. Current results below are from actual execution.

| Check | Current result |
|---|---|
| Python 3.12 clean environment + requirements.lock | PASS |
| pytest -q | **74 passed**, 1 Starlette/httpx test-client deprecation warning |
| Frontend npm ci | PASS |
| ESLint, zero warnings | PASS |
| TypeScript | PASS |
| Next.js production build | PASS |
| Node proxy/recorded-state unit tests | **10 passed, 0 failed** |
| Browser E2E, four viewports, 100 cases | **100 passed, 0 failed, 0 flaky** in 6.6 minutes |
| Four-revision migration roundtrip | PASS |
| Old-head data upgrade/backfill/downgrade/re-upgrade | PASS; users/member/device/chat/packet preserved; one normalized reading |
| Real local TCP auth/security smoke | **12 checks PASS** |
| Real local TCP planning smoke | **7 checks PASS** |
| Real local TCP workbench + executed Python adapter | **18 checks PASS**, explicitly SIMULATION |
| Pure navigation helper | **17 assertions PASS** |
| pip check | PASS |
| Dependency advisory audit | **0 known vulnerabilities reported** by npm audit and pip-audit against the pinned Python lock |
| Source archive CRC / extraction / checksum manifest | PASS; final extraction and every checksum checked after packaging |

Commands: `python -m pip install -r backend/requirements.lock`; from backend `python -m pytest -q`; frontend `npm ci`, `npm run lint`, `npm run typecheck`, `npm run build`, `npm run test:unit`, `npm run test:e2e`; root `python scripts/verify_migration.py`, `python scripts/verify_industrial_migration.py`, `python scripts/smoke_http.py`, `python scripts/smoke_planning_http.py`, `python scripts/smoke_workbench_http.py`, `node scripts/test_navigation_logic.cjs`.

Browser profiles are 1440×900, 768×1024, 390×844 and 320×700. The runner uses one worker, per-case timeout 60 seconds and an outer 15-minute bound. Some inherited mobile-only cases return early on wide viewports; case totals are not counts of unique workflows. The first recovery attempt was interrupted after missing SwiftShader libraries caused explicit renderer-unavailable failures. Extraction had stopped at a file-ownership error. The libraries were restored with ownership preservation disabled; the complete rerun passed all 100 cases. This setup failure was not hidden or counted as success.

Coverage includes auth/RBAC/CSRF/isolation, saved engineering and source data, consent/provider failures, selected AI context and explicitly reviewed specification changes, assembly transforms/hierarchy/pins/visibility/revisions, analytic deterministic simulation, sensor mappings and independent stale state, simulation exclusion, recorded atomic pose/angle units, real local TCP proxy resets/timeouts/status forwarding, camera/evidence, navigation/refresh, original telemetry/control routes and BOM deletion cleanup. Serious/critical automated accessibility and viewport checks run on integrated routes and populated assembly; this is not manual WCAG certification.

Provider success tests use an explicit mocked HTTP transport. No real Meta key, catalog or text/image inference was verified. Browser capture uses an explicitly synthetic MediaStream plus denial/upload tests; no physical webcam was verified here. Telemetry fixtures, including software tests enrolled with LIVE_REAL to test that contract, are not physical measurements. The executed Python transport uses SIMULATION. No real Raspberry Pi/ESP32 calibration or physical actuator test occurred.

Detailed geometry is project-authored PROCEDURAL_PROVISIONAL, not manufacturer CAD, verified dimensions or electrical/physical safety. The simulation is constant-twist planar kinematics, not validated collision/traction/torque/navigation. Physical coordinate frames/scales require commissioning. Stale/revoked channels freeze recorded values; they do not extrapolate. Image guidance remains REVIEW. User PASS requires independent-test attestation. Every control approval remains HOLD_NO_EXECUTOR.

Execution was Linux, Python 3.12.14, Node 24.22.1, npm 11.9.0, Next 16.4.3 and headless Chromium 153 with ANGLE/SwiftShader. Windows instructions are supplied but not Windows-executed. Docker/Render/PostgreSQL/TLS/load/availability commissioning remains external. No push/deployment/submission occurred.

The exact previous Windows ECONNRESET cause remains unconfirmed without its matching backend trace. Explicit fresh-socket proxy and serialized/cancelable polling fixes are included and locally fault-tested. See `docs/ECONNRESET_DIAGNOSIS.md`.

The source ZIP excludes private environment files, secrets, databases, node_modules, build caches, virtual environments, browser binaries, screenshots and traces. All asset geometry and tests are real source. Run `python scripts/verify_manifest.py` after extraction.


## Current outcome and corrections

All 100 browser cases completed with no retries, skipped cases or flaky outcomes reported by Playwright. Inherited mobile-only cases that return early on wide profiles are still counted as declared cases. The first driver-deficient run was interrupted and is preserved separately as preliminary failure evidence. The initial new role test used POST instead of the existing PUT membership endpoint; its test fixture was corrected and the full backend rerun passed 74/74. A leftover unused rover helper triggered lint during restoration; it was removed and zero-warning lint passed. No authentication or feature was removed to make tests pass.

Windows setup, API-key/camera requirements, hardware commissioning and deployment actions are documented in `docs/WINDOWS_VSCODE_RUN.md` and `docs/EXTERNAL_INTEGRATION_CHECKLIST.md`. Real provider inference/native camera/hardware/cloud remain externally unverified; validated physical actuation/CAD/dynamics/automatic camera alignment are not implemented. Old industrial bytes lost to maintenance cannot be recovered exactly; this release is the verified restored implementation described in recovery provenance.

Runtime/test/config fingerprints: **119 files**, aggregate SHA-256 `168073f84a7e13dd3fdf9f3e638ade4214b7c1f74b56a3e98fd1ab5bfb0d4151`. Final extracted files are compared with this tested source.
