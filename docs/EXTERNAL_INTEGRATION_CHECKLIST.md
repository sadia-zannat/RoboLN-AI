# External integration and acceptance checklist

Current measured results are in FINAL_VERIFICATION_REPORT.md. No external account, GitHub, deployment or submission action was performed.

## Complete browser acceptance first

Run `scripts/verify_windows_copilot.ps1` without -SkipBrowser on a machine that can start Chromium. Require real results for the 124-case regular suite and 4-case explicit mock-provider/media/speech suite. Their release-environment execution was blocked before page creation; do not convert that into a UI PASS. Follow MANUAL_ACCEPTANCE_TESTS.md for visual/gizmo/camera/voice/mobile and keyboard review. Check the new five-item mobile navigation, collapsed panels, Guided/Engineering switching and both themes.

## Prove actual Meta account/model access

- Put your own server key in backend/.env as MODEL_API_KEY and restart the API. Never use NEXT_PUBLIC_ for a provider key.
- Confirm account/region/model eligibility and quota in the official Meta developer portal. The preserved default is muse-spark-1.3. CONFIGURED_UNVERIFIED only means a key is present.
- Consent to a non-sensitive question. Verify a real answer and provider/model metadata. A 401/403/429/timeout is a failed integration check; it must not create a fake success record.
- Upload an actual datasheet, retrieve a known term, ask about it and independently compare the answer and source/page/chunk reference.
- Request a provider plan, review the proposed steps and explicitly adopt it. Confirm no steps are saved before acceptance and edits reopen confirmation as needed.
- Capture/upload a non-sensitive engineering photo, explicitly consent to storage and transmission, inspect the current step and verify the actual provider response. Check that it names visible observations/unknowns/next independent check and remains REVIEW/NOT VERIFIED. Repeat with multiple selected equipment photos if your model supports them.
- The included provider fixtures prove software behavior only. `scripts/verify_meta_inference.py --consent-send` is an optional operator live catalog/text smoke; it is deliberately excluded from automatic release QA. Native photo quality and model engineering advice require separate inspection.

## Verify camera and voice on Windows

- Use localhost/HTTPS, allow the intended USB/built-in camera, capture/retake/stop/switch source and confirm tracks stop on navigation. Test denial/no-device and upload fallback.
- Try Speak Instruction, English voice selection, repeat/stop and step-change interruption. Test Dictate question in a supported browser; recognized text must wait for your Ask AI action. Confirm permission/service errors retain the text fallback. Browser recognition may use a browser-vendor speech service.
- Confirm local preview is not advertised as continuous provider vision. No microphone audio is stored by RoboLN's backend.

## Commission any real device independently

- Review exact board revision, ratings, power/wiring and physical safety with qualified independent evidence. Generic meshes are provisional.
- Enroll software fixtures as SIMULATION. Enroll a real calibrated sensor as LIVE_REAL only when you actually have that device, clock, driver and calibration.
- Send a timestamped authenticated packet and compare the exact recorded value/unit/origin in history, inspector and twin. Test stale/revoked/invalid token behavior. Pose channels need an independently calibrated frame and atomic packet.
- Record instrument/method/uncertainty/results for independent tests. Step completion is a user report and photos are not electrical verification. Owner approvals remain HOLD_NO_EXECUTOR; physical execution is not implemented.

## Optional future hosting

Live PostgreSQL, Docker/Render, HTTPS/secure cookies, backup/retention policy, load/availability and provider usage/cost must be commissioned separately. Deployment files are preserved but nothing was deployed. Back up existing databases before applying migrations. No push, external account change or hackathon submission occurred during this release.
