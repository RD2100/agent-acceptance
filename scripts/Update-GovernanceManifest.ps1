<#
.SYNOPSIS
Update-GovernanceManifest.ps1 — Recalculate SHA256 hashes for all governance files
and update hooks/sealed-files-manifest.json.

Explicitly excludes hooks/sealed-files-manifest.json itself (self-hashing excluded).
This exclusion is HARDCODED, not dependent on manifest-ignore.txt.

Usage:
  .\Update-GovernanceManifest.ps1 [-ProjectRoot <path>]
#>
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = 'Stop'

$manifestPath = Join-Path $ProjectRoot "hooks\sealed-files-manifest.json"
$expectedPath = Join-Path $ProjectRoot "governance\expected-files.txt"
$selfPath = "hooks/sealed-files-manifest.json"

Write-Host "=== Update Governance Manifest ==="
Write-Host "Project: $ProjectRoot"

# Load expected file patterns
if (-not (Test-Path $expectedPath)) {
    Write-Error "expected-files.txt not found at $expectedPath"
    exit 2
}

$patterns = Get-Content $expectedPath | Where-Object { $_ -notmatch '^\s*(#|$)' } | ForEach-Object { $_.Trim() }

# Resolve all matching files via Get-ChildItem
$files = @()
foreach ($pattern in $patterns) {
    $dir = Split-Path $pattern -Parent
    $name = Split-Path $pattern -Leaf
    $fullDir = Join-Path $ProjectRoot $dir
    if (Test-Path $fullDir) {
        $found = Get-ChildItem -Path $fullDir -Filter $name -Recurse -File -ErrorAction SilentlyContinue
        foreach ($f in $found) {
            $relPath = $f.FullName.Substring($ProjectRoot.Length + 1) -replace '\\', '/'
            # HARDCODED: exclude active manifest itself
            if ($relPath -eq $selfPath) { continue }
            $files += $relPath
        }
    }
}

$files = $files | Sort-Object -Unique

# Apply manifest-ignore.txt
$ignorePath = Join-Path $ProjectRoot "governance\manifest-ignore.txt"
if (Test-Path $ignorePath) {
    $ignorePatterns = Get-Content $ignorePath | Where-Object { $_ -notmatch '^\s*(#|$)' } | ForEach-Object { $_.Trim() }
    $files = $files | Where-Object {
        $keep = $true
        foreach ($ip in $ignorePatterns) {
            # Convert glob to wildcard: ** matches any depth
            $wc = $ip -replace '\*\*/', '*' -replace '/', '/'
            if ($_ -like $wc) { $keep = $false; break }
        }
        $keep
    }
}

Write-Host "Files to hash: $($files.Count)"

# Calculate hashes
$sealed = @()
foreach ($file in $files) {
    $fullPath = Join-Path $ProjectRoot $file
    if (-not (Test-Path $fullPath)) { continue }
    try {
        $hash = (Get-FileHash -Path $fullPath -Algorithm SHA256).Hash
        $sealed += @{
            path = $file
            sha256 = $hash
        }
    } catch {
        Write-Warning "Cannot hash: $file — $($_.Exception.Message)"
    }
}

# Build manifest
$manifest = @{
    generated = (Get-Date -Format 'o')
    source = $ProjectRoot
    note = "Active manifest authority. hooks/sealed-files-manifest.json is self-excluded from hashing; protected by CODEOWNERS + branch protection."
    sealed_files = $sealed
    memory_paths = @(
        "$env:USERPROFILE\.claude\projects\D--agent-acceptance\memory\",
        "$env:USERPROFILE\.claude\memory\"
    )
    sealed_dirs = @("hooks/", "governance/")
}

$manifest | ConvertTo-Json -Depth 3 | Out-File -FilePath $manifestPath -Encoding utf8

Write-Host "Manifest updated: $manifestPath"
Write-Host "Sealed files: $($sealed.Count)"
exit 0
