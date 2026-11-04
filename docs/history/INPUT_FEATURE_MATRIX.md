# Feature implementation and verification matrix

Status vocabulary: **Implemented and verified** = exercised by this release's automated software checks; **Implemented, external verification pending** = functioning source with provider/device/cloud dependencies not exercised; **Partial** = useful bounded capability with specified missing behavior; **Blocked** = a required external credential or physical resource is absent; **Not implemented** = no working implementation is claimed.

The exact executed counts, commands, failures corrected and limitations are in `VERIFIED_TEST_REPORT.md` and `verification/`. Mocked services and synthetic frames are not real external integrations.

| Capability | Status | Verification / exact limit |
|---|---|---|
| Registration, login/logout, sessions, theme, project CRUD | Implemented and verified | Preserved foundation tests plus real browser navigation/export flows |
| CSRF, origin checks, RBAC, isolation, archive protection | Implemented and verified | Backend negative tests, anonymous/forbidden routes and browser signout/deep-link checks |
| Database schema and upgrade chain | Implemented and verified | SQLite fresh/previous-checkpoint upgrade, existing identity preservation and downgrade/re-upgrade |
| Responsive navigation, keyboard controls and light/dark UI | Implemented and verified | Four viewport profiles, width checks, keyboard/navigation and accessibility scans; not a complete manual screen-reader audit |
| Requirements, constraints, BOM, task checklist, software notes | Implemented and verified | Persisted workbench revisions, exports and browser rover workflow; input remains a user engineering draft |
| Universal deterministic engineering intake | Implemented and verified | Seven project families, versioned templates, missing-fact/risk checks; explicitly not model inference |
| Board/component compatibility and pin mapping | Partial | User pin mapping, duplicate/conflict detection and required evidence checklist work; electrical/manufacturer compatibility is not certified or automatically solved |
| Real Meta text/image connector | Implemented, external verification pending | Official contract verified; deterministic HTTP transport success/failure/consent tests. No real key/provider success in this release |
| Actual provider inference | Blocked | Requires your server key, account eligibility, quota and network. UI truthfully shows NOT_CONFIGURED without a key |
| Project-aware AI chat and source-linked context | Implemented and verified for software boundaries | Project/board/workbench/plan/history/excerpts sent through tested connector; answer truthfulness and actual external model behavior remain unverified |
| Source upload, extraction, versions, inspection and retrieval | Implemented and verified | UTF-8 TXT/MD/CSV/JSON and text PDF; actual page/chunk/hash references; lexical retrieval rather than embeddings |
| Source prompt-injection protection | Partial | Untrusted-data policy, no tools/executors, bounded context, real citation metadata and plain-text rendering. Generative instruction compliance is not guaranteed |
| Interactive component 3D assembly | Implemented and verified | Real WebGL canvas, orbit/zoom/reset, select/inspect/edit/save, connection declarations, keyboard component alternatives |
| Accurate manufacturer CAD / physics | Not implemented | Generic provisional meshes, units and layouts only; one mesh per BOM entry |
| Camera start/stop, capture, image upload and storage | Implemented and verified for software flow | Synthetic MediaStream drives actual video/canvas capture and stop; upload, normalized image storage, permission/error paths tested |
| Native USB webcam and real images | Implemented, external verification pending | Requires supported user browser, permission and camera; headless runner cannot prove native camera operation |
| Camera-to-3D synchronization | Partial | Manual user-confirmed correspondence works. Automatic visual registration/tracking is not implemented |
| Evidence states and verification history | Implemented and verified | UNKNOWN/REVIEW/FAIL/HOLD and independent-test user-attested PASS. AI never grants physical PASS |
| Device enrollment, token auth, validated telemetry | Implemented and verified | Software HTTP packets, origin separation, timestamps/units/ranges, duplicate/revocation/stale handling and history |
| Digital Twin monitoring | Implemented and verified for software flow | Reads real stored ingested packets; absent data stays absent; explicit simulation and stale states. No physical dynamics model |
| Raspberry Pi/generic Python transport | Implemented, hardware verification pending | Uses verified HTTPS, origin check and actual supplied packets; board-specific sensor acquisition/calibration remains external |
| ESP32 MicroPython transport | Partial | TLS-aware transport source and syntax validation provided; firmware-specific TLS, Wi-Fi, clocks and sensor drivers not executed on hardware |
| Owner control review and fail-safe queue | Implemented and verified for intent handling | Context-bound expiry and repeat checks; approvals remain APPROVED_HOLD; no physical executor |
| Irrigation / fertilizer / autonomous physical operations | Not implemented | No dispatcher, operational GPIO driver, fertilizer system or safety-commissioned autonomous loop |
| Plant image diagnosis accuracy | Not implemented | Provider image guidance can be requested with consent; no trained/validated crop-diagnosis model or accuracy claim |
| Deployment templates and health endpoints | Implemented, external verification pending | Env templates, migration commands, Dockerfiles, Render prep, health/readiness. No Docker/cloud deployment or live PostgreSQL commissioning claimed |
| Source archive and checksum manifest | Verified by packaging checks | Final ZIP integrity, clean extraction, file hashes and excluded secret/cache artifacts recorded in the test report |

## Ultimate recovery additions

| Capability | Status and boundary |
|---|---|
| Detailed procedural R3F, 12-category library, transforms/hierarchy/visibility/explode/focus/revisions | VERIFIED IMPLEMENTED in the current 100-case browser run; no verified CAD/scale |
| Design / Simulation / Live Monitor | VERIFIED IMPLEMENTED on shared components, saved deterministic simulation/replay/events; no validated dynamics |
| Sensor/device/component mapping, independent freshness, history, chart/annotation and atomic pose | VERIFIED IMPLEMENTED by current API/state/browser tests; hardware calibration/coordinate registration external |
| Selected-component genuine Meta context and reviewed specification proposals | IMPLEMENTED — EXTERNAL VERIFICATION REQUIRED; mocked-provider selected-context/review contract tests pass; real key/catalog/text/image inference external |
| Explicit proxy/serialized polling/503 DB errors | VERIFIED IMPLEMENTED and fault-tested; exact original Windows reset cause unconfirmed |
| Removed industrial source and old 78/96 test evidence | Cannot recover byte-for-byte after workspace maintenance; restored functionality and new results are documented honestly |

Physical actuation, automatic camera alignment, manufacturer CAD, validated collision/torque/navigation physics, automatic electrical certification and native hardware commissioning remain not implemented or externally unverified as stated. No unfinished physical capability is marked complete.
