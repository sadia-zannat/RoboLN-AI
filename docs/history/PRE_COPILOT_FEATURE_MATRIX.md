# Final release feature and verification matrix — November 4, 2026

`FINAL_VERIFICATION_REPORT.md` and `verification/` are authoritative for this source. Browser UI tests could not start because this runtime denied Chromium's local Unix socket. Historical browser PASS counts do not apply to this release. “API verified” does not mean browser interaction, real hardware or cloud deployment was verified.

| Capability | Current evidence | Remaining limit |
|---|---|---|
| Registration, login/logout, sessions and project CRUD | Pinned backend suite and real production frontend/API HTTP flow passed | Client-side redirects and browser controls pending E2E |
| CSRF, origins, owner/editor/viewer, archive and project isolation | Backend negative tests and real proxy RBAC checks passed | Hosted/TLS commissioning pending |
| Settings and account theme persistence | API tests plus dark preference retained after signout/login | Light/dark/system appearance and responsive controls need browser verification |
| Navigation, breadcrumbs, Back/Forward | Production build and 17 pure navigation assertions passed | Real browser history and keyboard navigation blocked |
| SQLite migrations and old records | Upgrade/downgrade/re-upgrade and old-data preservation passed | Live PostgreSQL not exercised |
| Requirements, BOM, drafts, tasks, pins and revisions | API revision/conflict/export/isolation tests and production HTTP roundtrip passed | Browser editor interactions pending |
| Deterministic engineering intake | Backend tests passed, versioned unverified plans preserved | No manufacturer compatibility or certified pinout |
| Text/PDF source ingestion and local retrieval | Actual pinned PDF extraction, page/chunk/hash and source isolation tests passed | Scanned PDF OCR and semantic embeddings absent |
| Project-aware Meta connector and history | Explicit mocked provider tests; context scoped by project and author; malformed catalog regression tests passed | No live provider key, catalog access, inference or answer-quality verification |
| AI question/answer cards, Markdown and previous-answer expansion | Source preserved; lint, types and production build passed; rendering E2E specs retained | Visual readability, interaction and browser XSS assertions blocked |
| 3D component library, mesh selection, orbit, zoom, focus, transforms and visibility | Source preserved and production build passed | WebGL interaction not executed in this release |
| Library drag/drop and existing-part repositioning | Camera-ray placement source retained; actual-drag browser specs strengthened | Browser execution blocked; touch users have Add/Inspector alternatives |
| Assembly parents and bounded group translation | Unit regressions verify offsets at boundaries; parent IDs/positions persist through real proxy/API | No inherited rotations, joint dynamics, fit or collision validation |
| Beginner assembly tutorial and responsive workspace | Source preserved and production build passed | Tutorial visibility, layout/overflow, keyboard and accessibility checks pending browser gate |
| Deterministic software simulation/replay | Backend analytic/scoped simulation tests passed | Playback UI pending E2E; no validated traction/torque/navigation physics |
| Camera preview/capture/stop and image upload UI | Source and synthetic MediaStream browser fixture preserved | Browser fixture and physical camera not executed |
| Evidence storage, states, independent user PASS boundary | Backend tests and synthetic image upload/read through production proxy passed | Physical observations and independent measurements require a real operator |
| Device enrollment, bearer auth, ingestion, mapping and history | Backend tests, real TCP/production proxy and executed Python SIMULATION adapter passed | No physical Pi/ESP32, clock/calibration or real sensor measurement |
| Twin freshness, origin exclusion, atomic recorded pose and stale behavior | Backend and Node invariant tests passed; production proxy reading remains SIMULATION/excluded | Live chart/annotation/WebGL UI pending; physical coordinates require commissioning |
| Owner review and held controls | Backend and real TCP review checks passed | Execution remains HOLD_NO_EXECUTOR; no actuator dispatcher |
| Manufacturer CAD, automatic camera alignment, physical autonomy, crop diagnosis accuracy | Not implemented/certified | These require further engineering and independent validation |
| Docker/Render/cloud/PostgreSQL deployment | Existing source/configuration retained | No deployment, GitHub push or hosted checks performed |
| Windows setup and complete QA runner | Instructions updated; disposable DB/key isolation and bounded browser run supplied | Not executed on Windows here |
| Source ZIP and checksum manifest | Final CRC, extraction and SHA-256 verification recorded separately | Verify the manifest immediately after extraction, before editing/building |

Original input reports and their old verification logs are retained under `docs/history/` for provenance only. No functionality was removed to obtain passing non-browser checks.
