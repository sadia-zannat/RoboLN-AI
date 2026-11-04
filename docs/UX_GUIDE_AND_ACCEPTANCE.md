> Current Copilot workflow: [LIVE_BUILD_COPILOT_GUIDE.md](../LIVE_BUILD_COPILOT_GUIDE.md). Current acceptance checklist: [MANUAL_ACCEPTANCE_TESTS.md](MANUAL_ACCEPTANCE_TESTS.md). Browser results are blocked, not PASS.

# RoboLN — user-friendly 3D assembly and AI walkthrough (updated build)

## What was changed in this ZIP

- **AI chat is now a conversation interface:** each question is visually separated; recent answer opens by default, older answers can be expanded; model Markdown is displayed as escaped React headings, lists, tables, code and emphasis. No HTML from Meta is inserted as executable markup. Four beginner question starters are supplied. The assistant's developer instruction asks for the answer first and shorter explanations while retaining physical safety/provenance limits. Image preview is local; cloud and image consents remain separate.
- **Beginner tutorial beside the 3D scene:** the Inspector has a Tutorial tab selected when the scene first opens, with four guided steps. Selecting a part automatically opens its Inspector. A collapsible full-width quick guide is available.
- **Component drag-and-drop:** in Design mode, select a part in the left library and drag the dashed part tile into the 3D scene. To reposition an existing part, drag its entry in the Assembly list into the scene. Drop uses the current 3D camera ray projected onto a provisional horizontal layout plane; the selected part keeps its Y height. Keyboard users can instead use Add selected component and the Inspector X/Y/Z numeric fields.
- **Attach/group behavior:** choose a selected component's Assembly parent (descendants and self are excluded to prevent cycles). Place above parent positions it at a *provisional* y-offset; subsequent parent translation moves its linked descendants. At workspace boundaries the whole group stops together so relative offsets are preserved. This is logical grouping with world-space positions, **not** a mechanically validated CAD joint, collision fit or wiring connection. Parent rotation now applies a rigid world-space transform to descendants.
- **Navigation:** long breadcrumb labels truncate instead of overlapping the project picker in constrained layouts.

## Test the user workflow (Windows laptop)

1. Start the backend and frontend exactly as in `docs/WINDOWS_VSCODE_RUN.md`; never paste your Meta key into screenshots or source code.
2. Sign in, make a *new disposable test project*, and open **Workspace → Practice in 3D → Design**. The right **Tutorial** tab should display four steps.
3. In the left **Component library**, select **Inspection camera**. Drag the dashed **Inspection camera · Drag to 3D** tile into the main 3D area. The part should appear in the Assembly list, be selected and have unsaved changes.
4. To move the camera again, drag its **Assembly** list name onto a different location in the 3D scene. Alternatively adjust the Inspector's position values. The original camera height should remain unchanged on a horizontal-plane drop.
5. In Inspector, set **Assembly parent** to **Controller board** if present; click **Place above parent** for a visual layout, then save. **Do not** assume electrical connection, exact clearance or mechanical fastening. Move the parent and inspect whether its children translate in the draft (rotations remain independent).
6. Click **Save assembly revision**, then **Reload saved assembly**, refresh the browser, and confirm the positions, visibility, hierarchy and revision persist.
7. Switch to **Simulation**, generate a deterministic virtual run, start/pause/reset, and verify the status stays labelled SOFTWARE SIMULATION. Switch to **Live Monitor**, confirm that no real measurements appear without an enrolled device and authenticated packet.
8. Open **Plan → RoboLN AI engineering guide**. Choose a starter question or type a short one. Consent to cloud project context before sending. If you attach an image, you must separately consent to image sharing. A successful provider answer should appear formatted, with the latest answer open and prior turns expandable.
9. Open **Evidence** and check that user observations and application activity remain separately labelled. Do not treat an AI answer as a physical PASS.
10. Check **Projects / breadcrumbs / Workspace / Digital Twin / Evidence**, back, forward, theme, browser refresh, and 320px mobile width. Screenshots of each are suitable for manual review.

## What the new controls do *not* claim

This is an improved **project-scoped procedural 3D engineering editor** and a responsive conversational UI. It is **not** a full parametric CAD system, CAD import pipeline, collision-accurate manipulator, verified electrical schematic tool, robotics physics engine, real robot-autonomy system, or commissioned physical digital twin. Simulation is deliberately labelled. Real Meta inference, physical sensor integration and native webcam require verification on your actual machine.

## Automated commands (run after dependencies are installed)

From `frontend`: `npm run test:unit`, `npm run lint`, `npm run typecheck`, `npm run build`, `npx playwright install chromium`. With the API/frontend stopped and a disposable E2E database, run `npm run test:e2e` as described in the Windows guide. The new `tests/e2e/ux-guided-assembly.spec.ts` adds drag/drop, saved grouping and a mocked-provider Markdown/XSS-rendering smoke. These additional browser tests were **not executed** in this authoring environment. Existing historical E2E pass counts do not apply to this modified code.

## Technical release status

Read `FINAL_VERIFICATION_REPORT.md` for exactly what was run. If any local build or browser test fails, do not treat the UX build as fully verified; collect the command, output, and failing Playwright trace. The package contains full source, not just design mockups.
