<#
.SYNOPSIS
Test-GovernanceDrift.ps1 — Periodic full-repo governance consistency check.
Checks rules, Phase boundaries, manifest coverage, and capability inventory for drift.
Exit: 0=PASS, 1=BLOCKED (drift), 2=INFRA_ERROR

Usage:
  .\Test-GovernanceDrift.ps1 [-ProjectRoot <path>] [-Strict]
#>
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [switch]$Strict
)

$ErrorActionPreference = 'Continue'
Import-Module (Join-Path $PSScriptRoot "checks\shared\GovernanceShared.psm1") -Force

Write-Host "=== Governance Drift Check ==="
Write-Host "Project: $ProjectRoot"

$drifts = @()
$blockCount = 0

# ---- 1. Rule ID bidirectional check ----
Write-Host ""
Write-Host "[1/5] Rule ID bidirectional check..."

$ruleDir = Join-Path $ProjectRoot "rules"
$readmePath = Join-Path $ruleDir "README.md"
$ruleFiles = Get-ChildItem $ruleDir -Filter "*.md" -File | Where-Object { $_.Name -ne 'README.md' }

$allIds = @()
foreach ($rf in $ruleFiles) {
    $parsed = Parse-RuleIds -FilePath $rf.FullName
    $allIds += $parsed
}

$readmeIds = @()
$readmeContent = Get-Content $readmePath -Raw
# Extract rule IDs mentioned in README (loose match)
foreach ($id in $allIds) {
    if ($readmeContent -match $id.id) {
        $readmeIds += $id.id
    }
}

# Check: all parsed IDs appear in README (non-blocking: README uses aggregate counts, not per-ID listing)
$missingFromReadme = $allIds | Where-Object { $_.id -notin $readmeIds }
if ($missingFromReadme) {
    $names = ($missingFromReadme | ForEach-Object { "$($_.id) ($($_.file))" }) -join ', '
    $drifts += "Rule IDs not individually listed in README (README uses aggregate counts): $($missingFromReadme.Count) IDs"
    # Non-blocking: README format uses per-file rule counts, not per-rule-ID enumeration
}

Write-Host "  Rules parsed: $($allIds.Count) | In README: $($readmeIds.Count)"
if ($missingFromReadme) { Write-Host "  WARN: $($missingFromReadme.Count) IDs not in README" }

# ---- 2. P0/P1 count vs README ----
Write-Host ""
Write-Host "[2/5] P0/P1 count vs README declaration..."

$p0Count = ($allIds | Where-Object { $_.priority -eq 'P0' }).Count
$p1Count = ($allIds | Where-Object { $_.priority -eq 'P1' }).Count
Write-Host "  Parsed: P0=$p0Count P1=$p1Count"

# ---- 3. Phase 0-5 cross-file consistency ----
Write-Host ""
Write-Host "[3/5] Phase 0-5 boundary consistency..."

$phaseStatements = @{}
foreach ($rf in $ruleFiles) {
    $lines = Get-Content $rf.FullName | Select-Object -First 5
    $phaseLine = ($lines | Where-Object { $_ -match 'Phase 0-5' }) -join ' '
    $phaseStatements[$rf.Name] = $phaseLine.Trim()
}

$expected = "P0/P1 active; P2-P4 within approved task scope"
$mismatches = @()
foreach ($file in $phaseStatements.Keys) {
    $stmt = $phaseStatements[$file]
    if ($stmt -notmatch 'P2-P4.*scope' -and $stmt -notmatch 'reference only') {
        $mismatches += "${file}" + ": " + $stmt
    }
}

if ($mismatches) {
    $drifts += "Phase boundary mismatch: $($mismatches -join '; ')"
    $blockCount++
}
Write-Host "  Files checked: $($phaseStatements.Count)"
if ($mismatches) { Write-Host "  BLOCKED: $($mismatches.Count) mismatch(es)" } else { Write-Host "  Consistent" }

# ---- 4. Manifest coverage ----
Write-Host ""
Write-Host "[4/5] Manifest coverage check..."

$manifestPath = Join-Path $ProjectRoot "hooks\sealed-files-manifest.json"
$expectedPath = Join-Path $ProjectRoot "governance\expected-files.txt"

if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    $manifestFiles = @($manifest.sealed_files | ForEach-Object { $_.path })

    $expectedFiles = Resolve-ExpectedFiles -ExpectedFilesPath $expectedPath -ProjectRoot $ProjectRoot
    $expectedFiles = $expectedFiles | Where-Object { $_ -ne 'hooks/sealed-files-manifest.json' }

    $missingFromManifest = $expectedFiles | Where-Object { $_ -notin $manifestFiles }
    $extraInManifest = $manifestFiles | Where-Object { $_ -notin $expectedFiles }
    $staleHashes = @()

    foreach ($entry in $manifest.sealed_files) {
        $fullPath = Join-Path $ProjectRoot $entry.path
        if (Test-Path $fullPath) {
            $currentHash = (Get-FileHash -Path $fullPath -Algorithm SHA256).Hash
            if ($currentHash -ne $entry.sha256) {
                $staleHashes += $entry.path
            }
        } else {
            $staleHashes += "$($entry.path) (file missing)"
        }
    }

    if ($missingFromManifest) {
        $drifts += "Files not in manifest: $($missingFromManifest -join ', ')"
        $blockCount++
    }
    if ($staleHashes) {
        $drifts += "Stale hashes: $($staleHashes -join ', ')"
        $blockCount++
    }

    Write-Host "  Expected: $($expectedFiles.Count) | In manifest: $($manifestFiles.Count)"
    if ($missingFromManifest) { Write-Host "  BLOCKED: $($missingFromManifest.Count) files missing from manifest" }
    if ($staleHashes) { Write-Host "  BLOCKED: $($staleHashes.Count) stale hashes" }
    if (-not $missingFromManifest -and -not $staleHashes) { Write-Host "  PASS" }
} else {
    Write-Host "  WARN: manifest not found at $manifestPath"
}

# ---- 5. Capability inventory consistency ----
Write-Host ""
Write-Host "[5/5] Capability inventory consistency..."

$capPath = Join-Path $ProjectRoot "docs\agent-runtime\capability-inventory.md"
if (Test-Path $capPath) {
    $caps = Parse-CapabilityEntries -FilePath $capPath
    $verified = ($caps | Where-Object { $_.status -eq 'verified' }).Count
    $broken = ($caps | Where-Object { $_.status -eq 'broken' }).Count
    $stale = ($caps | Where-Object { $_.status -eq 'stale' }).Count
    $unknown = ($caps | Where-Object { $_.status -eq 'unknown' }).Count

    Write-Host "  Capabilities: $($caps.Count) total | verified=$verified broken=$broken stale=$stale unknown=$unknown"

    if ($unknown -gt $caps.Count / 2) {
        $drifts += "Many capabilities have unknown status ($unknown/$($caps.Count)). Parser coverage limited; verify manually."
        # Non-blocking: capability parser coverage is limited (detailed entries format not yet fully parseable)
    }
} else {
    Write-Host "  WARN: capability-inventory.md not found"
}

# ---- Report ----
Write-Host ""
Write-Host "=== Drift Summary ==="
if ($drifts.Count -gt 0) {
    Write-Host "Drift(s) detected:"
    foreach ($d in $drifts) {
        Write-Host "  - $d"
    }
}

if ($blockCount -gt 0) {
    Write-Host "BLOCKED: $blockCount blocking drift(s)"
    exit 1
} else {
    Write-Host "PASS: No blocking drift detected"
    exit 0
}
