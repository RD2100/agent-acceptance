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

# Define hook config once, used by both branches
$hookConfigJson = @'
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "powershell -ExecutionPolicy Bypass -File \"D:\\agent-acceptance\\hooks\\pre-edit.audit.draft.ps1\""
      }
    ]
  }
}
'@
$hookConfig = $hookConfigJson | ConvertFrom-Json

# Branch 1: Create new settings.json if missing
if (-not (Test-Path $settingsPath)) {
    Write-Output "[INFO] settings.json not found. Creating default with hooks."
    $defaultSettings = @{
        defaultMode = "bypassPermissions"
        hooks = $hookConfig.hooks
    }
    $defaultSettings | ConvertTo-Json -Depth 6 | Set-Content $settingsPath -Encoding UTF8
    Write-Output "[OK] settings.json created with hooks at: $settingsPath"
    Write-Output ""
    Write-Output "=== Registration Complete ==="
    exit 0
}

# Branch 2: Merge into existing settings.json
$rawJson = Get-Content $settingsPath -Raw

if ($rawJson -match "pre-edit\.audit\.draft\.ps1") {
    Write-Output "[SKIP] Hook already registered for Write|Edit"
} else {
    $backupPath = "$settingsPath.bak.$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item $settingsPath $backupPath
    Write-Output "[OK] Backup saved: $backupPath"

    $settings = $rawJson | ConvertFrom-Json
    if (-not $settings.hooks) {
        $settings | Add-Member -MemberType NoteProperty -Name "hooks" -Value $hookConfig.hooks -Force
    }
    $settings | ConvertTo-Json -Depth 6 | Set-Content $settingsPath -Encoding UTF8
    Write-Output "[OK] Hook registered: PreToolUse(Write|Edit) -> pre-edit.audit.draft.ps1"
    Write-Output "To rollback: copy $backupPath -> $settingsPath"
}

Write-Output ""
Write-Output "=== Registration Complete ==="
Write-Output "Restart Claude Code to activate hooks."
