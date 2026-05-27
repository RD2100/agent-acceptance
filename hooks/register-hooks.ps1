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

# Read raw JSON as text for safe manipulation
$rawJson = Get-Content $settingsPath -Raw

# Define the hook entry as raw JSON string
$hookEntryRaw = @'
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

# Check if already registered
if ($rawJson -match "pre-edit\.audit\.draft\.ps1") {
    Write-Output "[SKIP] Hook already registered for Write|Edit"
} else {
    # Merge: add hooks section into existing JSON
    $hookConfig = $hookEntryRaw | ConvertFrom-Json
    $settings = $rawJson | ConvertFrom-Json

    if (-not $settings.hooks) {
        $settings | Add-Member -MemberType NoteProperty -Name "hooks" -Value $hookConfig.hooks -Force
    }

    # Re-serialize with proper depth
    $settings | ConvertTo-Json -Depth 6 | Set-Content $settingsPath -Encoding UTF8
    Write-Output "[OK] Hook registered: PreToolUse(Write|Edit) -> pre-edit.audit.draft.ps1"
}

Write-Output ""
Write-Output "=== Registration Complete ==="
Write-Output "Restart Claude Code to activate hooks."
Write-Output "To rollback: copy $backupPath -> $settingsPath"
