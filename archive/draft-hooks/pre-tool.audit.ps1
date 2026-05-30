# PRODUCTION HOOK - Active blocking hook

$hadViolation = $false

#
# pre-tool.audit.draft.ps1
# Runs before a tool invocation (conceptual hook, not actually registered).
# Exits 0 on pass, exits 1 on violations.
#
# Usage (conceptual): Receive tool name and params on stdin, output audit to stdout.

param(
    [Parameter(ValueFromPipeline = $true)]
    [string]$ToolInfo = ""
)

$AUDIT_HEADER = @"

========================================
 PRE-TOOL AUDIT (Draft - Not Registered)
========================================
"@

Write-Output $AUDIT_HEADER

if (-not $ToolInfo) {
    Write-Output "[AUDIT] No tool info provided. Suggest: pass tool name and key params."
    Write-Output "[AUDIT] STATUS: INCOMPLETE_INPUT"
    exit 0
}

# Parse tool name
$toolName = ""
if ($ToolInfo -match '"tool"\s*:\s*"([^"]+)"')       { $toolName = $Matches[1] }
if (-not $toolName -and $ToolInfo -match '"name"\s*:\s*"([^"]+)"')  { $toolName = $Matches[1] }

Write-Output "[AUDIT] Tool name: $toolName"

# Phase 0-5 Forbidden Tools
$forbiddenTools = @{
    "Bash" = @{
        patterns = @("npm install", "npm ci", "pip install", "pip3 install", "yarn add",
                     "git commit", "git push", "git reset --hard", "git clean",
                     "git stash", "git checkout --", "git merge", "git rebase",
                     "curl", "wget", "Invoke-WebRequest", "Invoke-Expression",
                     "rm -rf", "rmdir /s", "del /f",
                     "ssh ", "scp ",
                     "chmod 777", "chmod -R",
                     "npx ", "npx ts", "python -m pytest", "npm test", "npm run",
                     "tsc --noEmit", "python -m compileall")
        message = "Bash command may be forbidden in Phase 0-5. Verify against tool-policy.md."
    }
    "Write" = @{
        patterns = @("\.env", "\.key", "\.pem", "CLAUDE\.md", "MEMORY\.md", "ACTIVE\.md",
                     "settings\.json", "\.claude\\", "\.codegraph\\")
        message = "Write target may be outside approved scope. Verify against batch plan."
    }
    "Edit" = @{
        patterns = @("README\.md", "AGENTS\.md", "scripts\\", "agent-workqueue\\",
                     "\.env", "MEMORY\.md")
        message = "Edit target may be a dirty baseline or forbidden file. Verify against batch plan."
    }
}

if ($forbiddenTools.ContainsKey($toolName)) {
    $check = $forbiddenTools[$toolName]
    foreach ($pattern in $check.patterns) {
        if ($ToolInfo -match $pattern) {
            Write-Output "[AUDIT] WARNING: $($check.message)"
            Write-Output "[AUDIT]   Matched pattern: '$pattern'"
        }
    }
}

# MCP tool audit
if ($toolName -match "^mcp__") {
    $restrictedMcp = @("computer-use", "pencil", "gsd-pi")
    foreach ($prefix in $restrictedMcp) {
        if ($toolName -match $prefix) {
            Write-Output "[AUDIT] WARNING: MCP tool category '$prefix' may be restricted in Phase 0-5."
            Write-Output "[AUDIT]   Recommend: verify this tool is permitted in tool-policy.md."
        }
    }
}

# Blackboard write audit
if ($toolName -match "^bb_") {
    $forbiddenBb = @("bb_solidify_knowledge", "bb_share_knowledge", "bb_claim_file",
                     "bb_release_file", "bb_acquire_build_lock", "bb_release_build_lock")
    if ($toolName -in $forbiddenBb) {
        Write-Output "[AUDIT] WARNING: Blackboard write tool '$toolName' is FORBIDDEN in Phase 0-5."
        Write-Output "[AUDIT]   Do NOT invoke this tool."
    }
}

# Skill tool audit
if ($toolName -eq "Skill") {
    $forbiddenSkills = @("skill-installer", "skill-creator", "skill-share",
                         "update-config", "file-organizer",
                         "connect-apps", "setup-pre-commit")
    foreach ($skill in $forbiddenSkills) {
        if ($ToolInfo -match $skill) {
            Write-Output "[AUDIT] WARNING: Skill '$skill' is FORBIDDEN in Phase 0-5."
            Write-Output "[AUDIT]   Do NOT invoke this skill."
        }
    }
}

Write-Output "[AUDIT] STATUS: COMPLETE"
if ($hadViolation) { Write-Output "[AUDIT] BLOCKED: violations detected"; exit 1 } else { Write-Output "[AUDIT] PASS: no violations"; exit 0 }