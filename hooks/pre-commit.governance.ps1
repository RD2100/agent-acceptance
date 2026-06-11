# pre-commit.governance.ps1 - Pre-commit governance gate.
# Runs: manifest auto-regen -> sadp-audit -> advisory governance scan.
# Order matters: regenerate manifest first so sadp-audit checks current state.
# Only git adds manifest files. Never use git add .
# Exit 0: allow commit. Exit 1: block commit.
#
# Evidence capture: Each stage output is persisted to _evidence/hook-output/
# for downstream evidence pack consumption. These files are NOT git-added.

$ErrorActionPreference = 'Continue'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$HookVersion = "2.2.0"

Write-Host "=== Pre-Commit Governance Gate (v$HookVersion) ==="

# ---- Evidence output directory ----
$evidenceDir = Join-Path $ProjectRoot "_evidence\hook-output"
if (-not (Test-Path $evidenceDir)) {
    New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
}
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$isoTimestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

# Helper: measure elapsed milliseconds
function Invoke-WithTiming {
    param([scriptblock]$Action)
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $result = & $Action
    $sw.Stop()
    return @{ Result = $result; ElapsedMs = $sw.ElapsedMilliseconds }
}

# ---- 1. Manifest auto-regeneration (before audit) ----
Write-Host "[1/3] Manifest auto-regeneration..."
$updateScript = Join-Path $ProjectRoot "scripts\Update-GovernanceManifest.ps1"
$manifestPath = "hooks\sealed-files-manifest.json"

$stage1Exit = 0
Push-Location $ProjectRoot
try {
    $before = if (Test-Path $manifestPath) { Get-Content $manifestPath -Raw } else { "" }

    if (Test-Path $updateScript) {
        & powershell -ExecutionPolicy Bypass -File $updateScript | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[WARN] Manifest regeneration had issues (exit=$LASTEXITCODE)"
            $stage1Exit = $LASTEXITCODE
        }
    } else {
        Write-Host "[WARN] Update-GovernanceManifest.ps1 not found - continuing."
    }

    $after = if (Test-Path $manifestPath) { Get-Content $manifestPath -Raw } else { "" }

    if ($before -ne $after) {
        git add $manifestPath 2>$null
        Write-Host "[OK] Manifest regenerated and staged for this commit."
    } else {
        Write-Host "[OK] Manifest already up to date."
    }
} finally {
    Pop-Location
}
Write-Host ""

# ---- 2. SADP audit ----
Write-Host "[2/3] SADP audit..."
$auditScript = Join-Path $ProjectRoot "scripts\sadp-audit.ps1"
$sadpOutputFile = Join-Path $evidenceDir "sadp-audit-$timestamp.txt"
$aiGuardOutputFile = Join-Path $evidenceDir "ai-guard-$timestamp.txt"
$auditExit = 0
$sadpElapsedMs = 0
$aiGuardElapsedMs = 0

