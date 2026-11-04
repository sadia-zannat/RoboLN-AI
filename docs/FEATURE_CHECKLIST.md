# Live Build Copilot implementation checklist

“Implemented” below means actual source and database/API/UI code exists. The measured validation scope is separate: backend/unit/HTTP/migration/build checks passed; browser interaction/native integrations remain pending as stated in FINAL_VERIFICATION_REPORT.md.

| Requested capability | Delivered implementation | Evidence / remaining boundary |
|---|---|---|
| Continue latest source | Uploaded 225-entry ZIP extended; original application modules preserved | Provenance and final source/checksum comparison |
| Persistent guided build | Seven new tables, saved plans/steps, eight states, private user sessions/checkpoints | Backend and production HTTP/restart tests passed |
| Resume Build | Current step, completion, notes, issues, experience, selected component and saved assembly revision | Real API restart/relogin and isolation passed; tab/browser interactions pending |
| Equipment inventory | Category/quantity/model/specifications, unknowns/function/status, corrections, BOM mapping, missing quantities, multiple photos and datasheet IDs | Database/media/scope tests and real proxy flow passed |
| AI-generated plan | Real provider JSON proposal, schema/reference validation, saved provider provenance, explicit user review before adoption | Actual transport exercised with labeled mock; live credentials unavailable |
| Template/manual steps | Deterministic project draft without key; editable instructions/checks/mistakes/components/safety/evidence; append custom steps | API tests passed; no invented wiring/pinout |
| Camera snapshots | Existing lifecycle extended with compact capture/retake/source-switch controls; upload alternative; local preview | Source built; native preview/capture/cleanup pending browser/hardware QA |
| Saved inspection | Scoped normalized image storage, explicit storage/transmission consent, step/equipment context, actual response metadata/history | HTTP provider mock passed; real Meta image inference pending |
| Safe progress | Explicit human confirmation, detailed notes/evidence, no AI completion, changed-reference review and stale-response protection | Negative/state/concurrency-boundary tests passed; not electrical certification |
| Conversation memory | Existing private history retained, recent context plus inventory/current step/docs; older-message cursor pagination and readable React Markdown | API paging/isolation passed; visual readability pending browser QA |
| English voice | Browser speech synthesis, English voices, repeat/stop, interruption cleanup; optional browser recognition into question field | Source/type/build and text helper tests; native audio/STT not executed |
| 3D upgrade | Search/categories, add/remove, interactive gizmos, exact numeric fields, snap, hierarchy translation/rotation, inherited visibility, annotations/focus/explode, undo/redo and revision save | Analytic transform/history tests and existing API tests; pointer/WebGL QA pending |
| Guided/Engineering modes | Same persisted data; simplified step flow vs editable instructions/technical/3D tools | API mode persistence passed; visual controls pending |
| UI design | Original blue-accent studio, light/dark tokens, action contrast fix, collapsible responsive project/visual/copilot panels | Production build passed; static contrast measured; no screenshot/WCAG certification |
| Evidence/export | Guided photos/reviews and checkpoints integrated with original Evidence and account export | API/export/isolation passed |
| Existing product | Authentication/RBAC, planner, sources, assembly, twin, simulation, telemetry, held controls and deployment config retained | Existing 81 tests plus new cases and HTTP regressions passed |
| Release | Source, migration, tests, Windows instructions, user guide, actual results, limitations, checklist and manifest | Final extraction/CRC/hashes checked before delivery |

Snapshot requests are implemented; continuous automated video analysis is not implemented. Native speech recognition is optional browser capability, not full real-time voice conversation. CAD accuracy, automatic camera registration, physical dynamics/compatibility certification and autonomous actuation are outside this release. Real provider/camera/speech/hardware/cloud commissioning is not claimed.

Inventory is capped at 100 records and 100 normalized images per project; images are up to 3 MiB each, six selected per AI request. New guided plans allow up to 60 steps. Current UI loads recent history in pages of 50; all saved conversation rows remain in the database. Checkpoints retain the latest 50 per project/account and display the latest 10; historical checkpoint rollback is not implemented. Undo/redo is in-memory scene history (up to 50 edits), cleared on successful save/reload.
