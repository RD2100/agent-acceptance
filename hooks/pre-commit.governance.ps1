# pre-commit.governance.ps1 — Pre-commit governance gate.
# Runs: manifest auto-regen → sadp-audit.
# Order matters: regenerate manifest FIRST so sadp-audit checks against current state.
# Only git adds manifest files (never git add .).
# Exit 0: allow commit. Exit 1: block commit.

$ErrorActionPreference = 'Continue'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

Write-Host "=== Pre-Commit Governance Gate ==="

# ---- 1. Manifest auto-regeneration (BEFORE audit) ----
Write-Host "[1/2] Manifest auto-regeneration..."
$updateScript = Join-Path $ProjectRoot "scripts\Update-GovernanceManifest.ps1"
$manifestPath = "hooks\sealed-files-manifest.json"

Push-Location $ProjectRoot
try {
    $before = if (Test-Path $manifestPath) { Get-Content $manifestPath -Raw } else { "" }

    if (Test-Path $updateScript) {
        & powershell -ExecutionPolicy Bypass -File $updateScript | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] Manifest regeneration had issues (exit=$LASTEXITCODE)"
        }
    } else {
        Write-Host "[WARN] Update-GovernanceManifest.ps1 not found — continuing."
    }

    $after = if (Test-Path $manifestPath) { Get-Content $manifestPath -Raw } else { "" }

    if ($before -ne $after) {
        git add $manifestPath 2>$null
        Write-Host "[OK] Manifest regenerated and staged for this commit."
    } else {
        Write-Host "[OK] Manifest already up to date."
    }
} finally {
    Pop-Location
}
Write-Host ""

# ---- 2. SADP audit (checks against NOW-CURRENT manifest) ----
Write-Host "[2/2] SADP audit..."
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
Write-Host "=== Pre-Commit PASS ==="
exit 0
