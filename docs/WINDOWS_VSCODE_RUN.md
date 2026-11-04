# Windows 11 + VS Code setup

Use Python 3.12, Node.js 24 and a current Chrome/Edge browser. Extract the ZIP to a short path such as `C:\Projects\RoboLN`; open the folder containing README.md, backend and frontend in VS Code. No source-code writing or integration is needed.

## Install the pinned dependencies

In a PowerShell terminal at the RoboLN root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.lock
if (!(Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
cd frontend
npm ci
if (!(Test-Path .env.local)) { Copy-Item .env.example .env.local }
cd ..
```

Existing private environment files are preserved. Do not copy a real key into frontend code. Python activation is optional when using these explicit interpreter paths.

## Start the application

From the RoboLN root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_local.ps1
```

The launcher applies migrations and opens backend and frontend terminals. Keep them open. Visit `http://127.0.0.1:3000`, register/sign in, create a project and choose Build Copilot. Use the same hostname consistently for cookies.

For separate production terminals, first run the API from `backend`:

```powershell
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```

Then, in a second terminal from `frontend`:

```powershell
npm run build
npm run start
```

API liveness is `http://127.0.0.1:8000/api/health`; readiness is `/api/ready`; API documentation is `/api/docs`. Readiness checks the new build-session table, so apply migrations before starting this release. The current five-revision chain ends at `c17a90bd4201`.

## Optional real Meta integration

Set your server key in `MODEL_API_KEY=` inside `backend/.env` and restart the API. Keep `ROBOLN_META_MODEL=muse-spark-1.3` unless your account's official catalog requires another supported model. Configuration is displayed as CONFIGURED_UNVERIFIED until you actually obtain a response. Allow project context for a question; consent separately for selected image transmission. No credentials are included in the ZIP.

Without a key, inventory, template plans, checkpoints, the 3D editor and simulations work. Meta questions, provider-generated plans and photo inference return a genuine NOT_CONFIGURED error. There is no canned-response fallback in the application. `backend/tests/mock_provider_api.py` is an explicit test-only HTTP fixture and is never used by the normal launcher.

## Complete automated verification

Stop manually running servers on ports 3000/8000. From the RoboLN root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_windows_copilot.ps1
```

This installs pinned dependencies; runs backend tests, three migration checks, frontend unit/lint/type/build, production HTTP integration and real backend-restart checks; then runs both browser suites. It uses a disposable database and no real paid provider key. The browser mock suite is clearly labeled and does not verify real Meta inference, physical camera/audio or hardware.

If browser installation is unavailable, the following explicitly skips browser certification:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_windows_copilot.ps1 -SkipBrowser
```

The browser suites declare 124 normal cases across desktop/tablet/mobile plus 4 explicit provider/media/speech fixture cases across desktop/mobile. Each case has a 60-second timeout; each suite has a 15-minute global limit. `verification/` contains the release environment's actual results. Here browser launch was blocked before UI assertions; those cases are not PASS.

For direct commands, from frontend run `npm run test:unit`, `npm run lint`, `npm run typecheck`, `npm run build`, `npx playwright install chromium`, `npm run test:e2e`, and `npm run test:e2e:copilot`. Put `.venv\Scripts` on PATH, set CI=1 and use a disposable ROBOLN_DATABASE_URL before browser execution, as the runner does.

## Existing database and privacy

Back up the database before upgrading. Run Alembic from backend with ROBOLN_DATABASE_URL pointing at the intended database. The additive migration preserves existing users, membership, source/AI history, workbench, telemetry and dependent proposals. A downgrade removes NEW copilot tables/data and is not a backup/recovery workflow. No user database is shipped.

Camera/recognition needs localhost or HTTPS plus browser permission. Stop camera when finished; view changes/unmount stop tracks. Speech synthesis uses installed English voices. Recognition support, permissions and browser speech-service availability vary; typing remains available. The release was executed on Linux, not Windows, and no native Windows camera/audio was tested.

If an assembly is dirty, Save assembly revision before Save Progress or leaving the editor. Failed AI calls retain saved evidence/progress. A 409 means another tab changed the current record; reload the saved checkpoint before retrying. Never send tests to a valuable database.

Immediately after extraction, verify source integrity with:

```powershell
py -3.12 scripts\verify_manifest.py
```