if (Test-Path $auditScript) {
    Push-Location $ProjectRoot
    try {
        # Capture sadp-audit output (stdout + stderr)
        $timing = Invoke-WithTiming {
            $output = & powershell -ExecutionPolicy Bypass -File $auditScript 2>&1 | Out-String
            $output
        }
        $auditExit = $LASTEXITCODE
        $sadpElapsedMs = $timing.ElapsedMs
        $sadpOutput = $timing.Result

        # Persist sadp-audit output
        $sadpHeader = "# SADP Audit Output - $isoTimestamp`n# Exit code: $auditExit`n# Source: pre-commit hook (original)`n`n"
        $sadpHeader + $sadpOutput | Out-File -FilePath $sadpOutputFile -Encoding utf8

        # Also display to console (preserves existing behavior)
        Write-Host $sadpOutput
    } finally {
        Pop-Location
    }

    # Run ai_guard.py separately if it exists
    # FAILURE SEMANTIC: ai_guard is NON-BLOCKING. Failure produces PASS_WITH_WARNINGS.
    $aiGuardScript = Join-Path $ProjectRoot "tools\ai_guard.py"
    $aiGuardTimeoutSec = 30
    if (Test-Path $aiGuardScript) {
        Push-Location $ProjectRoot
        try {
            $timing = Invoke-WithTiming {
                $stagedFiles = git diff --cached --name-only 2>$null
                # Use Job for timeout enforcement
                $job = Start-Job -ScriptBlock {
                    param($scriptPath, $files, $root)
                    Set-Location $root
                    python $scriptPath --files $files 2>&1 | Out-String
                } -ArgumentList $aiGuardScript, $stagedFiles, $ProjectRoot

                $completed = Wait-Job $job -Timeout $aiGuardTimeoutSec
                if ($null -eq $completed) {
                    # Timeout — kill job and report
                    Stop-Job $job -ErrorAction SilentlyContinue
                    Remove-Job $job -Force -ErrorAction SilentlyContinue
                    $script:aiGuardTimedOut = $true
                    return "TIMEOUT: ai_guard exceeded ${aiGuardTimeoutSec}s limit"
                }
                $jobOutput = Receive-Job $job
                Remove-Job $job -Force -ErrorAction SilentlyContinue
                # Job exit code is not directly available; check output for error indicators
                $script:aiGuardTimedOut = $false
                return $jobOutput
            }
            $aiGuardElapsedMs = $timing.ElapsedMs
            $aiGuardOutput = $timing.Result

            # Determine exit code: timeout = 1, otherwise check output
            if ($aiGuardTimedOut) {
                $aiGuardExit = 1
                $aiGuardOutput = "TIMEOUT: ai_guard exceeded ${aiGuardTimeoutSec}s limit"
            } else {
                # ai_guard.py prints "PASS" or "FAIL" — use output heuristic
                if ($aiGuardOutput -match "(?i)\bFAIL\b") {
                    $aiGuardExit = 1
                } else {
                    $aiGuardExit = 0
                }
            }

            # Persist ai_guard output
            $aiHeader = "# AI Guard Output - $isoTimestamp`n# Exit code: $aiGuardExit (non-blocking)`n# Timeout: ${aiGuardTimeoutSec}s`n# Source: pre-commit hook (original)`n`n"
            $aiHeader + $aiGuardOutput | Out-File -FilePath $aiGuardOutputFile -Encoding utf8

            Write-Host "[ai_guard] $aiGuardOutput"
        } catch {
            $aiGuardOutput = "ERROR: $($_.Exception.Message)"
            $aiGuardExit = 1
            "# AI Guard Output - $isoTimestamp`n# Error during execution (non-blocking)`n`n$aiGuardOutput" | Out-File -FilePath $aiGuardOutputFile -Encoding utf8
            Write-Host "[WARN] ai_guard execution failed: $($_.Exception.Message)"
        } finally {
            Pop-Location
        }
    } else {
        Write-Host "[INFO] ai_guard.py not found - skipping AI guard check."
        "# AI Guard - $isoTimestamp`n# ai_guard.py not found - skipped`n" | Out-File -FilePath $aiGuardOutputFile -Encoding utf8
    }

    if ($auditExit -ne 0) {
        Write-Host "[BLOCKED] sadp-audit failed (exit=$auditExit). Fix issues before commit."

        # Still write JSON summary even on block
        $overallResult = "BLOCKED"
        $stages = @(
            @{ name = "manifest-regen";  exit_code = $stage1Exit;   output_file = $null;                duration_ms = 0 }
            @{ name = "sadp-audit";       exit_code = $auditExit;    output_file = $sadpOutputFile;      duration_ms = $sadpElapsedMs }
            @{ name = "ai-guard";         exit_code = $aiGuardExit;  output_file = $aiGuardOutputFile;   duration_ms = $aiGuardElapsedMs }
        )
        $branch = git rev-parse --abbrev-ref HEAD 2>$null
        $commitCount = (git rev-list --count HEAD 2>$null)
        $stagedFileCount = (git diff --cached --name-only 2>$null | Measure-Object).Count
        $jsonSummary = @{
            timestamp      = $isoTimestamp
            hook_version   = $HookVersion
            stages         = $stages
            git_context    = @{
                branch            = $branch
                commit_count      = [int]$commitCount
                staged_file_count = $stagedFileCount
            }
            overall_result = $overallResult
        } | ConvertTo-Json -Depth 5
        $jsonSummary | Out-File -FilePath (Join-Path $evidenceDir "latest.json") -Encoding utf8

        exit 1
    }
} else {
    Write-Host "[WARN] sadp-audit.ps1 not found - skipping."
    "# SADP Audit - $isoTimestamp`n# sadp-audit.ps1 not found - skipped`n" | Out-File -FilePath $sadpOutputFile -Encoding utf8
}
Write-Host ""

