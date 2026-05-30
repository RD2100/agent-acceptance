# Register governance hooks for agent-acceptance
# Run once per clone to activate hooks and Claude Code settings.
# Updated: 2026-05-30 — governance de-hallucination reform.

$ErrorActionPreference = "Stop"

Write-Output "=== Registering RD2100 Agent Runtime Governance Hooks ==="

$hookDir = "$PSScriptRoot"
$repoRoot = (Resolve-Path (Join-Path $hookDir "..")).Path

# ---- 1. Git hooks via core.hooksPath (Git 2.9+) ----
Write-Output ""
Write-Output "[1/2] Configuring git hooks path..."

Push-Location $repoRoot
try {
    git config core.hooksPath hooks
    Write-Output "  core.hooksPath = hooks"
    Write-Output "  Active git hooks:"
    Get-ChildItem $hookDir -Filter "*.ps1" | ForEach-Object {
        $hookName = $_.BaseName -replace '\.governance$',''
        Write-Output "    - $($_.Name)"
    }
} finally {
    Pop-Location
}

# ---- 2. Claude Code settings ----
Write-Output ""
Write-Output "[2/2] Claude Code settings..."
$settingsPath = "$env:USERPROFILE\.claude\settings.json"
Write-Output "  Settings: $settingsPath"
Write-Output "  (Manual merge required — see hooks/registration-config.json)"
Write-Output ""

Write-Output "=== Registration Complete ==="
Write-Output "Git hooks active via core.hooksPath = hooks"
Write-Output "Pre-push gate: ai_guard + drift check + governance gate"
Write-Output "Pre-commit gate: sadp-audit (SADP compliance + secret scan)"
exit 0
