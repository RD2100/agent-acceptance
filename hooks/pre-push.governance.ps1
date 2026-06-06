# pre-push.governance.ps1 — Governance gate before git push
# Runs the same checks as CI. Blocks push if any fail.
# Exit 0: allow push. Exit 1: block push.

$ErrorActionPreference = 'Continue'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$errors = 0

Write-Host "=== Pre-Push Governance Gate ==="

# 1. AI Guard — secret scan + deny paths
Write-Host "[1/6] ai_guard.py..."
$result = & python (Join-Path $ProjectRoot "tools\ai_guard.py") full 2>&1
$ec = $LASTEXITCODE
Write-Host $result
if ($ec -ne 0) {
    Write-Host "[BLOCKED] ai_guard.py failed (exit=$ec)"
    $errors++
}
Write-Host ""

# 2. Reviewer Evidence Validation
Write-Host "[2/6] Reviewer evidence..."
$result = & powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\Test-ReviewerEvidence.ps1") 2>&1
$ec = $LASTEXITCODE
Write-Host $result
if ($ec -ne 0) {
    Write-Host "[BLOCKED] Reviewer evidence validation failed (exit=$ec)"
    $errors++
}
Write-Host ""

# 2.5 Workflow Closure Validation (SD-01/02/03 enforcement)
Write-Host "[2.5/6] Workflow closure validation..."
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
    Write-Host "  [BLOCKED] validate_workflow_closure.py not found — fail-closed (SD-01/02/03 guard)"
    $packErrors++
}
if ($packErrors -gt 0) {
    Write-Host "[BLOCKED] Workflow closure validation failed for $packErrors pack(s)."
    $errors++
}
Write-Host ""

# Step 2.6: GPT Review Gate
Write-Host "[2.6/6] GPT Review Gate..."
$gptGatePassed = $true
$stagedClosurePacks = Get-ChildItem -Path "runs" -Recurse -Filter "POST_REVIEW_ROUTE.json" | Where-Object { (Get-Item $_.DirectoryName).LastWriteTime -gt (Get-Date).AddHours(-2) }
foreach ($pack in $stagedClosurePacks) {
    $route = Get-Content $pack.FullName -Raw | ConvertFrom-Json
    if ($route.overall_judgment -eq "submitted_for_gpt_review") {
        Write-Host "  BLOCKED: $($pack.Directory.Name) has overall_judgment=submitted_for_gpt_review - not yet GPT accepted"
        $gptGatePassed = $false
    }
}
if (-not $gptGatePassed) {
    Write-Host "  GPT Review Gate: BLOCKED - some packs not yet GPT accepted. Submit to GPT first."
    exit 1
}
Write-Host "  GPT Review Gate: PASS"
Write-Host ""

# 3. Governance Drift Check
Write-Host "[3/6] Drift check..."
$result = & powershell -ExecutionPolicy Bypass -File (Join-Path $ProjectRoot "scripts\Test-GovernanceDrift.ps1") 2>&1
$ec = $LASTEXITCODE
if ($ec -ne 0) {
    Write-Host "[BLOCKED] Governance drift detected (exit=$ec)"
    $errors++
}
Write-Host ""

# 4. Governance Gate (blocking)
Write-Host "[4/6] Governance gate..."
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
