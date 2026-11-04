> **4 Nov 2026 Photo Save hotfix:** See `PHOTO_SAVE_HOTFIX_REPORT.md` and `APPLY_PHOTO_FIX_WINDOWS.md`. The local-image fix is implemented and targeted unit-tested; full Windows browser acceptance is still required. Pre-existing release verification reports refer to the original build.

# RoboLN — Robotics Logic Navigator

**Design. Practice. Build. Verify. Monitor.**

A consolidated Next.js + FastAPI engineering workbench for robotics, embedded systems, electronics and IoT. This release extends the supplied source architecture and preserves account authentication, project membership, isolated notes, hardware identity, deterministic engineering plans, navigation and themes.

The software connects requirements, source-grounded Meta guidance, a detailed procedural 3D assembly, camera/image evidence, device enrollment and timestamped telemetry. Design / Simulation / Live Monitor share stable project component IDs, saved transforms and BOM/pin/source references. It is **production-oriented source, not certification of hardware safety or a claim of production commissioning**.

> **Live Build Copilot release — November 4, 2026:** Persistent guided steps, private checkpoints/Resume Build, equipment photos and BOM mapping, reviewed provider plan proposals, step-linked snapshot inspection, English browser speech, upgraded 3D transforms/gizmos/undo, and a new original blue-accent studio. The supplied codebase was extended directly. Read [actual verification results](FINAL_VERIFICATION_REPORT.md): non-browser checks passed; browser interaction and native integrations remain unverified in this environment.

Start at **Project → Build Copilot** (`/projects/<id>/workspace/copilot`). The original Plan, Practice in 3D, Live Build evidence workbench, Digital Twin and Evidence views remain available.

- [Live Build Copilot user guide](LIVE_BUILD_COPILOT_GUIDE.md)
- [Windows 11 / VS Code run instructions](docs/WINDOWS_VSCODE_RUN.md)
- [Implementation checklist and validation scope](docs/FEATURE_CHECKLIST.md)
- [Manual acceptance tests](docs/MANUAL_ACCEPTANCE_TESTS.md)
- [Known limitations](docs/KNOWN_LIMITATIONS.md)
- [External integration checklist](docs/EXTERNAL_INTEGRATION_CHECKLIST.md)

Guided plans can be generated from your saved project without a key. Actual Meta questions, images and provider plan proposals require your server-side MODEL_API_KEY and consent. There is no production mock-response fallback. Step completion is user-reported; hardware remains NOT VERIFIED.

## Run and verify

- [Windows VS Code instructions](docs/WINDOWS_VSCODE_RUN.md)
- [Final verification report and exact browser limitation](FINAL_VERIFICATION_REPORT.md)
- [Feature implementation and verification matrix](docs/FEATURE_MATRIX.md)
- [Architecture and API](docs/ARCHITECTURE.md)
- [Deployment preparation](docs/DEPLOYMENT.md)
- [External integration checklist](docs/EXTERNAL_INTEGRATION_CHECKLIST.md)
- [Security and limitations](SECURITY.md)
- [Hardware adapters](adapters/README.md)

Python 3.12 and Node 24 LTS are the tested runtime family. Install backend dependencies from `backend/requirements.lock`, frontend dependencies with `npm ci`, then apply Alembic migrations before starting the API. No source editing or patch merging is required.

## Included workflow

1. Register or sign in; create a project and record its exact hardware identity.
2. Open Plan. Collect requirements, constraints, BOM, user-defined pin assignments, software notes and build tasks. Save immutable revisions and export JSON artifacts.
3. Upload technical TXT/MD/CSV/JSON or text PDF sources. Inspect original text, hashes, versions and retrieved excerpts. The local lexical retrieval service does not require an AI key.
4. Ask the project-aware Meta assistant after explicit cloud consent. Text and image requests use the real documented Meta Model API contract. A missing key produces `NOT_CONFIGURED`; no substitute answer is generated. Chat history is private to each project/account; project sources and build observations are shared with project members.
5. Practice with the industrial React Three Fiber assembly: orbit, zoom, reset, select, inspect, move and manually declare component/connection correspondence. Load a provisional rover draft or define other components. Save the scene to the same engineering revision history.
6. In Live Build, deliberately enable the browser camera or select an image. Capture locally, optionally ask Meta to analyze, and separately consent to storing project evidence. Independent user test notes are required for a user-attested PASS. Image analysis cannot produce physical PASS or automatic scene synchronization.
7. Enroll a physical or explicitly simulated controller. A one-time bearer token authenticates packets. The Digital Twin polls actual stored device observations, distinguishes origin and stale state, and displays history. No measurements exist before a packet arrives.
8. Request owner review for a consequential operation. Approval records intent only; dispatch remains `HOLD_NO_EXECUTOR`. Physical actuation is not implemented.

## Important boundaries

- Real Meta inference requires your provider key, model eligibility, network access and explicit consent. Release verification uses explicitly mocked provider responses for connector tests; no real provider success is claimed.
- 3D shapes and coordinates are provisional generic geometry, not manufacturer CAD, accurate scale, physics or electrical simulation.
- Compatibility checks detect user pin conflicts and list required evidence. They do not certify part ratings or generate an electrically validated pinout.
- Native webcam/hardware commissioning remains external. Browser capture specs use a synthetic MediaStream fixture, but they could not execute in this release environment.
- Telemetry is authenticated device-reported data, not proof that a sensor is physically correct. Origin is fixed at device enrollment; a dishonest device can still report incorrect values.
- No automatic irrigation, fertilizer dispensing, firmware flashing, validated plant diagnosis or physical command execution is included.
- Local SQLite is verified; PostgreSQL configuration is supplied but a live PostgreSQL deployment is not claimed.

This package contains no API key, private `.env`, local database, dependency folder, build cache or virtual environment. Historical checkpoint documents are retained under `docs/history/` for provenance and do not describe the current verification state. `packages/contracts/LEGACY_*` are historical contracts; current runtime schemas are the FastAPI/Pydantic definitions and `/api/openapi.json`.

No GitHub push, Render deployment or hackathon submission was performed.


## Ultimate recovery release

Read [recovery provenance](docs/RECOVERY_STATUS.md) and the current test report. Workspace maintenance removed the previous unsaved industrial source. This release retains the last saved consolidated foundation and restores recorded industrial functionality; it is not a byte-for-byte recovery of the removed tree. Earlier 78/96 results are historical, not current certification.

The reusable scene includes 12 generic procedural component categories and a 16-entry rover with PBR materials, lighting/shadows, detailed wheels/motors/PCB/sensors, focus, visibility, explode, orientation and hierarchy. Simulation runs persist deterministic planar traces/events and never write device telemetry. Live sensor mappings feed genuine stored values/times/units into the inspector, scene annotations and trend charts. Measured wheel/atomic pose channels do not extrapolate; simulation streams cannot drive live geometry. Missing/stale/revoked/unmapped states remain explicit.

Selected-component Meta chat uses genuine responses only when configured/consented. Specification proposals require explicit human review and unchanged revision. No physical actuator executor is included. Exact CAD, electrical/physical certification, automatic camera alignment, validated dynamics and real hardware commissioning remain outside the implemented boundary.

The explicit API proxy reads ROBOLN_BACKEND_URL at runtime. It uses fresh upstream sockets, visible reset/timeout errors and no write retry. One serialized abortable twin snapshot replaces overlapping triple polling. See [reset investigation](docs/ECONNRESET_DIAGNOSIS.md) and [local asset provenance](assets/ASSETS_AND_LICENSES.md).