# ---- 3. Advisory governance scan ----
Write-Host "[3/3] Governance advisory..."
$governanceScript = Join-Path $ProjectRoot "scripts\Test-Governance.ps1"
$govOutputFile = Join-Path $evidenceDir "test-governance-$timestamp.txt"
$govElapsedMs = 0
$govExit = 0

if (Test-Path $governanceScript) {
    Push-Location $ProjectRoot
    try {
        $timing = Invoke-WithTiming {
            $govOutput = & powershell -ExecutionPolicy Bypass -File $governanceScript -Mode advisory 2>&1 | Out-String
            $govOutput
        }
        $govExit = $LASTEXITCODE
        $govElapsedMs = $timing.ElapsedMs
        $govOutputContent = $timing.Result

        # Persist Test-Governance output
        $govHeader = "# Test-Governance Output - $isoTimestamp`n# Exit code: $govExit`n# Source: pre-commit hook (original)`n`n"
        $govHeader + $govOutputContent | Out-File -FilePath $govOutputFile -Encoding utf8

        # Also display to console (preserves existing behavior)
        Write-Host $govOutputContent
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[WARN] Test-Governance.ps1 not found - skipping advisory scan."
    "# Test-Governance - $isoTimestamp`n# Test-Governance.ps1 not found - skipped`n" | Out-File -FilePath $govOutputFile -Encoding utf8
}

# ---- Write combined JSON summary ----
$branch = git rev-parse --abbrev-ref HEAD 2>$null
$commitCount = (git rev-list --count HEAD 2>$null)
$stagedFileCount = (git diff --cached --name-only 2>$null | Measure-Object).Count

$stages = @(
    @{ name = "manifest-regen";   exit_code = $stage1Exit;   output_file = $null;               duration_ms = 0 }
    @{ name = "sadp-audit";       exit_code = $auditExit;    output_file = $sadpOutputFile;     duration_ms = $sadpElapsedMs }
    @{ name = "ai-guard";         exit_code = $aiGuardExit;  output_file = $aiGuardOutputFile;  duration_ms = $aiGuardElapsedMs }
    @{ name = "test-governance";  exit_code = $govExit;      output_file = $govOutputFile;      duration_ms = $govElapsedMs }
)

# Failure semantics (v2.2.0):
#   BLOCKING:   sadp-audit (exit 1 → hook exits 1, commit rejected)
#   WARNING:    ai-guard (exit non-zero → PASS_WITH_WARNINGS, commit allowed)
#   ADVISORY:   manifest-regen, test-governance (exit code logged, never blocks)
$overallResult = "PASS"
foreach ($s in $stages) {
    if ($s.exit_code -ne 0) {
        if ($s.name -eq "sadp-audit") {
            # Sole blocking gate — handled earlier with exit 1
            $overallResult = "BLOCKED"
            break
        } elseif ($s.name -eq "ai-guard") {
            # Non-blocking: downgrade to PASS_WITH_WARNINGS
            if ($overallResult -eq "PASS") {
                $overallResult = "PASS_WITH_WARNINGS"
            }
        }
        # manifest-regen and test-governance: purely advisory, no effect on result
    }
}

$jsonSummary = @{
    timestamp      = $isoTimestamp
    hook_version   = $HookVersion
    stages         = $stages
    git_context    = @{
        branch            = $branch
        commit_count      = [int]$commitCount
        staged_file_count = $stagedFileCount
    }
    overall_result = $overallResult
} | ConvertTo-Json -Depth 5

$jsonSummary | Out-File -FilePath (Join-Path $evidenceDir "latest.json") -Encoding utf8

Write-Host ""
if ($overallResult -eq "PASS_WITH_WARNINGS") {
    Write-Host "=== Pre-Commit PASS (with warnings) ==="
    Write-Host "[WARN] Non-blocking stage(s) had issues — review _evidence/hook-output/ for details."
} else {
    Write-Host "=== Pre-Commit PASS ==="
}
Write-Host "[evidence] Output captured to: $evidenceDir"
exit 0
