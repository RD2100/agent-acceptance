# Test-ReviewerEvidence.ps1 - Validate @go reviewer evidence directories.
# Exit 0: PASS or no run evidence. Exit 1: invalid evidence.
# Supports RUN_CLASSIFICATION.yaml: completed_run, historical_incomplete_run, negative_test_fixture.

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

function Read-ClassificationFile {
    param([string]$DirPath)
    $classFile = Join-Path $DirPath "RUN_CLASSIFICATION.yaml"
    if (-not (Test-Path $classFile)) {
        return @{ classification = "completed_run" }
    }
    $content = Get-Content $classFile -Raw -Encoding UTF8
    # Simple YAML key extraction (avoids yaml module dependency)
    $map = @{}
    foreach ($line in $content -split "`n") {
        if ($line -match '^\s*(\w[\w_]*)\s*:\s*"?([^"#\n]*?)"?\s*$') {
            $key = $Matches[1]
            $val = $Matches[2].Trim()
            if ($val -eq "false") { $val = $false }
            elseif ($val -eq "true") { $val = $true }
            $map[$key] = $val
        }
    }
    return $map
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
$skipped = 0
foreach ($dir in $runDirs) {
    $classification = Read-ClassificationFile $dir.FullName
    $classType = if ($classification.classification) { $classification.classification } else { "completed_run" }

    switch ($classType) {
        "historical_incomplete_run" {
            Write-Host "Validating: $($dir.FullName) (historical_incomplete_run)"
            $accepted = $classification.accepted
            $reviewVerified = $classification.review_verified
            $declarationFile = Join-Path $dir.FullName "INCOMPLETE_RUN_DECLARATION.md"
            if ($accepted -ne $false) {
                Write-Host "  ERROR: historical_incomplete_run must have accepted: false"
                $errors++
            }
            if ($reviewVerified -ne $false) {
                Write-Host "  ERROR: historical_incomplete_run must have review_verified: false"
                $errors++
            }
            if (-not (Test-Path $declarationFile)) {
                Write-Host "  ERROR: historical_incomplete_run requires INCOMPLETE_RUN_DECLARATION.md"
                $errors++
            }
            if ($errors -eq 0) {
                Write-Host "  SKIPPED: historical incomplete run — retained as evidence only"
                $skipped++
            }
        }
        "negative_test_fixture" {
            Write-Host "Validating: $($dir.FullName) (negative_test_fixture)"
            $expectedInvalid = $classification.expected_invalid
            $accepted = $classification.accepted
            $reviewVerified = $classification.review_verified
            $declarationFile = Join-Path $dir.FullName "NEGATIVE_FIXTURE_DECLARATION.md"
            if ($expectedInvalid -ne $true) {
                Write-Host "  ERROR: negative_test_fixture must have expected_invalid: true"
                $errors++
            }
            if ($accepted -ne $false) {
                Write-Host "  ERROR: negative_test_fixture must have accepted: false"
                $errors++
            }
            if ($reviewVerified -ne $false) {
                Write-Host "  ERROR: negative_test_fixture must have review_verified: false"
                $errors++
            }
            if (-not (Test-Path $declarationFile)) {
                Write-Host "  ERROR: negative_test_fixture requires NEGATIVE_FIXTURE_DECLARATION.md"
                $errors++
            }
            if ($errors -eq 0) {
                Write-Host "  SKIPPED: negative test fixture — intentionally invalid evidence"
                $skipped++
            }
        }
        default {
            # completed_run or unrecognized — full validation
            Write-Host "Validating: $($dir.FullName) (completed_run)"
            $result = & python $guard evidence $dir.FullName 2>&1
            $exitCode = $LASTEXITCODE
            Write-Host $result
            if ($exitCode -ne 0) {
                $errors++
            }
        }
    }
}

if ($errors -gt 0) {
    Write-Host "[BLOCKED] Reviewer evidence validation failed for $errors run(s)."
    exit 1
}

if ($skipped -gt 0) {
    Write-Host "Reviewer evidence validation PASS ($skipped skipped by classification)."
} else {
    Write-Host "Reviewer evidence validation PASS."
}
exit 0
