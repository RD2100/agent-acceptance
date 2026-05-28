# ACTIVE HOOK â€?Governance Gate
# Registered - Blocking on hard violations - No mutation - No secret access
#
# pre-edit.audit.draft.ps1
# Runs before Write/Edit tool calls. Blocks edits to memory, sealed files, and secrets.
# Exit 0: allowed. Exit 1: BLOCKED (hard violation).
#
# Usage: Hook runs with file_path from tool call context.

param(
    [Parameter(ValueFromPipeline = $true)]
    [string]$EditInfo = ""
)

$AUDIT_HEADER = @"

========================================
 PRE-EDIT AUDIT (Active - Registered)
========================================
"@

Write-Output $AUDIT_HEADER

# DIAGNOSTIC: log raw input to temp file
$diagPath = Join-Path $env:TEMP "hook-diag-$(Get-Date -Format 'yyyyMMddHHmmss').txt"
"=== HOOK FIRED ===" | Out-File $diagPath
"EditInfo length: $($EditInfo.Length)" | Out-File $diagPath -Append
"EditInfo: [$EditInfo]" | Out-File $diagPath -Append
"All args: [$args]" | Out-File $diagPath -Append
"Input: [$input]" | Out-File $diagPath -Append

if (-not $EditInfo) {
    Write-Output "[AUDIT] No edit info provided. Suggest: pass file path and edit type."
    Write-Output "[AUDIT] STATUS: INCOMPLETE_INPUT"
    exit 0
}

# Parse file path
$filePath = ""
if ($EditInfo -match '"file_path"\s*:\s*"([^"]+)"') { $filePath = $Matches[1] }
if (-not $filePath -and $EditInfo -match '"path"\s*:\s*"([^"]+)"')  { $filePath = $Matches[1] }

Write-Output "[AUDIT] Target file: $filePath"

# P0: Block edits to memory directories â€?HARD STOP
$memoryPaths = @(
    "C:\Users\RD\.claude\projects\D--agent-acceptance\memory\",
    "C:\Users\RD\.claude\memory\"
)
foreach ($memPath in $memoryPaths) {
    $memPattern = [regex]::Escape($memPath)
    if ($filePath -match $memPattern) {
        Write-Output "[AUDIT] HARD STOP: Target is in RD2100 memory directory."
        Write-Output "[AUDIT]   Handoff 'Do Not write RD2100 memory' â€?BLOCKED."
        Write-Output "[AUDIT] STATUS: BLOCKED_MEMORY_WRITE"
        exit 1
    }
}


# ================================================================
# P0: Block edits to governance files without valid TaskSpec
# LL-009/LL-010: Plan Agent must not self-bypass SADP.
# Governance file modifications require a TaskSpec that lists
# this file in its write_set.
# ================================================================
$governanceFilePatterns = @(
    "AGENTS\.md$",
    "CLAUDE\.md$",
    "\\rules\\",
    "\\docs\\agent-runtime\\sub-agent-dispatch-protocol",
    "\\docs\\agent-runtime\\capability-inventory",
    "\\docs\\agent-runtime\\lessons-learned",
    "\\docs\\agent-runtime\\session-ledger",
    "\\docs\\agent-runtime\\audit-record",
    "\\docs\\agent-runtime\\governance-manifest",
    "\\docs\\agent-runtime\\dependency-canaries",
    "\\schemas\\agent-runtime\\",
    "\\templates\\runtime-bootstrap\\",
    "\\hooks\\"
)

$isGovernanceFile = $false
foreach ($pattern in $governanceFilePatterns) {
    if ($filePath -match $pattern) {
        $isGovernanceFile = $true
        break
    }
}

