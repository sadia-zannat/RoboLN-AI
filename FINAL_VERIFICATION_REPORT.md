# RoboLN Live Build Copilot — actual release verification

Release: `RoboLN_AI_LIVE_BUILD_COPILOT_ULTIMATE_FINAL_2026.zip` · November 4, 2026.

**Verdict:** This is a real source/database/API/UI upgrade of the supplied project. Pinned backend, frontend unit/lint/type/build, real production HTTP integration, a real backend restart and migration preservation checks passed. **Browser suites were blocked before page creation; native camera/audio, live Meta and physical hardware are not verified.** No complete UI/production-readiness claim is made.

## Source and implemented work

Input was the attached `RoboLN_AI_FINAL_VERIFIED_RELEASE_2026(6).zip`, 414,670 bytes, SHA-256 `043121a446f169ebc53c99eb1af66ec6ae987eaaf018eb1c51868cae9a7012f0`. This is the actual uploaded file, despite the prompt's `(5)` spelling. Its 225 entries were extracted directly. No restart from an earlier archive or replacement scaffold occurred. Original application modules, lockfiles, tests and deployment configuration were preserved and extended. Prior verification records are archived under `docs/history/pre-copilot-verification/`; prior root reports are retained as `docs/history/PRE_COPILOT_*`.

Actual additions include seven persistent tables, migration `c17a90bd4201`, 12 project-scoped inventory/build/media/session/plan endpoints, step/equipment/image context in the preserved Meta connector, reviewed provider plan proposals, older private conversation pagination, Evidence/export integration, a dedicated `/workspace/copilot` interface, English browser speech controls, inventory/photos/BOM tools, and upgraded 3D gizmos/transforms/history. Read `docs/FEATURE_CHECKLIST.md` for exact scope.

Shared inventory/plans/photos require project authorization; private progress/checkpoints/messages require the account. All eight build states are persistent. Step completion remains USER REPORTED and physical verification remains NOT VERIFIED. No physical executor or autonomous actuation was added.

## Actual executed results

Evidence paths below are under `verification/` unless stated otherwise.

| Check | Result | Evidence |
|---|---|---|
| Pinned Python installation/consistency | PASS in isolated Python 3.12 environment; pypdf 6.21.4; no compatibility shims | `python-lock-install.txt`, `python-integrity.txt`, `installed-python.txt` |
| Baseline regression before completing Copilot | 81 passed | `preserved-baseline.txt` |
| Final full backend suite | **105 passed**, 1 upstream Starlette/httpx deprecation warning | `backend-pytest.txt`, `backend-junit.xml` |
| Frontend `npm ci` with existing lock | PASS, 452 packages installed | `frontend-clean-install.txt` |
| Frontend Node unit suite | **22 passed**, 0 failed | `frontend-unit-tests.txt` |
| ESLint with zero warnings | PASS | `frontend-eslint.txt` |
| TypeScript `tsc --noEmit` | PASS | `frontend-typecheck.txt` |
| Next.js production build | PASS, including Copilot route | `frontend-production-build.txt` |
| Existing production Next → FastAPI → SQLite integration | **41 HTTP checks passed** | `http-production-fullstack.txt` |
| New Copilot production HTTP flow | **48 HTTP checks passed**, including actual backend termination/restart | `copilot-production-http.txt` |
| Real TCP auth / planning / workbench-adapter regressions | **12 / 7 / 18 checks passed**; adapter packet explicitly SIMULATION | `http-auth-smoke.txt`, `http-planning-smoke.txt`, `http-workbench-adapter-smoke.txt` |
| Five-revision migration roundtrip | PASS | `migration-roundtrip.txt` |
| Existing industrial data preservation | PASS | `industrial-migration-preservation.txt` |
| Copilot old-head upgrade / downgrade / re-upgrade | PASS; old chat and dependent change proposal retained; seven tables and backfilled defaults checked | `copilot-migration-preservation.txt` |
| Pure navigation helpers | 17 assertions passed; not browser E2E | `navigation-assertions.txt` |
| Static color contrast | Corrected dark primary action white-text ratio 2.89 → **5.83**; light primary 5.83; muted text 8.04 dark / 5.99 light | `color-contrast.json`; not a full rendered WCAG audit |
| Regular Playwright suite | 124 collected; **0 passed, 1 launch failure, 123 not run** after fail-fast | `browser-test-collection.txt`, `browser-e2e.txt`, `playwright-results.json` |
| Explicit mock-provider/media/speech browser suite | 4 collected; **0 passed, 1 launch failure, 3 not run** after fail-fast | `copilot-browser-collection.txt`, `copilot-mock-browser.txt`, `copilot-mock-browser-results.json` |
| Final source packaging | CRC, safe extraction, complete SHA-256 manifest and source fingerprint comparison checked before delivery | root `RELEASE_SHA256SUMS.txt`, `verification/source-fingerprints.json`, `verification/release-provenance.json` |

Tests/assertions above are different layers and are not unique-user-journey counts. A successful HTTP HTML response is not proof of browser rendering. Historical PASS counts are not substituted for current execution. Frontend unit output retains Node's package-module detection warning; Python retains the pinned upstream test-client deprecation warning. Neither was suppressed by dependency shims.

## What the new tests actually cover

The final suite retains all 81 existing tests and adds 24 Copilot cases. These cover inventory/media persistence and correction, BOM shortages, eight states, explicit confirmation, evidence requirements, checkpoint/relogin, per-project and per-user isolation, viewer/archive/CSRF denial, stale-write conflicts, secure media validation, multiple-image provider wire context, provider failure without fabricated answers, reviewed plan adoption and malformed plan rejection, late-response protection, changed assembly reference invalidation, old-message pagination and account-deletion media cleanup.

