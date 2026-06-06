# pre-push.governance.ps1 — Governance gate before git push
# Runs the same checks as CI. Blocks push if any fail.
# Exit 0: allow push. Exit 1: block push.

$ErrorActionPreference = 'Continue'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$errors = 0

Write-Host "=== Pre-Push Governance Gate ==="

# 1. AI Guard — secret scan + deny paths
Write-Host "[1/5] ai_guard.py..."
$result = & python (Join-Path $ProjectRoot "tools\ai_guard.py") full 2>&1
$ec = $LASTEXITCODE
Write-Host $result
if ($ec -ne 0) {
    Write-Host "[BLOCKED] ai_guard.py failed (exit=$ec)"
    $errors++
}
Write-Host ""

# 2. Reviewer Evidence Validation
Write-Host "[2/5] Reviewer evidence..."
$result = & powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\Test-ReviewerEvidence.ps1") 2>&1
$ec = $LASTEXITCODE
Write-Host $result
if ($ec -ne 0) {
    Write-Host "[BLOCKED] Reviewer evidence validation failed (exit=$ec)"
    $errors++
}
Write-Host ""

# 2.5 Workflow Closure Validation (SD-01/02/03 enforcement)
Write-Host "[2.5/5] Workflow closure validation..."
$validator = Join-Path $ProjectRoot "scripts\validate_workflow_closure.py"
$packErrors = 0
if (Test-Path $validator) {
    $stagedZips = @(git diff --cached --name-only 2>$null | Where-Object { $_ -like "*closure-pack*" -or $_ -like "*evidence-pack*" })
    if ($stagedZips.Count -eq 0) {
        Write-Host "  No staged closure packs found; skipping."
    } else {
        foreach ($zipRel in $stagedZips) {
            $zipAbs = Join-Path $ProjectRoot $zipRel
            Write-Host "  Validating: $zipRel"
            $result = & python $validator $zipAbs 2>&1
            $ec = $LASTEXITCODE
            Write-Host $result
            if ($ec -ne 0) {
                Write-Host "  [BLOCKED] Closure validation failed: $zipRel (SD-01/02/03 check)"
                $packErrors++
            }
        }
    }
} else {
    Write-Host "  [WARN] validate_workflow_closure.py not found — skipping."
}
if ($packErrors -gt 0) {
    Write-Host "[BLOCKED] Workflow closure validation failed for $packErrors pack(s)."
    $errors++
}
Write-Host ""

# 3. Governance Drift Check
Write-Host "[3/5] Drift check..."
$result = & powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\Test-GovernanceDrift.ps1") 2>&1
$ec = $LASTEXITCODE
if ($ec -ne 0) {
    Write-Host "[BLOCKED] Governance drift detected (exit=$ec)"
    $errors++
}
Write-Host ""

# 4. Governance Gate (blocking)
Write-Host "[4/5] Governance gate..."
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
