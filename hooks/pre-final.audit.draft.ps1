# AUDIT-ONLY DRAFT
# Not registered - Not blocking - No mutation - No secret access
#
# pre-final.audit.draft.ps1
# Runs before task finalization (conceptual hook, not actually registered).
# Checks verification gates are satisfied before reporting completion.
# Outputs audit recommendations to stdout. Always exits 0.
#
# Usage (conceptual): Receive task result JSON on stdin, output audit to stdout.

param(
    [Parameter(ValueFromPipeline = $true)]
    [string]$TaskResult = ""
)

$AUDIT_HEADER = @"

========================================
 PRE-FINAL AUDIT (Draft - Not Registered)
========================================
"@

Write-Output $AUDIT_HEADER

if (-not $TaskResult) {
    Write-Output "[AUDIT] No task result provided. Suggest: pass ExecutionReport JSON."
    Write-Output "[AUDIT] STATUS: INCOMPLETE_INPUT"
    exit 0
}

# Check for required report sections
$requiredSections = @(
    "Executive Assessment",
    "Batch",
    "Pre/Post Git Status",
    "Files Created",
    "Constraint Compliance",
    "Forbidden Action Check"
)

$missingSections = @()
foreach ($section in $requiredSections) {
    if ($TaskResult -notmatch [regex]::Escape($section)) {
        $missingSections += $section
    }
}

if ($missingSections.Count -gt 0) {
    Write-Output "[AUDIT] WARNING: ExecutionReport may be missing sections:"
    foreach ($s in $missingSections) {
        Write-Output "[AUDIT]   - $s"
    }
    Write-Output "[AUDIT] Recommend: verify report completeness before submitting."
}

# P1: Check for fake green - FAILED/BLOCKED should not be reported as PASS
if ($TaskResult -match "FAILED" -and $TaskResult -match '"status"\s*:\s*"PASS"') {
    Write-Output "[AUDIT] HARD STOP: FAILED detected but status is PASS. This is fake green."
    Write-Output "[AUDIT]   Rule review-001: Never report FAILED/BLOCKED as PASS."
}

if ($TaskResult -match "BLOCKED" -and $TaskResult -match '"status"\s*:\s*"PASS"') {
    Write-Output "[AUDIT] HARD STOP: BLOCKED detected but status is PASS. This is fake green."
    Write-Output "[AUDIT]   Rule review-001: Never report FAILED/BLOCKED as PASS."
}

# P1: Check for forbidden action violations in report
$forbiddenReportPatterns = @(
    "npm install(ed)?",
    "pip install(ed)?",
    "skill-installer",
    "bb_solidify_knowledge",
    "MCP config.*modif",
    "hook.*register",
    "git commit",
    "git push",
    "memory.*writ",
    "secret.*read"
)

$foundForbidden = @()
foreach ($pattern in $forbiddenReportPatterns) {
    if ($TaskResult -match $pattern) {
        $foundForbidden += $pattern
    }
}

if ($foundForbidden.Count -gt 0) {
    Write-Output "[AUDIT] WARNING: ExecutionReport may contain references to Phase 0-5 forbidden actions:"
    foreach ($f in $foundForbidden) {
        Write-Output "[AUDIT]   - Pattern: '$f'"
    }
    Write-Output "[AUDIT] Recommend: verify these are only in 'forbidden action check: no' context."
}

# P2: Check for evidence references
$evidenceCount = 0
if ($TaskResult -match "evidence" -or $TaskResult -match "Evidence" -or $TaskResult -match "test -f") {
    $evidenceCount = 1
}

if ($evidenceCount -eq 0) {
    Write-Output "[AUDIT] INFO: ExecutionReport should include evidence for claims."
    Write-Output "[AUDIT]   Rule review-004: Claims must be traceable to observable evidence."
}

# P2: Check for pre/post git status
if ($TaskResult -notmatch "git status --short" -and $TaskResult -notmatch "Pre.*Post.*Git") {
    Write-Output "[AUDIT] INFO: ExecutionReport should include pre/post git status diff."
    Write-Output "[AUDIT]   Rule review-006: Pre/Post status required for file-modifying tasks."
}

# P3: Check for blocking issues
if ($TaskResult -notmatch "Blocking Issue" -and $TaskResult -notmatch "blocking") {
    Write-Output "[AUDIT] INFO: Consider adding Blocking Issues section (or explicitly state None)."
}

Write-Output "[AUDIT] STATUS: COMPLETE"
exit 0
