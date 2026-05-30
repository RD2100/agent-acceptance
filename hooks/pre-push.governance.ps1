# pre-push.governance.ps1 — Governance gate before git push
# Runs the same checks as CI. Blocks push if any fail.
# Exit 0: allow push. Exit 1: block push.

$ErrorActionPreference = 'Continue'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$errors = 0

Write-Host "=== Pre-Push Governance Gate ==="

# 1. AI Guard — secret scan + deny paths
Write-Host "[1/3] ai_guard.py..."
$result = & python (Join-Path $ProjectRoot "tools\ai_guard.py") full 2>&1
$ec = $LASTEXITCODE
Write-Host $result
if ($ec -ne 0) {
    Write-Host "[BLOCKED] ai_guard.py failed (exit=$ec)"
    $errors++
}
Write-Host ""

# 2. Governance Drift Check
Write-Host "[2/3] Drift check..."
$result = & powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\Test-GovernanceDrift.ps1") 2>&1
$ec = $LASTEXITCODE
if ($ec -ne 0) {
    Write-Host "[BLOCKED] Governance drift detected (exit=$ec)"
    $errors++
}
Write-Host ""

# 3. Governance Gate (blocking)
Write-Host "[3/3] Governance gate..."
$result = & powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\Test-Governance.ps1") -Mode blocking 2>&1
$ec = $LASTEXITCODE
if ($ec -ne 0) {
    Write-Host "[BLOCKED] Governance gate failed (exit=$ec)"
    $errors++
}
Write-Host ""

if ($errors -gt 0) {
    Write-Host "=== BLOCKED: $errors check(s) failed. Fix before push. ==="
    exit 1
}
Write-Host "=== PASS: All governance checks passed ==="
exit 0
