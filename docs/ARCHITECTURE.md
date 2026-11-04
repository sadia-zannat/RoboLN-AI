# RoboLN architecture

## Request and trust boundaries

The Next.js App Router frontend sends same-origin `/api` requests through a bounded explicit Node HTTP/HTTPS proxy to FastAPI. The API is the authority for sessions, CSRF, membership, project state, device credentials and data validation. UI disablement is convenience only. SQLAlchemy persists data; Alembic owns the four-version schema chain. The original models and routes are retained and extended, not replaced by a disconnected app.

Browser session: Argon2 password → hashed random eight-hour session token → HttpOnly cookie. Mutations require matching CSRF header/cookie/session hash and an allowed origin. Membership is owner/editor/viewer. Nonmembers receive 404. Archived projects reject work mutations and device uploads. Device endpoints use separate hashed bearer tokens, with no browser session required.

## Data model

Foundation: users, sessions, login_throttles, projects, memberships, hardware_profiles, conversations (private notes), consents, audit_events, engineering_plans.

Workbench: source_documents (binary original + extracted chunks + SHA-256 + versions), chat_messages (per project/user provider interactions), workbench_states + workbench_revisions (BOM, requirements, pins, tasks and scene), observations (normalized evidence image + user state/method), devices, telemetry and control_requests.

Foreign keys cascade with account/project deletion. Device tokens and session tokens are not exported in plaintext. Source/evidence data are visible only within authorized project membership. Camera frames remain local until a user explicitly chooses server storage or cloud transmission.

## Engineering and 3D

Deterministic family templates collect missing facts and review steps without pretending to be AI. The editable workbench stores requirements, constraints, BOM, references, pins, software notes and tasks. Concurrent saves require the expected revision and a unique revision-history entry. Exports contain real stored records.

React Three Fiber draws detailed locally authored procedural component assemblies and declared connections from this same state. Orbit/zoom/reset, selection, position edits and manual correspondence are functional. Quantities appear in the BOM; the scene shows one representative mesh per BOM entry, not a mechanically expanded assembly. Geometry has no validated manufacturer dimensions, constraints, physics or collision proof.

## Sources and AI

Allowed source files: UTF-8 TXT/MD/CSV/JSON and extractable-text PDFs. Maximum 4 MiB, PDF 100 pages, 500k extracted characters, bounded decoded streams. Unsupported, encrypted, scanned/empty and malformed content is rejected. No external URL downloader or OCR is hidden behind upload.

Text is split into overlapping chunks. Local lexical relevance ranking returns existing source IDs, versions, hashes, chunks and actual PDF page numbers where available. It is a small retrieval system, not an embedding/vector database. All uploaded versions remain searchable until explicitly deleted. Deleted source downloads cease to exist; saved AI records retain a text/hash snapshot. After source deletion, an original-download link may return 404; the genuine saved text/hash snapshot remains in the AI record.

The Meta connector uses server-side `MODEL_API_KEY`, fixed HTTPS `https://api.meta.ai/v1`, `/chat/completions`, `model`, `messages`, `max_completion_tokens` and documented image content blocks. Status never equates configuration with successful inference. A separate catalog check lists models available to the account. User consent precedes transmission. Requests include selected project context, matching retrieved excerpts and up to four private conversation turns. No arbitrary tool execution is exposed.

Prompt-injection mitigation: source/context/image content is designated untrusted data, separated from the developer policy; no model tools, shell, URL fetching or actuator functions exist. Retrieved citation metadata comes from the database. Unknown structured citation markers are replaced; model prose is rendered as plain text. These boundaries reduce consequences but do not prove that a generative answer obeys source instructions or is factually correct. Human review remains required.

Timeouts, rate limits, rejected credentials and malformed provider responses have explicit errors. At most one transient retry is performed. No fake response is persisted on failure. AI audits record attempts/success/failure without logging keys. Runtime provider output exists only after a successful provider request; unit tests replace HTTP transport explicitly and are not evidence of external provider access.

## Camera evidence

Local browser camera lifecycle includes start, permission/error handling, capture, stop and cleanup. Browser or image upload provides a local data URL. The backend re-encodes supported images to fresh JPEG, strips EXIF metadata and limits image size/pixels. Evidence states: UNKNOWN, REVIEW, FAIL, HOLD and user-attested PASS. PASS requires independent-test notes and explicit confirmation. AI analysis returns REVIEW guidance and cannot approve a build. Scene correspondence is manually declared by the user.

## Telemetry and controls

Owner enrollment creates a random device token shown once and stores its hash. Origin (LIVE_REAL/SIMULATION) is fixed at enrollment. HTTP packets have unique IDs, monotonically advancing timezone-aware observation times, receipt timestamps, explicit units, finite numbers and known-sensor ranges. Duplicate/old/future/invalid/rate-excess packets fail. The twin reads actual DB packets and treats data older than 60 seconds as stale. Polling is every five seconds. This is read-only monitoring, not a physically validated simulation.

Control requests bind target, requester, engineering context and a two-minute expiry. Only the owner can review with explicit acknowledgement. A changed context/expired/repeated request is rejected. Approval becomes APPROVED_HOLD. There is no dispatcher or physical executor, even for SAFE_STOP. Independent hardware safety does not depend on the web app.

