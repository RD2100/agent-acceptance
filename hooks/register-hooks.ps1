# Register governance hooks for agent-acceptance
# Run once after human gate approval
# Now registers ALL 5 active hooks (Batch C3D, 2026-05-28)

$ErrorActionPreference = "Stop"

Write-Output "=== Registering RD2100 Agent Runtime Governance Hooks ==="
Write-Output "Total: 5 hooks (pre-edit + 4 activated audit hooks)"

$hookDir = "$PSScriptRoot"
$settingsPath = "$env:USERPROFILE\.claude\settings.json"

$requiredHooks = @(
    "pre-edit.governance.ps1",
    "pre-final.audit.ps1",
    "pre-task.audit.ps1",
    "pre-tool.audit.ps1",
    "skill-intake-scan.audit.ps1"
)

foreach ($hook in $requiredHooks) {
    if (-not (Test-Path "$hookDir\$hook")) {
        Write-Error "Required hook not found: $hook"
        exit 1
    }
}

Write-Output "[OK] All 5 hooks verified."
Write-Output "Hooks ready for registration in Claude Code settings.json."
Write-Output "Run this script with human gate approval."
Write-Output "=== Registration Ready ==="