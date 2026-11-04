# RoboLN final release verification. Run PowerShell in the extracted project root:
# powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify_windows_updated.ps1
# The test suite uses a disposable E2E database. Stop your existing localhost servers first.
param([switch]$SkipBrowser)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $root '.venv\Scripts\python.exe'
$testDatabase = Join-Path ([System.IO.Path]::GetTempPath()) ('roboln-release-' + [guid]::NewGuid().ToString('N') + '.db')
$savedEnvironment = @{}
foreach ($key in @('PATH','CI','ROBOLN_DATABASE_URL','MODEL_API_KEY','ROBOLN_BACKEND_URL','ROBOLN_ALLOWED_ORIGINS','ROBOLN_COOKIE_SECURE','NEXT_TELEMETRY_DISABLED')) {
 $savedEnvironment[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
}
function Assert-Exit([string]$label) { if ($LASTEXITCODE -ne 0) { throw "$label failed with exit code $LASTEXITCODE" } }
if (!(Test-Path $python)) {
 Write-Host 'Creating local Python 3.12 environment...'
 & py -3.12 -m venv (Join-Path $root '.venv'); Assert-Exit 'venv setup'
}
Push-Location $root
try {
 & $python -c 'import sys; sys.exit(0 if sys.version_info[:2] == (3, 12) else 1)'; Assert-Exit 'Python 3.12 version'
 $env:ROBOLN_DATABASE_URL = 'sqlite:///' + ($testDatabase -replace '\\','/')
 $env:MODEL_API_KEY = ''
 $env:ROBOLN_BACKEND_URL = 'http://127.0.0.1:8000'
 $env:ROBOLN_ALLOWED_ORIGINS = 'http://127.0.0.1:3000,http://localhost:3000'
 $env:ROBOLN_COOKIE_SECURE = 'false'
 $env:NEXT_TELEMETRY_DISABLED = '1'
 & $python -m pip install -r backend\requirements.lock; Assert-Exit 'Python pinned dependencies'
 & $python -m pip check; Assert-Exit 'Python dependency consistency'
 Push-Location backend
 try { & $python -m alembic upgrade head; Assert-Exit 'Alembic upgrade'; & $python -m pytest -q; Assert-Exit 'Backend pytest' }
 finally { Pop-Location }
 & $python scripts\verify_migration.py; Assert-Exit 'Migration roundtrip'
 & $python scripts\verify_industrial_migration.py; Assert-Exit 'Existing data preservation'
 & $python scripts\verify_copilot_migration.py; Assert-Exit 'Copilot migration and dependent chat preservation'
 Push-Location frontend
 try {
  & npm ci; Assert-Exit 'npm ci'
  & npm run test:unit; Assert-Exit 'Frontend unit tests'
  & npm run lint; Assert-Exit 'ESLint'
  & npm run typecheck; Assert-Exit 'TypeScript'
  & npm run build; Assert-Exit 'Next.js build'
  & $python ..\scripts\smoke_fullstack_http.py; Assert-Exit 'Production frontend/API HTTP integration'
  & $python ..\scripts\smoke_copilot_http.py; Assert-Exit 'Copilot provider mock and backend-restart HTTP integration'
  if (!$SkipBrowser) {
   & npx playwright install chromium; Assert-Exit 'Chromium install'
   $env:PATH = (Resolve-Path (Join-Path $root '.venv\Scripts')).Path + ';' + $env:PATH
   $env:CI = '1'
   $env:MODEL_API_KEY = '' # Browser QA never consumes your real paid key.
   & npm run test:e2e; Assert-Exit 'Playwright E2E'
   & npm run test:e2e:copilot; Assert-Exit 'Explicit provider-mock Copilot browser tests'
  }
 } finally { Pop-Location }
 if ($SkipBrowser) { Write-Host 'Non-browser checks completed; browser E2E was deliberately skipped.' }
 else { Write-Host 'Automated software checks completed. Native camera/Meta/physical devices require separate verification.' }
} finally {
 Pop-Location
 foreach ($key in $savedEnvironment.Keys) { [Environment]::SetEnvironmentVariable($key, $savedEnvironment[$key], 'Process') }
 foreach ($suffix in @('','-wal','-shm','-journal')) { if (Test-Path ($testDatabase + $suffix)) { Remove-Item ($testDatabase + $suffix) -Force } }
}
