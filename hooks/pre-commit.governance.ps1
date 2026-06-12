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
$HookVersion = "2.4.0"

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
Write-Host "[1/4] Manifest auto-regeneration..."
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
Write-Host "[2/4] SADP audit..."
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
    # FAILURE SEMANTIC: ai_guard is BLOCKING (v2.3.0). Failure causes BLOCKED + exit 1.
    $aiGuardScript = Join-Path $ProjectRoot "tools\ai_guard.py"
    $aiGuardTimeoutSec = 30
    if (Test-Path $aiGuardScript) {
        Push-Location $ProjectRoot
        try {
            $timing = Invoke-WithTiming {
                $stagedFiles = git diff --cached --name-only 2>$null
                # v2.4.1: Pass file list via env var to avoid Windows cmdline length limit (~32K chars)
                $env:AI_GUARD_FILE_LIST = ($stagedFiles -join "`n")
                # Use Job for timeout enforcement
                $job = Start-Job -ScriptBlock {
                    param($scriptPath, $root)
                    Set-Location $root
                    $output = python $scriptPath --files 2>&1 | Out-String
                    # Return output and exit code as array (cross-process safe)
                    return @($output, $LASTEXITCODE)
                } -ArgumentList $aiGuardScript, $ProjectRoot

                $completed = Wait-Job $job -Timeout $aiGuardTimeoutSec
                $timedOut = ($null -eq $completed)
                if ($timedOut) {
                    Stop-Job $job -ErrorAction SilentlyContinue
                    Remove-Job $job -Force -ErrorAction SilentlyContinue
                    return @{
                        Output   = "TIMEOUT: ai_guard exceeded ${aiGuardTimeoutSec}s limit"
                        ExitCode = 1
                        TimedOut = $true
                    }
                }
                # Receive-Job returns the array: [output_string, exit_code]
                $jobResult = @(Receive-Job $job)
                $jobExitCode = $jobResult[-1]   # Last element = exit code
                $jobOutput = ($jobResult[0..($jobResult.Count - 2)]) -join "`n"
                Remove-Job $job -Force -ErrorAction SilentlyContinue
                # Null-safe: default to 1 (fail-closed)
                $exitCode = if ($null -ne $jobExitCode) { [int]$jobExitCode } else { 1 }
                return @{
                    Output   = $jobOutput
                    ExitCode = $exitCode
                    TimedOut = $false
                }
            }
            $aiGuardElapsedMs = $timing.ElapsedMs
            $aiGuardResult = $timing.Result

            # Extract values from cross-process result hashtable
            $aiGuardOutput = $aiGuardResult.Output
            $aiGuardExit = $aiGuardResult.ExitCode
            $aiGuardTimedOut = $aiGuardResult.TimedOut

            if ($aiGuardTimedOut) {
                $aiGuardOutput = "TIMEOUT: ai_guard exceeded ${aiGuardTimeoutSec}s limit"
                $aiGuardExit = 1
            }

            # Persist ai_guard output
            $aiHeader = "# AI Guard Output - $isoTimestamp`n# Exit code: $aiGuardExit (blocking)`n# Timeout: ${aiGuardTimeoutSec}s`n# Source: pre-commit hook (original)`n`n"
            $aiHeader + $aiGuardOutput | Out-File -FilePath $aiGuardOutputFile -Encoding utf8

            Write-Host "[ai_guard] $aiGuardOutput"
        } catch {
            $aiGuardOutput = "ERROR: $($_.Exception.Message)"
            $aiGuardExit = 1
            "# AI Guard Output - $isoTimestamp`n# Error during execution (blocking)`n`n$aiGuardOutput" | Out-File -FilePath $aiGuardOutputFile -Encoding utf8
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
Write-Host "[3/4] Governance scan..."
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

# ---- 4. Conversation Health Advisory (A3 Layer 4 — ADVISORY only) ----
Write-Host "[4/4] Conversation health advisory..."
$healthScript = Join-Path $ProjectRoot "scripts\pre_commit_health_advisory.py"
$healthOutputFile = Join-Path $evidenceDir "conversation-health-$timestamp.txt"
$healthElapsedMs = 0
$healthExit = 0

if (Test-Path $healthScript) {
    Push-Location $ProjectRoot
    try {
        $timing = Invoke-WithTiming {
            $healthOutput = python $healthScript --project-root $ProjectRoot 2>&1 | Out-String
            $healthOutput
        }
        $healthExit = $LASTEXITCODE
        $healthElapsedMs = $timing.ElapsedMs
        $healthOutputContent = $timing.Result

        # Persist conversation-health advisory output
        $healthHeader = "# Conversation Health Advisory - $isoTimestamp`n# Exit code: $healthExit (advisory)`n# Source: pre-commit hook v$HookVersion`n`n"
        $healthHeader + $healthOutputContent | Out-File -FilePath $healthOutputFile -Encoding utf8

        Write-Host $healthOutputContent
    } catch {
        $healthOutputContent = "ERROR: $($_.Exception.Message)"
        $healthExit = 0  # Advisory: fail-graceful, never blocks
        "# Conversation Health Advisory - $isoTimestamp`n# Error during execution (advisory)`n`n$healthOutputContent" | Out-File -FilePath $healthOutputFile -Encoding utf8
        Write-Host "[ADVISORY] Conversation health check had issues: $($_.Exception.Message)"
    } finally {
        Pop-Location
    }
} else {
    Write-Host "[ADVISORY] pre_commit_health_advisory.py not found - skipping."
    "# Conversation Health Advisory - $isoTimestamp`n# pre_commit_health_advisory.py not found - skipped`n" | Out-File -FilePath $healthOutputFile -Encoding utf8
}

# ---- Write combined JSON summary ----
$branch = git rev-parse --abbrev-ref HEAD 2>$null
$commitCount = (git rev-list --count HEAD 2>$null)
$stagedFileCount = (git diff --cached --name-only 2>$null | Measure-Object).Count

$stages = @(
    @{ name = "manifest-regen";        exit_code = $stage1Exit;   output_file = $null;                 duration_ms = 0 }
    @{ name = "sadp-audit";            exit_code = $auditExit;    output_file = $sadpOutputFile;       duration_ms = $sadpElapsedMs }
    @{ name = "ai-guard";              exit_code = $aiGuardExit;  output_file = $aiGuardOutputFile;    duration_ms = $aiGuardElapsedMs }
    @{ name = "test-governance";       exit_code = $govExit;      output_file = $govOutputFile;        duration_ms = $govElapsedMs }
    @{ name = "conversation-health";   exit_code = $healthExit;   output_file = $healthOutputFile;     duration_ms = $healthElapsedMs }
)

# Failure semantics (v2.4.0):
#   BLOCKING:   sadp-audit, ai-guard (any non-zero → BLOCKED + exit 1)
#   ADVISORY:   manifest-regen, test-governance, conversation-health (exit code logged, never blocks)
#   Test-Governance runs in advisory mode (-Mode advisory), so its exit code
#   does not affect the commit decision. conversation-health is advisory only (A3 Layer 4).
#   Only sadp-audit and ai-guard are enforcement gates with reliable process exit codes.
$overallResult = "PASS"
foreach ($s in $stages) {
    if ($s.exit_code -ne 0) {
        if ($s.name -eq "sadp-audit" -or $s.name -eq "ai-guard") {
            $overallResult = "BLOCKED"
            break
        }
        # manifest-regen, test-governance, conversation-health: advisory only
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
if ($overallResult -eq "BLOCKED") {
    Write-Host "=== Pre-Commit BLOCKED ==="
    Write-Host "[BLOCKED] A required governance stage failed."
    Write-Host "[evidence] Output captured to: $evidenceDir"
    exit 1
} else {
    Write-Host "=== Pre-Commit PASS ==="
    Write-Host "[evidence] Output captured to: $evidenceDir"
    exit 0
}