if ($isGovernanceFile) {
    Write-Output "[AUDIT] GOVERNANCE FILE DETECTED"
    
    # Check for valid TaskSpec that lists this file
    $taskSpecFound = $false
    $taskDir = Join-Path (Split-Path $PSScriptRoot -Parent) "tasks"
    
    if (Test-Path $taskDir) {
        $taskFiles = Get-ChildItem $taskDir -Filter "task-*.md" -ErrorAction SilentlyContinue
        $fileName = Split-Path $filePath -Leaf
        foreach ($tf in $taskFiles) {
            $taskContent = Get-Content $tf.FullName -Raw -ErrorAction SilentlyContinue
            if ($taskContent -and ($taskContent -match [regex]::Escape($fileName))) {
                $taskSpecFound = $true
                Write-Output "[AUDIT]   TaskSpec found: $($tf.Name) references this file."
                break
            }
        }
    }
    
    if (-not $taskSpecFound) {
        Write-Output "[AUDIT] HARD STOP: No TaskSpec authorizes modification of this governance file."
        Write-Output "[AUDIT]   Per SADP section 3.3a: Plan Agent must create a TaskSpec with"
        Write-Output "[AUDIT]   gate_0 evidence before modifying governance files."
        Write-Output "[AUDIT]   Remediation: Create a TaskSpec listing this file in write_set."
        Write-Output "[AUDIT] STATUS: BLOCKED_NO_TASKSPEC"
        exit 1
    }
    
    Write-Output "[AUDIT]   Governance file edit authorized by existing TaskSpec."
}
# P0: Block edits to sealed files â€?HARD STOP
# Load sealed files from manifest (single source of truth)
$manifestPath = Join-Path $PSScriptRoot "sealed-files-manifest.json"
$sealedFiles = @()
if (Test-Path $manifestPath) {
    try {
        $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
        $sealedFiles = $manifest.sealed_files
    } catch {
        Write-Output "[AUDIT] WARNING: Could not read sealed-files-manifest.json. Using hardcoded fallback."
        $sealedFiles = @(
            "operating-model.md",
            "tool-policy.md",
            "memory-architecture.md",
            "verification-gates.md",
            "integration-contracts.md",
            "runtime-invariants.md",
            "skill-trigger-matrix.md"
        )
    }
}
foreach ($sealed in $sealedFiles) {
    $pattern = [regex]::Escape($sealed)
    if ($filePath -match $pattern) {
        Write-Output "[AUDIT] HARD STOP: Target file is SEALED."
        Write-Output "[AUDIT]   '$sealed' is in sealed-files-manifest.json."
        Write-Output "[AUDIT]   To unseal: remove from manifest with human approval."
        Write-Output "[AUDIT] STATUS: BLOCKED_SEALED_FILE"
        exit 1
    }
}

# P0: Reject edits to secret files
$secretPatterns = @("\.env$", "\.key$", "\.pem$", "token", "credential", "id_rsa", "id_ed25519")
foreach ($pattern in $secretPatterns) {
    if ($filePath -match $pattern) {
        Write-Output "[AUDIT] HARD STOP: File matches secret pattern: '$pattern'"
        Write-Output "[AUDIT]   Do NOT edit this file. Report to reviewer."
        Write-Output "[AUDIT] STATUS: BLOCKED_SECRET_PATTERN"
        exit 1
    }
}

# P1: Check write scope - Phase 0-5 approved directories
$approvedScopes = @(
    [regex]::Escape("D:\agent-acceptance\docs\agent-runtime\"),
    [regex]::Escape("D:\agent-acceptance\rules\"),
    [regex]::Escape("D:\agent-acceptance\hooks\"),
    [regex]::Escape("D:\agent-acceptance\skills-inbox\")
)

$inApprovedScope = $false
foreach ($scope in $approvedScopes) {
    if ($filePath -match "^$scope") {
        $inApprovedScope = $true
        break
    }
}

# P1: Check against dirty baseline files
$dirtyBaseline = @(
    "README.md",
    "agent-workqueue\QUEUE_INDEX.md",
    "agent-workqueue\cleanup-dryrun.queue.json",
    "agent-workqueue\docs-quality.queue.json",
    "agent-workqueue\local-quality.queue.json",
    "agent-workqueue\recovery-regression.queue.json",
    "agent-workqueue\release-readiness.queue.json",
    "docs\FLOW_CATALOG.md",
    "docs\NEXT_STAGE_BACKLOG.md",
    "docs\RUNBOOK.md",
    "scripts\Run-WorkQueue.ps1",
    "scripts\Test-WorkQueue.ps1",
    "scripts\examples\batch-docs-quality.json"
)

$isDirtyBaseline = $false
foreach ($dirty in $dirtyBaseline) {
    if ($filePath -match [regex]::Escape($dirty)) {
        $isDirtyBaseline = $true
        break
    }
}

if ($isDirtyBaseline) {
    Write-Output "[AUDIT] WARNING: Target file is in dirty baseline (13 modified files)."
    Write-Output "[AUDIT]   Phase 0-5 rule: do NOT modify dirty baseline files."
    Write-Output "[AUDIT]   Recommend: skip this edit unless explicitly approved in batch plan."
    Write-Output "[AUDIT] STATUS: WARNING_DIRTY_BASELINE"
    exit 0
}

if (-not $inApprovedScope) {
    Write-Output "[AUDIT] WARNING: Target file is outside Phase 0-5 approved write scope."
    Write-Output "[AUDIT]   Approved scopes: docs/agent-runtime/, rules/, hooks/, skills-inbox/"
    Write-Output "[AUDIT]   Recommend: verify this edit is in the current batch plan."
    Write-Output "[AUDIT] STATUS: WARNING_OUTSIDE_SCOPE"
    exit 0
}

# P2: Check for forbidden directories
$forbiddenDirs = @("\.claude", "\.codegraph", "\.git", "node_modules", "__pycache__")
foreach ($dir in $forbiddenDirs) {
    if ($filePath -match $dir) {
        Write-Output "[AUDIT] WARNING: Target file is in forbidden directory: '$dir'"
        Write-Output "[AUDIT] STATUS: WARNING_FORBIDDEN_DIR"
        exit 0
    }
}

Write-Output "[AUDIT] File is in approved scope. Proceed with edit."
Write-Output "[AUDIT] STATUS: PASS"
exit 0
