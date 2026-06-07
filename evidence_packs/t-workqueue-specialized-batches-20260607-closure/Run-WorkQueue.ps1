<#
.SYNOPSIS
WorkQueue Runner — executes pending queue items via Run-Batch.ps1.
Tier 2 items are skipped (escalated). Forbidden runners/commands blocked.
Exit: 0=PASS, 1=BLOCKED/ESCALATED, 2=FAILED
#>
param(
    [Parameter(Mandatory)][string]$QueueFile,
    [string]$RunsBase = 'runs/powershell-acceptance/workqueue'
)

$ErrorActionPreference = 'Continue'
$script:qStart = Get-Date
Import-Module (Join-Path $PSScriptRoot "lib\Process.psm1") -Force

# ---- Load queue ----
if (-not (Test-Path $QueueFile)) {
    Write-Host "FATAL: queue file not found: $QueueFile"
    exit 2
}
$queue = Get-Content $QueueFile -Raw | ConvertFrom-Json
$qid = $queue.queue_id
$qdir = Join-Path $RunsBase $qid
New-Item -ItemType Directory -Force -Path $qdir | Out-Null

Write-Host "=== WorkQueue: $qid ==="
Write-Host "Mode: $($queue.mode) | Items: $($queue.items.Count)"
Write-Host "Output: $qdir"
Write-Host ""

# ---- Allowed runners (security) ----
$allowedRunners = @(
    'scripts/Run-Batch.ps1'
)

$script:forbidden = @(
    'git push', 'git reset --hard', 'git clean', 'rm -rf',
    'Remove-Item -Recurse', 'cleanup --apply', 'review-recovered --apply',
    'AIHUB_PLANNER_TIMEOUT_SECONDS', 'AIHUB_SYSTEM_TIMEOUT_SECONDS'
)

function IsForbidden($cmd) {
    foreach ($pat in $script:forbidden) {
        if ($cmd -match $pat) { return $true }
    }
    return $false
}

# ---- Execute pending items ----
$itemResults = [System.Collections.ArrayList]::new()
$executed = 0

