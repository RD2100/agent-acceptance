<#
.SYNOPSIS
Check git diff for modifications to protected governance paths.
Returns: New-CheckResult (PASS if no protected paths modified, BLOCKED otherwise).
#>
param(
    [Parameter(Mandatory)]$ChangedFiles,
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

Import-Module (Join-Path $PSScriptRoot "shared\GovernanceShared.psm1") -Force

$protectedPatterns = @(
    "AGENTS\.md",
    "CLAUDE\.md",
    "rules/*",
    "hooks/*",
    ".ai/policy\.yaml",
    ".github/workflows/*",
    "schemas/agent-runtime/*",
    "docs/agent-runtime/sub-agent-dispatch-protocol\.md",
    "docs/agent-runtime/capability-inventory\.md",
    "docs/agent-runtime/governance-manifest\.md",
    "docs/agent-runtime/lessons-learned\.md",
    "docs/agent-runtime/verification-gates\.md",
    "docs/agent-runtime/operating-model\.md",
    "templates/runtime-bootstrap/*"
)

$violations = @()
foreach ($file in $ChangedFiles) {
    $normalized = $file -replace '\\', '/'
    foreach ($pat in $protectedPatterns) {
        if ($normalized -like $pat) {
            $violations += $normalized
            break
        }
    }
}

if ($violations.Count -gt 0) {
    function Test-PathCoveredByPattern {
        param([string]$FilePath, [string]$Pattern)

        $normalizedPath = $FilePath -replace '\\', '/'
        $normalizedPattern = $Pattern -replace '\\', '/'
        if ($normalizedPattern -eq $normalizedPath) { return $true }
        if ($normalizedPattern.EndsWith('/**')) {
            $prefix = $normalizedPattern.Substring(0, $normalizedPattern.Length - 3)
            return $normalizedPath.StartsWith($prefix + '/')
        }
        try {
            $wildcard = [System.Management.Automation.WildcardPattern]::new(
                $normalizedPattern,
                [System.Management.Automation.WildcardOptions]::IgnoreCase
            )
            return $wildcard.IsMatch($normalizedPath)
        } catch {
            return $false
        }
    }

    function Test-TaskSpecCoversViolations {
        param([string[]]$ViolationPaths)

        $taskFiles = @()
        if (Test-Path (Join-Path $ProjectRoot "tasks")) {
            $taskFiles += @(Get-ChildItem (Join-Path $ProjectRoot "tasks") -Filter "t-*.json" -ErrorAction SilentlyContinue)
        }
        if (Test-Path (Join-Path $ProjectRoot ".ai\current-task.yaml")) {
            $taskFiles += @(Get-Item (Join-Path $ProjectRoot ".ai\current-task.yaml"))
        }

        foreach ($taskFile in $taskFiles) {
            $content = Get-Content $taskFile.FullName -Raw -ErrorAction SilentlyContinue
            $patterns = @()
            if ($taskFile.Extension -eq ".json") {
                try {
                    $json = $content | ConvertFrom-Json -ErrorAction Stop
                    $patterns += @($json.allow_write)
                    $patterns += @($json.write_set)
                    if ($json.conflict_registry) {
                        $patterns += @($json.conflict_registry.write_set)
                    }
                } catch {
                    continue
                }
            } else {
                $matches = [regex]::Matches($content, '(?m)^\s*-\s+["'']?([^"''\r\n]+)["'']?\s*$')
                foreach ($match in $matches) {
                    $patterns += $match.Groups[1].Value.Trim()
                }
            }

            $patterns = @($patterns | Where-Object { $_ } | ForEach-Object { $_ -replace '\\', '/' })
            if ($patterns.Count -eq 0) { continue }

            $allCovered = $true
            foreach ($violation in $ViolationPaths) {
                $covered = $false
                foreach ($pattern in $patterns) {
                    if (Test-PathCoveredByPattern -FilePath $violation -Pattern $pattern) {
                        $covered = $true
                        break
                    }
                }
                if (-not $covered) {
                    $allCovered = $false
                    break
                }
            }
            if ($allCovered) { return $taskFile.Name }
        }
        return $null
    }

    function Test-ReviewerEvidenceExists {
        $runsDir = Join-Path $ProjectRoot "runs"
        $guard = Join-Path $ProjectRoot "tools\ai_guard.py"
        if ((-not (Test-Path $runsDir)) -or (-not (Test-Path $guard))) { return $false }

        $runDirs = @(Get-ChildItem $runsDir -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object {
            Test-Path (Join-Path $_.FullName "review.yaml")
        })
        foreach ($dir in $runDirs) {
            $result = & python $guard evidence $dir.FullName 2>&1
            if ($LASTEXITCODE -eq 0) { return $true }
        }
        return $false
    }

    $coveringTask = Test-TaskSpecCoversViolations -ViolationPaths $violations
    $hasReviewerEvidence = Test-ReviewerEvidenceExists
    if ($coveringTask -and $hasReviewerEvidence) {
        return New-CheckResult -CheckName "ProtectedPaths" -Status "PASS" `
            -Details @("Protected paths covered by TaskSpec: $coveringTask", "Independent reviewer evidence: PASS") `
            -Suggestion "Governance protected-path changes admitted through SADP evidence."
    }

    return New-CheckResult -CheckName "ProtectedPaths" -Status "BLOCKED" `
        -Details $violations `
        -Suggestion "Governance files modified. Require TaskSpec coverage plus independent reviewer evidence."
} else {
    return New-CheckResult -CheckName "ProtectedPaths" -Status "PASS"
}
