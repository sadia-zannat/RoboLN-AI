# Current release QA entrypoint; retains the compatible previous runner name.
param([switch]$SkipBrowser)
& (Join-Path $PSScriptRoot 'verify_windows_updated.ps1') -SkipBrowser:$SkipBrowser
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