foreach ($item in $queue.items) {
    $iid = [string]$item.id
    if (-not $iid) { $iid = "item-$([Guid]::NewGuid().ToString('N').Substring(0,8))" }
    $idir = Join-Path $qdir ('items') | Join-Path -ChildPath $iid
    New-Item -ItemType Directory -Force -Path $idir | Out-Null
    $t0 = Get-Date

    # Skip non-pending
    if ($item.status -ne 'pending') {
        Write-Host "[$iid] skipped (status=$($item.status))"
        [void]$itemResults.Add(@{
            id = $iid; status = 'skipped'; verdict = 'SKIPPED'
            reason = "status is $($item.status), not pending"
            duration = 0
        })
        continue
    }

    # Tier 2 must escalate
    if ($item.tier -eq 2) {
        Write-Host "[$iid] escalated (Tier 2 not auto-executable)"
        [void]$itemResults.Add(@{
            id = $iid; status = 'escalated'; verdict = 'ESCALATED'
            reason = 'Tier 2 requires manual review or user ACK'
            duration = 0
        })
        continue
    }

    # Validate runner
    $runner = $item.runner
    if ($runner -notin $allowedRunners) {
        Write-Host "[$iid] blocked (runner not in allowlist: $runner)"
        [void]$itemResults.Add(@{
            id = $iid; status = 'blocked'; verdict = 'BLOCKED'
            reason = "runner not allowed: $runner"
            duration = 0
        })
        continue
    }

    # Forbidden metadata check (title, name, description)
    $metaText = "$($item.title) $($item.name) $($item.description)"
    if (IsForbidden $metaText) {
        Write-Host " [BLOCKED] forbidden in metadata"
        [void]$itemResults.Add(@{
            id = $iid; status = 'blocked'; verdict = 'BLOCKED'
            reason = 'forbidden pattern in item metadata (title/name/description)'
            duration = 0
        })
        continue
    }

    # Execute
    Write-Host "[$iid] $($item.title)" -NoNewline
    try {
        $taskFile = $item.task_file
        $cmd = "powershell -ExecutionPolicy Bypass -File $runner -TaskFile $taskFile"
        if (IsForbidden $cmd) {
            Write-Host " [BLOCKED] forbidden command"
            [void]$itemResults.Add(@{
                id = $iid; status = 'escalated'; verdict = 'ESCALATED'
                reason = 'forbidden command pattern detected'
                duration = 0
            })
            continue
        }

        $result = Invoke-CheckedCommand -Command $cmd -OutputDir $idir `
            -WorkingDirectory (Get-Location).Path -TimeoutSeconds 300

        if ($result.TimedOut) {
            Write-Host " [FAILED] timeout"
            [void]$itemResults.Add(@{
                id = $iid; status = 'failed'; verdict = 'FAILED'
                reason = 'timeout after 300s'
                duration = 300
            })
            continue
        }

        $ec = $result.ExitCode
        $ts = $result.Duration
        $executed++

        # Check expected artifacts
        $missing = @()
        foreach ($art in $item.expected_artifacts) {
            if (-not (Test-Path $art)) { $missing += $art }
        }

        if ($ec -eq 0 -and $missing.Count -eq 0) {
            Write-Host " [PASS] ${ts}s"
            [void]$itemResults.Add(@{
                id = $iid; status = 'passed'; verdict = 'PASS'
                reason = ''; duration = $ts
            })
        } elseif ($ec -eq 1) {
            Write-Host " [BLOCKED] ${ts}s"
            [void]$itemResults.Add(@{
                id = $iid; status = 'blocked'; verdict = 'BLOCKED'
                reason = "batch exit 1"; duration = $ts
            })
        } elseif ($missing.Count -gt 0) {
            Write-Host " [FAILED] missing: $($missing -join ', ')"
            [void]$itemResults.Add(@{
                id = $iid; status = 'failed'; verdict = 'FAILED'
                reason = "missing artifacts: $($missing -join ', ')"; duration = $ts
            })
        } else {
            Write-Host " [FAILED] exit=$ec ${ts}s"
            [void]$itemResults.Add(@{
                id = $iid; status = 'failed'; verdict = 'FAILED'
                reason = "exit code $ec"; duration = $ts
            })
        }
    } catch {
        $ts = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
        Write-Host " [FAILED] $($_.Exception.Message)"
        [void]$itemResults.Add(@{
            id = $iid; status = 'failed'; verdict = 'FAILED'
            reason = $_.Exception.Message; duration = $ts
        })
    }  # end try/catch for item execution
}

# ---- Queue report ----
$elapsed = [math]::Round(((Get-Date) - $script:qStart).TotalSeconds, 1)
$passed = 0; $blocked = 0; $failed = 0; $escalated = 0; $skipped = 0
foreach ($r in $itemResults) {
    if ($r.verdict -eq 'PASS') { $passed++ }
    elseif ($r.verdict -eq 'BLOCKED') { $blocked++ }
    elseif ($r.verdict -eq 'FAILED') { $failed++ }
    elseif ($r.verdict -eq 'ESCALATED') { $escalated++ }
    else { $skipped++ }
}
$total = $itemResults.Count

$lines = @()
$lines += "# Queue Report: $qid"; $lines += ""
$lines += "**Time**: $(Get-Date -Format 'o')"
$lines += "**Duration**: ${elapsed}s"
$lines += "**Mode**: $($queue.mode)"; $lines += ""
$lines += "## Executive Decision"; $lines += ""
if ($failed -gt 0) { $lines += 'FAILED — escalate to reviewer for diagnosis.' }
elseif ($blocked -gt 0 -or $escalated -gt 0) { $lines += 'BLOCKED/ESCALATED — reviewer should check escalated items.' }
else { $lines += 'PASS — all pending items passed. Queue complete.' }
$lines += ""
$lines += "## Summary"; $lines += "PASS=$passed BLOCKED=$blocked FAILED=$failed ESCALATED=$escalated SKIPPED=$skipped TOTAL=$total"
$lines += ""
$lines += "## Item Matrix"; $lines += ""
$lines += "| # | Item ID | Status | Verdict | Duration | Reason |"
$lines += "|---|---------|--------|---------|----------|--------|"
for ($i = 0; $i -lt $total; $i++) {
    $r = $itemResults[$i]
    $lines += "| $($i+1) | $($r.id) | $($r.status) | $($r.verdict) | $($r.duration)s | $($r.reason) |"
}
$lines += ""
$lines += "## Next Action"
if ($failed -gt 0) { $lines += 'Stop. Escalate failed items to reviewer.' }
elseif ($blocked -gt 0) { $lines += 'Review blocked items. May be expected pre-flight blocks.' }
elseif ($escalated -gt 0) { $lines += 'Tier 2 items escalated. Requires reviewer decision.' }
else { $lines += 'Queue complete. Ready for next batch or release gate.' }

$rptPath = Join-Path $qdir 'queue-report.md'
($lines -join "`n") | Out-File -FilePath $rptPath -Encoding utf8

$qResult = @{
    queue_id = $qid
    timestamp = (Get-Date -Format 'o')
    mode = $queue.mode
    passed = $passed; blocked = $blocked; failed = $failed
    escalated = $escalated; skipped = $skipped; total = $total
    duration = $elapsed
    items = @($itemResults)
    report_path = $rptPath
} | ConvertTo-Json -Depth 3
$qResult | Out-File (Join-Path $qdir 'queue-result.json') -Encoding utf8

Write-Host "`nQueue Report: $rptPath"

if ($failed -gt 0) { exit 2 }
if ($blocked -gt 0 -or $escalated -gt 0) { exit 1 }
exit 0
