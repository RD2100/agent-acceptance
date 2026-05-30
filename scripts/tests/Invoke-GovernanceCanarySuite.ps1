<#
.SYNOPSIS
Invoke-GovernanceCanarySuite.ps1 — Creates a temporary git clone, injects
violation samples, runs the full canary suite, and cleans up.
All destructive/negative canaries run in isolation, never in the developer workspace.

Usage:
  .\Invoke-GovernanceCanarySuite.ps1 [-ProjectRoot <path>] [-KeepTemp]
#>
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$KeepTemp
)

$ErrorActionPreference = 'Continue'
$script:startTime = Get-Date
$allPassed = $true

Write-Host "=== Governance Canary Suite ==="
Write-Host "Source: $ProjectRoot"

# Create temp repo
$tempRoot = Join-Path $env:TEMP "gov-canary-$([Guid]::NewGuid().ToString('N').Substring(0,8))"
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
Write-Host "Temp: $tempRoot"

try {
    # Clone (or copy files for speed — use git worktree or robocopy if available)
    Write-Host "[Setup] Copying project files..."
    $excludeDirs = @('.git', 'node_modules', '__pycache__', 'runs', 'reports', '.backup', '.codegraph')
    $items = Get-ChildItem $ProjectRoot -Exclude $excludeDirs -ErrorAction SilentlyContinue
    foreach ($item in $items) {
        Copy-Item $item.FullName -Destination (Join-Path $tempRoot $item.Name) -Recurse -ErrorAction SilentlyContinue
    }

    Push-Location $tempRoot

    # ---- Canary 1: Smoke batch ----
    Write-Host ""
    Write-Host "=== Canary 1: Smoke Batch ==="
    $batchResult = & (Join-Path $tempRoot "scripts\Run-Batch.ps1") `
        -TaskFile (Join-Path $tempRoot "batches\batch-smoke.json") `
        -RunsBase (Join-Path $tempRoot "runs\canary-test")

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[PASS] Smoke batch completed (exit 0)"
    } else {
        Write-Host "[FAIL] Smoke batch exit=$LASTEXITCODE (expected 0)"
        $allPassed = $false
    }

    # ---- Canary 2: Protected path violation ----
    Write-Host ""
    Write-Host "=== Canary 2: Protected Path Violation ==="
    "canary-test-content" | Out-File (Join-Path $tempRoot "rules\canary-test.md") -Encoding utf8
    $pgResult = & (Join-Path $tempRoot "scripts\Test-Governance.ps1") -Mode blocking
    Remove-Item (Join-Path $tempRoot "rules\canary-test.md") -ErrorAction SilentlyContinue

    if ($LASTEXITCODE -eq 1) {
        Write-Host "[PASS] Protected path violation blocked (exit 1)"
    } else {
        Write-Host "[FAIL] Protected path violation not blocked (exit=$LASTEXITCODE)"
        $allPassed = $false
    }

    # ---- Canary 3: Secret canary ----
    Write-Host ""
    Write-Host "=== Canary 3: Secret Canary ==="
    $secretFile = Join-Path $tempRoot "scripts\tests\canary-test.txt"
    "sk-proj-deadbeef1234567890abcdef1234567890_not_a_real_key" | Out-File $secretFile -Encoding ascii
    $secretResult = & python (Join-Path $tempRoot "tools\ai_guard.py") full
    Remove-Item $secretFile -ErrorAction SilentlyContinue

    if ($LASTEXITCODE -eq 1) {
        Write-Host "[PASS] Secret canary detected by ai_guard (exit 1)"
    } else {
        Write-Host "[FAIL] Secret canary not detected (exit=$LASTEXITCODE)"
        $allPassed = $false
    }

    Write-Host ""
    Write-Host "=== Canary Suite Complete ==="
    $elapsed = [math]::Round(((Get-Date) - $script:startTime).TotalSeconds, 1)
    if ($allPassed) {
        Write-Host "Verdict: PASS (${elapsed}s)"
    } else {
        Write-Host "Verdict: FAIL (${elapsed}s)"
    }

} finally {
    Pop-Location
    if (-not $KeepTemp) {
        Remove-Item -Recurse -Force $tempRoot -ErrorAction SilentlyContinue
        Write-Host "Cleaned up: $tempRoot"
    } else {
        Write-Host "Kept temp: $tempRoot"
    }
}

if (-not $allPassed) { exit 1 }
exit 0