## API surfaces

The exact request schemas are available from `/api/openapi.json` and `/api/docs` after the API starts.

| Area | Main routes |
|---|---|
| Foundation | `/api/auth/*`, `/api/projects`, `/api/projects/{pid}`, `/members`, `/hardware`, `/draft`, `/context` |
| Planning | `/api/planning/families`, `/api/projects/{pid}/engineering-plans` |
| Workbench | `/api/projects/{pid}/workbench`, `/workbench/history`, `/workbench/checks`, `/engineering-export` |
| Sources | `/api/projects/{pid}/sources`, `/sources/search`, `/sources/{sid}`, `/sources/{sid}/download` |
| AI | `/api/ai/status`, `/api/ai/check`, `/api/projects/{pid}/ai/ask`, `/ai/messages` |
| Evidence | `/api/projects/{pid}/observations`, `/observations/{oid}/image`, `/evidence` |
| Devices | `/api/projects/{pid}/devices`, `/devices/{did}/revoke`, `/api/device/status`, `/api/device/telemetry` |
| Twin | `/api/projects/{pid}/telemetry/twin`, `/twin` (alias), `/telemetry/history` |
| Review | `/api/projects/{pid}/controls`, `/controls/{cid}/review` |
| Health | `/api/health`, `/api/ready` |

## Official provider references checked

- https://dev.meta.ai/docs/overview
- https://dev.meta.ai/docs/cookbook/quickstart-chat-completions
- https://dev.meta.ai/docs/protocols/chat-completions
- https://dev.meta.ai/docs/image-understanding
- https://dev.meta.ai/docs/models

Contract documentation was checked for this release on October 30, 2026. Your account eligibility, actual model catalog and successful text/image inference still require external verification.


## Industrial additions

ComponentMapping binds a saved project component ID to an authenticated device stream, explicit unit, freshness threshold and optional measured visual channel/user review bounds. SensorReading normalizes every accepted packet value with its original observation/receipt times and packet ID. Migration a8f90230d117 adds these records and backfills prior packets. SimulationRun stores deterministic planar constant-twist traces/parameters/events separately. ChatMessage records selected-component context; ChangeProposal requires a genuine saved private response and explicit acknowledged revision-matched review before changing a specification.

The coherent `/twin/snapshot` contains devices, mapped per-stream history (60 samples), alerts, packet-backed device events, observations and held controls. Per-stream freshness is independent of a device's latest packet. Wheel angles retain compatible recorded physical-origin values; planar poses require three axes from one packet. No extrapolation or inferred RPM/pump actuation occurs. World-space scene positions/rotations and logical parent references are provisional, not calibrated CAD/articulation constraints.

New APIs: `/api/projects/{pid}/twin/mappings`, `/twin/snapshot`, `/simulation/runs`, `/simulation/runs/{rid}`, `/ai/proposals`, `/ai/proposals/{rid}/review`. All are membership-scoped; writes use CSRF and editor/owner permissions. Device registration/control review remain owner-only. Browser polling waits for completion, cancels on leave and pauses when hidden. Proxy uses per-request sockets, explicit error correlation and limits; no mutation retry. Operational DB failures are explicit 503s.

This recovery uses existing telemetry events and review audit records rather than a separate TwinEvent table. No lost-tree test result is substituted for current execution.


## Live Build Copilot extension

The additive Alembic head is `c17a90bd4201`, after the existing industrial head `a8f90230d117`. Seven tables add shared build plans/steps/equipment, private build sessions and step progress, scoped binary image media, and bounded private checkpoints. ChatMessage gains optional build-step/equipment IDs, selected media IDs and an intent label; old question/answer/model/provider data remains intact. Nullable chat identifiers are validated by the API without rebuilding the old SQLite parent table, so existing dependent change proposals survive migration.

New routes use `/api/projects/{pid}`: GET `/build`; POST `/equipment`, PUT/DELETE `/equipment/{eid}`; POST `/build/media`, GET/DELETE `/build/media/{mid}`; POST `/build/plan/proposal`, POST `/build/plan`; POST `/build/steps`, PUT `/build/steps/{sid}`; PUT `/build/session`. The existing `/ai/ask` accepts optional copilot/step/equipment/media/intent context. `/ai/messages?before_id=<id>` pages older private conversation rows. Account export includes current private build memory and shared project inventory metadata, excluding image bytes and credentials.

`copilot.py` owns scope checks, state transitions, optimistic revisions, review invalidation and checkpoints. Shared plan edits or relevant saved assembly changes reopen prior user confirmations. Inspection can request review; it cannot complete a step. The provider transport remains the original real Meta API. `tests/mock_provider_api.py` installs an explicit MockTransport only in the test process. Production never imports it.

The new `/workspace/copilot` screen combines inventory/BOM/step navigation, provisional 3D or local camera, and the English step/conversation panel. Existing workspace routes are retained. English browser voice functions have a written fallback; no continuous video inference or autonomous physical control is introduced. Poses remain world-space for old data compatibility; editor operations propagate rigid parent transforms to descendants. Undo/redo is bounded client-side scene history and saved revisions remain on the server.
