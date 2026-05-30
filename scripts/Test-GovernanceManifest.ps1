<#
.SYNOPSIS
Test-GovernanceManifest.ps1 — Verify that manifest is in sync with current files.
Runs Update-GovernanceManifest then checks if git diff is empty.

Usage:
  .\Test-GovernanceManifest.ps1 [-ProjectRoot <path>]
Exit: 0=PASS (in sync), 1=BLOCKED (drift detected), 2=INFRA_ERROR
#>
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = 'Continue'

# Check manifest-ignore constraints
$ignorePath = Join-Path $ProjectRoot "governance\manifest-ignore.txt"
if (Test-Path $ignorePath) {
    $ignored = Get-Content $ignorePath | Where-Object { $_ -notmatch '^\s*(#|$)' } | ForEach-Object { $_.Trim() }
    $forbidden = @('rules/', 'hooks/', 'scripts/', 'governance/', '.github/workflows/', 'AGENTS.md', '.ai/policy.yaml')
    foreach ($line in $ignored) {
        foreach ($pat in $forbidden) {
            if ($line.TrimStart('/') -like "$pat*" -and $line -notmatch '^(archive|future|runs|reports|\.backup|__pycache__|node_modules)') {
                Write-Warning "[MANIFEST-IGNORE] Potentially unsafe exclusion: '$line' matches protected path '$pat'"
                # Do not block on warning alone — only block if the exclusion is definitive
                if ($line -eq $pat -or $line -like "$pat*" -and $pat -match '/$') {
                    Write-Error "[MANIFEST-IGNORE] BLOCKED: '$line' excludes protected path '$pat'. Remove from manifest-ignore.txt."
                    exit 1
                }
            }
        }
    }
}

# Run update
$updateScript = Join-Path $PSScriptRoot "Update-GovernanceManifest.ps1"
if (-not (Test-Path $updateScript)) {
    Write-Error "Update-GovernanceManifest.ps1 not found"
    exit 2
}

Push-Location $ProjectRoot
try {
    # Save current manifest state
    $before = Get-Content "hooks\sealed-files-manifest.json" -Raw -ErrorAction SilentlyContinue

    & $updateScript

    $after = Get-Content "hooks\sealed-files-manifest.json" -Raw

    if ($before -ne $after) {
        Write-Host "[MANIFEST] Drift detected — manifest was out of sync and has been updated."
        Write-Host "[MANIFEST] Verify the changes and re-commit."
        exit 1
    } else {
        Write-Host "[MANIFEST] In sync — no drift."
        exit 0
    }
} finally {
    Pop-Location
}
