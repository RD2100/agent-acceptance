# Register governance hooks for agent-acceptance
# Run once after human gate approval

$ErrorActionPreference = "Stop"

Write-Output "=== Registering RD2100 Agent Runtime Governance Hooks ==="
Write-Output ""

# Paths
$hookDir = "D:\agent-acceptance\hooks"
$settingsPath = "$env:USERPROFILE\.claude\settings.json"

# Verify prerequisites
if (-not (Test-Path $hookDir)) {
    Write-Error "hooks/ directory not found: $hookDir"
    exit 1
}

if (-not (Test-Path "$hookDir\pre-edit.audit.draft.ps1")) {
    Write-Error "pre-edit.audit.draft.ps1 not found"
    exit 1
}

if (-not (Test-Path $settingsPath)) {
    Write-Error "settings.json not found: $settingsPath"
    exit 1
}

# Backup existing settings
$backupPath = "$settingsPath.bak.$(Get-Date -Format 'yyyyMMddHHmmss')"
Copy-Item $settingsPath $backupPath
Write-Output "[OK] Backup saved: $backupPath"

# Read current settings
$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json

# Add hooks if not present
if (-not $settings.hooks) {
    $settings | Add-Member -MemberType NoteProperty -Name "hooks" -Value @{} -Force
}

if (-not $settings.hooks.PreToolUse) {
    $settings.hooks | Add-Member -MemberType NoteProperty -Name "PreToolUse" -Value @() -Force
}

# Define the hook entry
$hookEntry = @{
    matcher = "Write|Edit"
    command = "powershell -ExecutionPolicy Bypass -File `"D:\agent-acceptance\hooks\pre-edit.audit.draft.ps1`""
}

# Check if already registered
$alreadyRegistered = $false
foreach ($existing in $settings.hooks.PreToolUse) {
    if ($existing.matcher -eq $hookEntry.matcher -and $existing.command -eq $hookEntry.command) {
        $alreadyRegistered = $true
        break
    }
}

if ($alreadyRegistered) {
    Write-Output "[SKIP] Hook already registered for Write|Edit"
} else {
    $settings.hooks.PreToolUse += $hookEntry
    Write-Output "[OK] Hook registered: PreToolUse(Write|Edit) -> pre-edit.audit.draft.ps1"
}

# Write back
$settings | ConvertTo-Json -Depth 4 | Set-Content $settingsPath -Encoding UTF8

Write-Output ""
Write-Output "=== Registration Complete ==="
Write-Output "Restart Claude Code to activate hooks."
Write-Output "To rollback: copy $backupPath -> $settingsPath"