The 48-check production smoke starts a real production Next server and real API with a temporary SQLite database. It stores two equipment photos, requests and reviews a plan, stores a step snapshot, calls the preserved provider connector through an **explicit HTTP test transport**, records review, confirms/completes a step, changes step/mode/notes/issues and saves. It then terminates/restarts the API process and verifies current step/revision/completion/photos/private messages/login state remain. It also tests logout/login, another project, viewer isolation, export and SIMULATION telemetry. The test provider IDs begin `EXPLICIT-TEST-MOCK-`; none is a live Meta success.

Analytic frontend tests verify parent rotation and nested descendant positions, inverse transform, rejection outside bounds/non-finite inputs, unchanged unrelated parts, inherited visibility, reparent placement, undo/redo branching, speech-text normalization, upload bounds and saved plan proposal defaults. Actual pointer gizmos and spoken audio remain unexecuted.

## Confirmed problems corrected during development

- Parent-linked rotation and inherited visibility now work with the existing world-space pose format; unrelated parts retain their identity. Bounds rejection and undo/redo have analytic tests.
- Original dark action buttons used white text on a bright blue with only 2.89 contrast. A separate action token provides 5.83 while keeping bright readable links. The five-destination mobile bar now uses five columns.
- A local snapshot is bound to the step where it was captured. The UI blocks moving steps with an unsaved snapshot and rejects attempts to store it against a different step. Dirty embedded scene edits require save/discard confirmation.
- Saved provider plan JSON can omit optional fields; history reopening now normalizes those fields without losing evidence requirements instead of crashing on a missing list.
- Older conversation paging preserves account/project scope. The current step/equipment/media context is included in actual provider calls, and a newer user checkpoint wins over a late provider response.
- Relevant saved assembly/instruction changes reopen prior confirmations for review. AI cannot silently mark a step electrically verified or complete.
- The additive migration avoids rebuilding SQLite's old chat parent table, preserving dependent change proposals. Equipment-author deletion cascades associated media instead of leaving unlinked project photos.
- Strict lint caught a voice cleanup ref warning; cleanup uses stable captured ref objects and zero-warning lint passes. New record races have explicit bounded conflict responses rather than overwriting data.

## Exact browser block

Both CLI browser suites reached the browser-launch fixture and failed before any page or UI assertion. The relevant Chromium error is:

`FATAL:chrome/browser/process_singleton_posix.cc:297 ... socket() failed: Operation not permitted (1)`

System Chromium 155 was attempted with the pinned Playwright 1.64.1. A separate managed browser could create a blank tab but could not reach the command environment's local server (`net::ERR_CONNECTION_REFUSED`). That did not provide manual UI coverage. No security-policy bypass, GitHub push or deployment was used.

Regular profiles are 1440×900 desktop, 768×1024 tablet, 390×844 and 320×700 mobile. The explicit fixture suite uses desktop and 390px mobile. Each case has a 60-second timeout, no retries and one worker; each suite has a 15-minute global limit. Release attempts used max-failures=1 to avoid repeating the same environment failure. One inherited mobile-only test returns early in each desktop/tablet profile; collection counts do not mean all declarations contain distinct assertions on every profile.

**Not browser-verified:** actual login/navigation/breadcrumb/Back/Forward behavior; new equipment/photo controls; resume across tab closure; rendered conversation/plan readability; Guided/Engineering switching; camera permissions/capture/source switch/cleanup; voice synthesis/recognition; gizmo drag/rotation/snap; responsive layout, themes, keyboard or axe results. Source, types and production build are verified separately.

## Remaining external and product limits

No personal Meta key, live catalog/model eligibility, real text/image/plan inference, quota/quality or provider retention was verified. Native camera/audio, Raspberry Pi/ESP32 sensing/calibration, real physical telemetry and hardware commissioning were not performed. Browser fixtures use synthetic media and speech stubs; those browser fixtures could not execute here. The actual HTTP transport fixture is clearly test-only and is never loaded by the normal application.

Snapshot inspection is implemented; continuous automated video AI, automatic visual registration, verified manufacturer CAD, physical dynamics/electrical certification, historical-checkpoint rollback and autonomous control are not implemented. Equipment identification is saved as review feedback; users correct/apply the structured inventory fields and BOM associations. There is no automatic verified multi-object photo-to-BOM converter. Geometry remains PROCEDURAL_PROVISIONAL and hardware remains NOT VERIFIED.

Windows PowerShell, live PostgreSQL, Docker/Render/cloud/TLS/load and current dependency advisory audits were not executed. Deployment preparation is preserved without claiming it was commissioned. Database downgrade intentionally removes new Copilot data; back up before schema operations.

## Run and acceptance

Read `docs/WINDOWS_VSCODE_RUN.md`, `LIVE_BUILD_COPILOT_GUIDE.md` and `docs/MANUAL_ACCEPTANCE_TESTS.md`. Install pinned dependencies, apply migrations and use `scripts/run_local.ps1`, or run the API and production frontend in two terminals. Actual Meta use requires your own backend MODEL_API_KEY and separate context/image consent. Inventory/template plans/checkpoints/3D/simulation work without a key.

Complete QA entrypoint: `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_windows_copilot.ps1`. It uses a disposable database, restores environment values, avoids real paid keys and runs both suites. `-SkipBrowser` explicitly skips browser certification. The provider-mock runner is not a production demo fallback.

Immediately after extraction, run `python scripts/verify_manifest.py`. The source ZIP excludes dependencies, virtual environments, caches, temporary databases, private environments, browser binaries and screenshots/traces. It includes source, migrations, tests, raw text/JSON/XML results, setup/user/acceptance guides, known limits, external checklist and checksums. No push, deployment or external account change occurred.
