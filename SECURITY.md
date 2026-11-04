# Security and known limitations

## Implemented protections

- Server-side membership on project APIs, owner-only enrollment/review, editor write permissions, archived-project write restrictions and project isolation.
- Argon2 passwords; random hashed session/device tokens; expiring HttpOnly session cookies; CSRF and request-origin checks for browser mutations; database-backed login throttling.
- Per-user AI request limits, timeouts and bounded transient retry; no browser-visible provider key; no model tools or physical executor.
- Bounded request bodies (6 MB), validated source types/sizes, bounded PDF text/streams, normalized image data and redacted validation errors.
- Untrusted source/context separation; real retrieval metadata; safe plain-text AI rendering; no model-produced HTML or link execution.
- No-store API responses; frame/content-type/referrer policy; frontend CSP and camera permission policy. Production cookies require HTTPS and `ROBOLN_COOKIE_SECURE=true`.
- Device credential hashing/revocation, fixed origin, timestamp/unit/range validation, duplicate and stale checks. Controls are context-bound, expiring and always held from execution.

## Limits and unfinished work

This source is not a security certification. Public production commissioning still needs ingress request/time/rate limits, monitoring, abuse controls, data retention/backup policies, load tests, recovery tests and independent review. Registration/email verification, password reset, MFA, SSO, organization administration and distributed rate-limit coordination are not implemented. Login throttling is persistent but per email/IP, not a complete abuse defense.

Source/evidence database encryption at rest depends on your infrastructure. Source limits are per project and do not replace account-wide storage billing/quotas. Sources are not antivirus-scanned or parsed inside an OS sandbox; upload only trusted technical material and keep parser dependencies patched. Prompt injection mitigation is not a guarantee of truthful or instruction-proof model output. Never place secrets in an AI question, image or source.

AI response text can contain incorrect facts, unsupported prose citations or unsafe suggestions even though structured citation links are restricted to supplied sources. All answers require human review. In-app status is configuration state, not a live provider health guarantee. Missing credentials, quota, region or model eligibility can prevent inference.

No exact automatic circuit validation, manufacturer compatibility certification, true CAD, physics, automatic visual registration, firmware compilation/flashing, calibrated plant diagnosis, fertilizer delivery or physical actuation is implemented. User-attested PASS is attributable evidence only. A malicious/miscalibrated authenticated device can report false readings. The browser cannot prove electrical continuity or safety from an image.

The ESP32 transport adapter is not hardware-executed. Raspberry Pi/Python packet transport is software-testable; sensor-specific drivers, calibration, physical stop mechanisms and commissioning require actual hardware. Native webcam capture must be verified on your supported browser; browser specifications use a synthetic MediaStream and denial fixtures; they were blocked before execution in this release.

SQLite and local HTTP are verified separately from any future PostgreSQL, TLS, Docker or Render deployment. No cloud deployment or load benchmark is claimed. Do not treat the supplied deployment configuration as evidence that an external service has been provisioned.

## Privacy lifecycle

Camera preview/capture remains local until explicit transmission/storage. Stopping the camera ends tracks; unmount cleanup invalidates pending starts. Saved images are shared with authorized project members and are removed when their observation/account/project is deleted. Source deletion removes the original but saved AI records retain excerpts/hashes; deleting an account removes its authored AI/source/evidence records through foreign keys. Revoking consent prevents subsequent requests; it cannot recall content already transmitted to Meta. Provider retention is governed by your actual account terms.

Do not publish device tokens in videos/screenshots. The UI shows a token once; hide it before recording. Never commit private `.env`, databases, `node_modules`, virtual environments or traces containing test/user data.

## Industrial boundaries

Same-project component/device mappings, explicit units and independent freshness guard recorded scene state. Simulation histories are separate and cannot drive live transforms. Proposed AI specification changes require a genuine account-owned response, explicit human acknowledgement and an unchanged workbench revision. No pin or actuator edits are applied automatically. Proxy errors remain visible; polling is serialized/abortable. Detailed geometry and planar kinematics are provisional software representations, not validated CAD, collision, electrical compatibility or physical safety. See recovery provenance and current tests.


## Live Build Copilot boundaries

Shared project plans, equipment, references and stored photos require project membership; mutations require an authorized non-archived owner/editor and CSRF validation. Build sessions, step notes/progress, checkpoints and AI messages are scoped to the account and project. Optimistic revisions protect checkpoint/plan/inventory writes. A late provider response cannot overwrite a newer human checkpoint. Step/image references are checked against the same project, and photos for another build step cannot be silently used as that step's inspection.

Photos are limited to 3 MiB input, validated as supported images, re-encoded as bounded JPEG and stripped of EXIF. Storage consent is separate from provider transmission consent. Authenticated image responses are no-store/nosniff. Equipment deletion removes its associated media, including when the equipment author deletes their account; project/account cascades are tested. Historical chat text may retain the fact that an image was used after the underlying media is removed.

English synthesis and optional recognition start only on deliberate user actions. Recognition requires browser microphone permission and may use the browser vendor's speech service. RoboLN does not send microphone audio to its backend or automatically submit recognized questions. Native speech/camera behavior is not verified here. Permissions-Policy allows self microphone access for this explicit feature; it does not grant permission by itself.

AI plan output is schema-checked and remains a proposal until explicit user review. Snapshots cannot establish continuity, polarity, voltage/current compatibility, insulation, absence of shorts or readiness. Every build progress response retains physical_verification=NOT_VERIFIED. Control execution remains disabled. The explicit provider test server is only a test fixture, never a normal application fallback.
