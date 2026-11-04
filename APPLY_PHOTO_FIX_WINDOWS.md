# Apply RoboLN Photo Save Fix — Windows 11

**Recommended: use the tiny HOTFIX PATCH ZIP; do not reinstall the full project.** This keeps your Agri Rover account, local database, backend key configuration and all projects.

1. In VS Code/terminal, stop the **frontend** server (`Ctrl+C` in its terminal). The backend can stay running.
2. Make a safety copy of your working folder, especially `C:\A. RoboLN\RoboLN\backend\roboln_dev.db`, `backend\.env` and `frontend\.env.local`. The database may be at a different location if your environment URL differs.
3. Extract the `RoboLN_PHOTO_SAVE_HOTFIX_PATCH_2026.zip` contents into `C:\A. RoboLN\RoboLN` (the folder containing `frontend` and `backend`) and allow the changed source files to be replaced. **Do not delete `.venv`, `node_modules`, `backend\.env`, `frontend\.env.local` or `backend\roboln_dev.db`.** The patch ZIP contains none of those private files.
4. In a new Windows CMD terminal:
   ```cmd
   cd /d "C:\A. RoboLN\RoboLN\frontend"
   npm run dev
   ```
   Keep your existing backend running at `http://127.0.0.1:8765`. In `frontend\.env.local`, confirm `ROBOLN_BACKEND_URL=http://127.0.0.1:8765` (one equals sign; no duplicate prefix).
5. Open `http://127.0.0.1:3000` and the existing Agri Rover project; test `Camera > Capture Snapshot > store consent > Save step photo`. The expected Network request is a **POST** to `/api/projects/<id>/build/media`, HTTP **201**. Then refresh and confirm the saved photo is still shown.
6. To inspect the saved image using Meta, separately tick `Send the selected photos to Meta for this request` and choose `Check My Work`. The inspection is AI-reported feedback, not proof of electrical safety.

**Practice in 3D:** From Build Copilot's `3D reference` select `Open Practice in 3D`. In the Practice page, use `Load flagship rover` then **Save assembly revision** to persist the provisional 3D BOM. The same project-scoped BOM appears in Build Copilot. This is a template, not verified CAD or a physically complete rover.

**Security:** If you previously showed your Meta key in a screenshot or stored a real value in `.env.example`, revoke/rotate that key. Keep only the new secret in `backend\.env` and never include keys or databases in a public submission ZIP.
