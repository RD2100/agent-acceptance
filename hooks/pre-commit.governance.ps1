# pre-commit.governance.ps1 — Pre-commit governance gate.
# Runs: sadp-audit → manifest auto-regen → git add manifest if changed.
# Exit 0: allow commit. Exit 1: block commit.

$ErrorActionPreference = 'Continue'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "=== Pre-Commit Governance Gate ==="

# ---- 1. SADP audit (secret scan + compliance check) ----
Write-Host "[1/2] SADP audit..."
$auditScript = Join-Path $ProjectRoot "scripts\sadp-audit.ps1"
if (Test-Path $auditScript) {
    Push-Location $ProjectRoot
    try {
        & powershell -ExecutionPolicy Bypass -File $auditScript
        $auditExit = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($auditExit -ne 0) {
        Write-Host "[BLOCKED] sadp-audit failed (exit=$auditExit). Fix issues before commit."
        exit 1
    }
} else {
    Write-Host "[WARN] sadp-audit.ps1 not found — skipping."
}
Write-Host ""

# ---- 2. Manifest auto-regeneration ----
Write-Host "[2/2] Manifest auto-regeneration..."
$updateScript = Join-Path $ProjectRoot "scripts\Update-GovernanceManifest.ps1"
if (-not (Test-Path $updateScript)) {
    Write-Host "[WARN] Update-GovernanceManifest.ps1 not found — skipping."
    exit 0
}

Push-Location $ProjectRoot
try {
    # Save manifest state before regeneration
    $manifestPath = "hooks\sealed-files-manifest.json"
    $before = if (Test-Path $manifestPath) { Get-Content $manifestPath -Raw } else { "" }

    # Regenerate
    & powershell -ExecutionPolicy Bypass -File $updateScript | Out-Null
    $regenerateExit = $LASTEXITCODE
    if ($regenerateExit -ne 0) {
        Write-Host "[WARN] Manifest regeneration had issues (exit=$regenerateExit)"
    }

    $after = if (Test-Path $manifestPath) { Get-Content $manifestPath -Raw } else { "" }

    # If manifest changed, auto-stage it into the current commit
    if ($before -ne $after) {
        git add $manifestPath 2>$null
        Write-Host "[OK] Manifest was out of date — auto-regenerated and staged for this commit."
    } else {
        Write-Host "[OK] Manifest already up to date."
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "=== Pre-Commit PASS ==="
exit 0
