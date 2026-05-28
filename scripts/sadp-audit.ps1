# sadp-audit.ps1 ¡ª External SADP Compliance Auditor
# ==================================================
# Runs INDEPENDENTLY of Plan Agent decision.
# Triggered by git pre-commit hook.
# Checks: git diff ¡ú TaskSpec existence ¡ú Audit Record existence.
#
# Usage: .\sadp-audit.ps1 [-ProjectRoot <path>] [-Strict]
# Exit 0: PASS (compliant or no changes)
# Exit 1: FAIL (SADP required but artifacts missing)
# Exit 2: WARN (minor issues, non-blocking)

param(
    [string]$ProjectRoot = ".",
    [switch]$Strict
)

$ErrorActionPreference = "Stop"
Push-Location $ProjectRoot

try {
    # Collect git state
    $changedFiles = @(git -c core.safecrlf=false diff --cached --name-only 2>$null | Where-Object { $_ })
    $changedCount = $changedFiles.Count

    # No changes staged ¡ú pass
    if ($changedCount -eq 0) {
        Write-Host "[SADP-AUDIT] No staged changes. PASS."
        exit 0
    }

    Write-Host "[SADP-AUDIT] Staged files: $changedCount"

    # Classify changes
    $governancePatterns = @(
        "AGENTS\.md$", "CLAUDE\.md$",
        "rules\\", "docs\\agent-runtime\\sub-agent-dispatch-protocol",
        "docs\\agent-runtime\\capability-inventory",
        "docs\\agent-runtime\\lessons-learned",
        "docs\\agent-runtime\\session-ledger",
        "docs\\agent-runtime\\audit-record",
        "docs\\agent-runtime\\governance-manifest",
        "docs\\agent-runtime\\dependency-canaries",
        "schemas\\agent-runtime\\",
        "templates\\runtime-bootstrap\\",
        "hooks\\"
    )

    $governanceTouched = $false
    foreach ($f in $changedFiles) {
        foreach ($p in $governancePatterns) {
            if ($f -match $p) {
                $governanceTouched = $true
                Write-Host "[SADP-AUDIT]   Governance file: $f"
                break
            }
        }
    }

    # Check for TaskSpecs
    $taskDir = "tasks"
    $taskSpecs = @()
    if (Test-Path $taskDir) {
        $taskSpecs = @(Get-ChildItem $taskDir -Filter "task-*.md" -ErrorAction SilentlyContinue)
    }

    # Check for Audit Records
    $auditDir = "tasks"  # Audit records stored alongside TaskSpecs for now
    $auditRecords = @()
    if (Test-Path $auditDir) {
        $auditRecords = @(Get-ChildItem $auditDir -Filter "execution-report-*.md" -ErrorAction SilentlyContinue)
    }

    Write-Host "[SADP-AUDIT] TaskSpecs found: $($taskSpecs.Count)"
    Write-Host "[SADP-AUDIT] ExecutionReports found: $($auditRecords.Count)"

    
# ================================================================
# V2: Cross-reference TaskSpec write_set with changed files
# ================================================================
function Test-TaskSpecCoverage {
    param([string[]]$ChangedFiles, [string]$TaskDir)
    
    $uncovered = @()
    $coveredBy = @{}
    
    $taskFiles = @(Get-ChildItem $TaskDir -Filter "task-*.md" -ErrorAction SilentlyContinue)
    if ($taskFiles.Count -eq 0) { return @{ Uncovered = $ChangedFiles; CoveredBy = @{} } }
    
    foreach ($f in $ChangedFiles) {
        $found = $false
        foreach ($tf in $taskFiles) {
            $content = Get-Content $tf.FullName -Raw -ErrorAction SilentlyContinue
            $fileName = Split-Path $f -Leaf
            $filePath = $f -replace '\\', '/'
            
            # Check if file appears in write_set or Allowed Files
            if (($content -match "write_set:") -and ($content -match [regex]::Escape($fileName) -or $content -match [regex]::Escape($filePath))) {
                $found = $true
                if (-not $coveredBy.ContainsKey($f)) { $coveredBy[$f] = @() }
                $coveredBy[$f] += $tf.Name
                break
            }
        }
        if (-not $found) { $uncovered += $f }
    }
    
    return @{ Uncovered = $uncovered; CoveredBy = $coveredBy }
}

# Only run V2 check when TaskSpecs exist
if ($taskSpecs.Count -gt 0) {
    $coverage = Test-TaskSpecCoverage -ChangedFiles $changedFiles -TaskDir $taskDir
    
    if ($coverage.Uncovered.Count -gt 0) {
        Write-Host "[SADP-AUDIT] WARN: $($coverage.Uncovered.Count) file(s) not covered by any TaskSpec write_set:"
        foreach ($u in $coverage.Uncovered) {
            Write-Host "[SADP-AUDIT]   UNCOVERED: $u"
        }
        Write-Host "[SADP-AUDIT]   Ensure each changed file is listed in a TaskSpec write_set or Allowed Files."
        
        if ($Strict) {
            $block = $true
        }
    } else {
        Write-Host "[SADP-AUDIT] V2: All $($changedFiles.Count) files covered by TaskSpec write_sets."
    }
    
    # Show coverage summary
    if ($coverage.CoveredBy.Count -gt 0) {
        Write-Host "[SADP-AUDIT] Coverage map:"
        foreach ($f in $coverage.CoveredBy.Keys | Sort-Object) {
            Write-Host "[SADP-AUDIT]   $f -> $($coverage.CoveredBy[$f] -join ', ')"
        }
    }
}

# Decision logic

$block = $false
    $warn = $false

    # RULE 1: 3+ files ¡ú SADP required ¡ú TaskSpec must exist
    if ($changedCount -ge 3 -and $taskSpecs.Count -eq 0) {
        Write-Host "[SADP-AUDIT] FAIL: $changedCount files changed but no TaskSpec found."
        Write-Host "[SADP-AUDIT]   SADP ¡ì0.0: 3+ modified files triggers mandatory SADP workflow."
        Write-Host "[SADP-AUDIT]   Remediation: Create a TaskSpec in tasks/ with gate_0 evidence."
        Write-Host "[SADP-AUDIT]   Then create an ExecutionReport after task completion."
        $block = $true
    }

    # RULE 2: Governance files ¡ú Audit Record must exist
    if ($governanceTouched -and $auditRecords.Count -eq 0) {
        Write-Host "[SADP-AUDIT] FAIL: Governance files changed but no ExecutionReport found."
        Write-Host "[SADP-AUDIT]   SADP ¡ì3.3a: Plan Auditor requires Audit Record for governance changes."
        Write-Host "[SADP-AUDIT]   Remediation: Create ExecutionReport with Trust Record."
        $block = $true
    }

    # RULE 3: Strict mode ¡ª any change requires TaskSpec
    if ($Strict -and $changedCount -gt 0 -and $taskSpecs.Count -eq 0) {
        Write-Host "[SADP-AUDIT] FAIL (strict mode): Files changed but no TaskSpec."
        $block = $true
    }

    # RULE 4: TaskSpec exists but no ExecutionReport ¡ú warn
    if ($taskSpecs.Count -gt 0 -and $auditRecords.Count -eq 0 -and $changedCount -gt 0) {
        Write-Host "[SADP-AUDIT] WARN: TaskSpec exists but no ExecutionReport yet."
        Write-Host "[SADP-AUDIT]   Ensure ExecutionReport is created before finalizing."
        $warn = $true
    }

    if ($block) {
        Write-Host "[SADP-AUDIT] STATUS: BLOCKED"
        Write-Host "[SADP-AUDIT] Commit rejected. Fix the issues above and retry."
        Write-Host "[SADP-AUDIT] (Use --no-verify only with explicit human approval per core-001)"
        exit 1
    }

    if ($warn) {
        Write-Host "[SADP-AUDIT] STATUS: PASS (with warnings)"
    } else {
        Write-Host "[SADP-AUDIT] STATUS: PASS"
    }
    exit 0
}
finally {
    Pop-Location
}
