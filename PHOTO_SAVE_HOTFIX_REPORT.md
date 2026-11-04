# RoboLN Photo Save Hotfix — 4 November 2026

## Scope and diagnosed cause

The existing backend endpoint `POST /api/projects/{pid}/build/media` already accepts consented step photos, validates size/type and associates the stored JPEG with a persisted build step. Its companion `GET /build/media/{mid}` and the `GET /build` media list are also present. **The backend upload endpoint was not missing.**

The frontend `LiveBuildCopilot.storePhoto()` previously called `fetch(photo)` to convert a camera or uploaded-image `data:image/...;base64,...` URL into a Blob. The site's strict `Content-Security-Policy` has `connect-src 'self'`. Browsers can block `fetch(data:...)` under that policy, producing a generic `Failed to fetch` **before** any `/build/media` POST reaches the server. This explains the user-observed blank Network upload list, while ordinary backend/API requests remained HTTP 200. This is a source-grounded diagnosis; live Windows browser confirmation remains pending.

## Changed source files

- `frontend/lib/local-image.ts`: NEW. Validate and decode the already captured local JPEG/PNG/WebP data URL using the browser's `atob()` into a native Blob. No `fetch(data:...)`, no relaxed CSP, and a strict 3-MiB cap.
- `frontend/components/live-build-copilot.tsx`: Use the local Blob conversion in `storePhoto()`; retain existing consent, CSRF, upload, project ownership and step-association logic. Link directly from 3D reference to existing Practice in 3D workspace.
- `frontend/tests/unit/local-image.test.ts`: NEW. Binary-preserving camera conversion and validation tests.
- `frontend/tests/unit/backend-proxy.test.ts`: NEW binary multipart/consent/CSRF forwarding regression.
- `frontend/tests/e2e/copilot.spec.ts`: Extended existing photo-upload scenario to check persistence after reload. Added assertion is **not executed here**.

No backend schema, migration, Meta credentials, database contents or project records were changed.

## Test results — actually executed in this environment

| Test/check | Result |
| --- | --- |
| `node --experimental-strip-types --test tests/unit/local-image.test.ts tests/unit/backend-proxy.test.ts` | **PASS: 10/10**; 0 failures. Covers local image conversion, binary multipart proxy forwarding, timeout/failure behavior and other proxy cases. |
| TypeScript compiler `transpileModule` parsing of five modified TS/TSX files | **PASS: 5/5 syntax-only**; this does not substitute for full TypeScript typechecking. |
| Python `compileall` backend app | **PASS syntax-only**; backend source unchanged. |
| Full frontend `npm run test:unit` | **BLOCKED: 18 passed, 1 suite unable to load dependency `three`**, as `node_modules` is absent. The failing suite was not a reported assertion failure. |
| `npm ci` | **BLOCKED: dependency installation unavailable in this sandbox**; could not complete (npm command stopped after long wait). Do not report lint/build/e2e as passing. |
| Backend `pytest -q tests/test_copilot.py` | **BLOCKED: 24 setup/import errors**, because sandbox has pypdf 5.9.0, whereas project pins pypdf 6.21.4 (which exposes `overwrite_configuration`); no test cases executed. An attempt to install the pinned version failed due to package-index unavailability. Python 3.13 is installed here; project targets 3.12. |
| Windows/Chrome live save, reload and Meta snapshot inspection | **NOT RUN IN THIS ENVIRONMENT**. Must verify on user's existing working local services. |

## Practice in 3D assessment

The existing full Practice in 3D feature remains: `Load flagship rover` generates the editable **provisional** procedural rover, and `Save assembly revision` persists it to the same per-project workbench that Live Build Copilot reads. The Build Copilot also already had `Load rover example` for an empty workspace. A new direct `Open Practice in 3D` navigation link makes that workflow easier to find. A seeded generic rover is **not** electrically validated, physically assembled or ready for autonomous actuation. No 3D engine rewrite or automatic verified hardware design has been claimed.

## Required acceptance check on Windows after applying patch

1. Back up the current database and keep private `.env` / `.env.local`. Replace changed source files; **do not wipe the project database**.
2. Restart the Next.js frontend so it uses the patched `LiveBuildCopilot` code. Leave the working backend on the configured 8765 port. Confirm backend `/api/health` is available.
3. Sign in and open the **same existing Agri Rover** project and step. Use `Camera > Open Camera > Capture Snapshot` or `Upload Photo` (consent is required).
4. Check `Store this step photo and share it with project members`; click `Save step photo` once. Watch DevTools Network for `POST /api/projects/{pid}/build/media` with **HTTP 201**; a successful call must produce a saved-photo thumbnail.
5. Reload the page. Confirm the thumbnail persists and is linked to the same step. To test AI inspection, separately grant photo-transmission consent, select the image and run `Check My Work` with an actual configured provider.
6. On failure, inspect the **POST request status and response** or newest browser Console error; never reveal secrets or authorization headers. Do not claim production readiness until this acceptance check passes.

## Known limitations

- No physical camera or hardware measurements were tested in the patch environment.
- Meta inference was not called from this sandbox. Earlier user-run real Meta requests are separate evidence.
- The user must explicitly consent to storing a photo **and separately** to sending it to Meta.
- Pre-existing release reports in this repository describe the earlier release. This hotfix report supersedes them **only for the changed files and test scope above**.
