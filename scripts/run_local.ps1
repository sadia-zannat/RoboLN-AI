# Optional development launcher. Dependencies and environment templates must be set up first.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Follow docs/WINDOWS_VSCODE_RUN.md to create the Python environment first.' }
Push-Location (Join-Path $root 'backend')
try { & $python -m alembic upgrade head; if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' } } finally { Pop-Location }
Start-Process powershell -WorkingDirectory (Join-Path $root 'backend') -ArgumentList '-NoExit', '-Command', "& '$python' -m uvicorn app.api:app --host 127.0.0.1 --port 8000"
Start-Process powershell -WorkingDirectory (Join-Path $root 'frontend') -ArgumentList '-NoExit', '-Command', 'npm run dev'
