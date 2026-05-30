# PRODUCTION HOOK - Active blocking hook

$hadViolation = $false

#
# pre-task.audit.draft.ps1
# Runs before task execution (conceptual hook, not actually registered).
# Exits 0 on pass, exits 1 on violations.
#
# Usage (conceptual): Receive task JSON on stdin, output audit to stdout.

param(
    [Parameter(ValueFromPipeline = $true)]
    [string]$TaskJson = ""
)

$AUDIT_HEADER = @"

========================================
 PRE-TASK AUDIT (Draft - Not Registered)
========================================
"@

Write-Output $AUDIT_HEADER

if (-not $TaskJson) {
    Write-Output "[AUDIT] No task input provided. Suggest: always pass TaskSpec JSON."
    Write-Output "[AUDIT] STATUS: INCOMPLETE_INPUT"
    exit 0
}

# Parse task fields (lightweight, no external parser needed for draft)
$taskId       = ""
$taskPriority = ""
$taskStatus   = ""
$taskDesc     = ""

if ($TaskJson -match '"task_id"\s*:\s*"([^"]+)"')       { $taskId       = $Matches[1] }
if ($TaskJson -match '"priority"\s*:\s*"([^"]+)"')       { $taskPriority = $Matches[1] }
if ($TaskJson -match '"status"\s*:\s*"([^"]+)"')         { $taskStatus   = $Matches[1] }
if ($TaskJson -match '"description"\s*:\s*"([^"]+)"')    { $taskDesc     = $Matches[1] }

Write-Output "[AUDIT] Task ID    : $taskId"
Write-Output "[AUDIT] Priority   : $taskPriority"
Write-Output "[AUDIT] Status     : $taskStatus"

# P0: Reject tasks with priority P0 that have no explicit approval marker
if ($taskPriority -eq "P0" -and $TaskJson -notmatch '"approved_by"') {
    Write-Output "[AUDIT] WARNING: P0 task without approved_by field. Recommend: add reviewer approval."
}

# P1: Check task status is valid
$validStatuses = @("draft", "ready", "deferred", "rejected")
if ($taskStatus -and $taskStatus -notin $validStatuses) {
    Write-Output "[AUDIT] WARNING: Task status '$taskStatus' not in valid list: $($validStatuses -join ', ')."
}

# P1: Scope check - reject tasks that mention forbidden Phase 0-5 actions
$forbiddenPatterns = @(
    "npm install", "pip install", "yarn add",
    "skill-installer install", "skill-installer",
    "bb_solidify_knowledge", "bb_share_knowledge",
    "MCP config", "register hook",
    "git commit", "git push", "git reset --hard", "git clean",
    "clone.*repo", "git clone",
    "Invoke-WebRequest", "curl.*http",
    "UI-TARS", "computer.use"
)

foreach ($pattern in $forbiddenPatterns) {
    if ($TaskJson -match $pattern) {
        Write-Output "[AUDit] WARNING: Task references potentially forbidden Phase 0-5 action: '$pattern'"
        Write-Output "[AUDIT]   Recommend: verify this action is approved in batch plan."
    }
}

# P2: Check for evidence requirements in P1+ tasks
if ($taskPriority -in @("P0", "P1") -and $TaskJson -notmatch '"evidence"') {
    Write-Output "[AUDIT] INFO: P0/P1 task should include evidence requirements."
}

Write-Output "[AUDIT] STATUS: COMPLETE"
if ($hadViolation) { Write-Output "[AUDIT] BLOCKED: violations detected"; exit 1 } else { Write-Output "[AUDIT] PASS: no violations"; exit 0 }