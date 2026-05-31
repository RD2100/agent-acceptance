# Test-ReviewerEvidence.ps1 - Validate @go reviewer evidence directories.
# Exit 0: PASS or no run evidence. Exit 1: invalid evidence.

param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Continue"
$runsDir = Join-Path $ProjectRoot "runs"
$guard = Join-Path $ProjectRoot "tools\ai_guard.py"

Write-Host "=== Reviewer Evidence Validation ==="

if (-not (Test-Path $runsDir)) {
    Write-Host "No runs/ directory; skipping reviewer evidence validation."
    exit 0
}

if (-not (Test-Path $guard)) {
    Write-Host "[BLOCKED] tools\ai_guard.py not found."
    exit 1
}

$runDirs = @(Get-ChildItem $runsDir -Directory -Recurse | Where-Object {
    (Test-Path (Join-Path $_.FullName "review.yaml")) -or
    (Test-Path (Join-Path $_.FullName "chain-evidence.json")) -or
    (Test-Path (Join-Path $_.FullName "final-report.md"))
})

if ($runDirs.Count -eq 0) {
    Write-Host "No reviewer evidence directories found; skipping."
    exit 0
}

$errors = 0
foreach ($dir in $runDirs) {
    Write-Host "Validating: $($dir.FullName)"
    $result = & python $guard evidence $dir.FullName 2>&1
    $exitCode = $LASTEXITCODE
    Write-Host $result
    if ($exitCode -ne 0) {
        $errors++
    }
}

if ($errors -gt 0) {
    Write-Host "[BLOCKED] Reviewer evidence validation failed for $errors run(s)."
    exit 1
}

Write-Host "Reviewer evidence validation PASS."
exit 0
