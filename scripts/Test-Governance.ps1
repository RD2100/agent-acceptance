<#
.SYNOPSIS
Test-Governance.ps1 — Authoritative diff gate (Phase 0-5).
Checks current git diff for governance violations. Aggregates sub-checkers.
Exit: 0=PASS, 1=BLOCKED (governance violation), 2=INFRA_ERROR

Modes:
  advisory: exit 0 always (violations reported, not blocked) — Commit 2a-2b
  blocking: exit 1 on violation — Commit 2c+

Usage:
  .\Test-Governance.ps1 [-Mode advisory|blocking] [-ProjectRoot <path>]
#>
param(
    [ValidateSet('advisory','blocking')]
    [string]$Mode = 'advisory',
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = 'Continue'
$script:startTime = Get-Date

Write-Host "=== Test-Governance ($Mode mode) ==="
Write-Host "Project: $ProjectRoot"
Write-Host ""

# Collect changed files (unstaged + staged)
Push-Location $ProjectRoot
try {
    $unstaged = @(git diff --name-only 2>$null | Where-Object { $_ })
    $staged   = @(git diff --cached --name-only 2>$null | Where-Object { $_ })
    $allChanged = @($unstaged + $staged | Sort-Object -Unique)
} finally {
    Pop-Location
}

Write-Host "Changed files: $($allChanged.Count) (unstaged=$($unstaged.Count), staged=$($staged.Count))"
if ($allChanged.Count -eq 0) {
    Write-Host "No changes detected. PASS."
    Write-Host ""
    exit 0
}
Write-Host ""

# Collect check scripts
$checksDir = Join-Path $PSScriptRoot "checks"
$checkScripts = @(
    (Join-Path $checksDir "Test-ProtectedPaths.ps1"),
    (Join-Path $checksDir "Test-KeyScan.ps1"),
    (Join-Path $checksDir "Test-BatchReferences.ps1")
)

$results = @()
$blockCount = 0
$errorCount = 0
$warnCount = 0

foreach ($checkPath in $checkScripts) {
    $checkName = [System.IO.Path]::GetFileNameWithoutExtension($checkPath)
    Write-Host "[$checkName] Running..." -NoNewline

    if (-not (Test-Path $checkPath)) {
        Write-Host " SKIP (script not found)"
        continue
    }

    try {
        $params = @{ ProjectRoot = $ProjectRoot }
        if ($checkName -eq 'Test-ProtectedPaths') {
            $params['ChangedFiles'] = $allChanged
        }
        $result = & $checkPath @params
    } catch {
        Write-Host " INFRA_ERROR ($($_.Exception.Message))"
        $results += New-CheckResult -CheckName $checkName -Status "INFRA_ERROR" `
            -Details @($_.Exception.Message)
        $errorCount++
        continue
    }

    $results += $result
    switch ($result.Status) {
        'BLOCKED' { $blockCount++; Write-Host " BLOCKED ($($result.Details.Count) violations)" }
        'INFRA_ERROR' { $errorCount++; Write-Host " INFRA_ERROR" }
        'WARN' { $warnCount++; Write-Host " WARN" }
        'PASS' { Write-Host " PASS" }
    }
}

Write-Host ""

# Report
Write-Host "=== Results ==="
foreach ($r in $results) {
    Write-Host "[$($r.CheckName)] $($r.Status)"
    if ($r.Details) {
        foreach ($d in $r.Details) {
            Write-Host "    $d"
        }
    }
    if ($r.Suggestion) {
        Write-Host "    -> $($r.Suggestion)"
    }
}

$elapsed = [math]::Round(((Get-Date) - $script:startTime).TotalSeconds, 1)
Write-Host ""
Write-Host "Summary: BLOCKED=$blockCount ERROR=$errorCount WARN=$warnCount (${elapsed}s)"

# Exit code (advisory = always 0; blocking = exit 1 on violation)
if ($Mode -eq 'blocking') {
    if ($errorCount -gt 0) { exit 2 }
    if ($blockCount -gt 0) { exit 1 }
    exit 0
} else {
    # Advisory: always exit 0, violations reported above
    exit 0
}
