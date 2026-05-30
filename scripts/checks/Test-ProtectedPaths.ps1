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
    return New-CheckResult -CheckName "ProtectedPaths" -Status "BLOCKED" `
        -Details $violations `
        -Suggestion "Governance files modified. Ensure TaskSpec + ExecutionReport exist per SADP."
} else {
    return New-CheckResult -CheckName "ProtectedPaths" -Status "PASS"
}
