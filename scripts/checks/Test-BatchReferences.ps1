<#
.SYNOPSIS
Verify that all batch JSON files in batches/ reference existing paths and modules.
#>
param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

Import-Module (Join-Path $PSScriptRoot "shared\GovernanceShared.psm1") -Force

$batchDir = Join-Path $ProjectRoot "batches"
if (-not (Test-Path $batchDir)) {
    return New-CheckResult -CheckName "BatchReferences" -Status "PASS" -Details @("No batches/ directory")
}

$violations = @()
$batchFiles = Get-ChildItem $batchDir -Filter "*.json" -File -ErrorAction SilentlyContinue

foreach ($bf in $batchFiles) {
    try {
        $batch = Get-Content $bf.FullName -Raw | ConvertFrom-Json
        if (-not $batch.tasks) { continue }

        foreach ($task in $batch.tasks) {
            $cmd = $task.command
            if (-not $cmd) { continue }

            # Check for .ps1 file references
            $scriptMatches = [regex]::Matches($cmd, 'scripts[/\\][^\s"]+\.ps1')
            foreach ($m in $scriptMatches) {
                $refPath = $m.Value -replace '\\', '/'
                $absPath = Join-Path $ProjectRoot $refPath
                if (-not (Test-Path $absPath)) {
                    $violations += "$($bf.Name):$($task.id): $refPath not found"
                }
            }

            # Check for src/ directory references
            if ($cmd -match '\bsrc\b') {
                $srcPath = Join-Path $ProjectRoot "src"
                if (-not (Test-Path $srcPath)) {
                    $violations += "$($bf.Name):$($task.id): references 'src/' which does not exist"
                }
            }

            # Check for module references
            if ($cmd -match 'python -m (\S+)') {
                $module = $Matches[1]
                $violations += "$($bf.Name):$($task.id): Python module '$module' — verify existence (not auto-checked)"
            }
        }
    } catch {
        $violations += "$($bf.Name): JSON parse error: $($_.Exception.Message)"
    }
}

if ($violations.Count -gt 0) {
    return New-CheckResult -CheckName "BatchReferences" -Status "BLOCKED" `
        -Details $violations `
        -Suggestion "Fix or remove non-existent batch references. Move future batches to batches/future/."
} else {
    return New-CheckResult -CheckName "BatchReferences" -Status "PASS" -Details @("All batch references valid")
}
