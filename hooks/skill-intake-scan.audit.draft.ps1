# AUDIT-ONLY DRAFT
# Not registered - Not blocking - No mutation - No secret access
#
# skill-intake-scan.audit.draft.ps1
# Periodically scans skills-inbox/external/ for new entries.
# Produces SkillIntakeRecord proposals for any new skills found.
# Outputs audit recommendations to stdout. Always exits 0.
#
# Usage (conceptual): Run on session start or periodically.
# No parameters needed; scans the well-known path.

$AUDIT_HEADER = @"

========================================
 SKILL INTAKE SCAN (Draft - Not Registered)
========================================
"@

Write-Output $AUDIT_HEADER

$inboxPath = "D:\agent-acceptance\skills-inbox\external"

if (-not (Test-Path $inboxPath)) {
    Write-Output "[AUDIT] Inbox path does not exist: $inboxPath"
    Write-Output "[AUDIT] No skills-inbox/external directory found. Nothing to scan."
    Write-Output "[AUDIT] STATUS: NO_INBOX"
    exit 0
}

$entries = Get-ChildItem -Path $inboxPath -Directory -ErrorAction SilentlyContinue

if (-not $entries -or $entries.Count -eq 0) {
    Write-Output "[AUDIT] Inbox is empty. No new skills to classify."
    Write-Output "[AUDIT] STATUS: EMPTY_INBOX"
    exit 0
}

Write-Output "[AUDIT] Found $($entries.Count) skill(s) in inbox:"
Write-Output ""

# Phase 0-5 high-risk skill name patterns
$highRiskPatterns = @(
    "install", "setup", "init", "deploy", "publish",
    "migrate", "delete", "clean", "purge", "reset",
    "admin", "root", "sudo", "system",
    "hook", "config", "setting", "registry",
    "network", "remote", "cloud", "api-gateway"
)

$criticalRiskPatterns = @(
    "credential", "secret", "token", "auth", "password",
    "mcp-config", "claude-config", "settings-writer",
    "computer-use", "ui-tars", "screen-control"
)

foreach ($entry in $entries) {
    $skillName = $entry.Name
    $skillPath = $entry.FullName

    Write-Output "--- Skill: $skillName ---"
    Write-Output "  Path: $skillPath"

    # Classify risk level based on name patterns
    $riskLevel = "low"
    $disposition = "candidate"

    foreach ($pattern in $criticalRiskPatterns) {
        if ($skillName -match $pattern) {
            $riskLevel = "critical"
            $disposition = "reject"
            break
        }
    }

    if ($riskLevel -ne "critical") {
        foreach ($pattern in $highRiskPatterns) {
            if ($skillName -match $pattern) {
                $riskLevel = "high"
                $disposition = "defer"
                break
            }
        }
    }

    # Check if directory has evaluation subdirectory (previously processed)
    $evalPath = Join-Path $skillPath "evaluation"
    if (Test-Path $evalPath) {
        Write-Output "  [AUDIT] Previously evaluated. Skipping classification."
        Write-Output "  [AUDIT] Evaluation exists at: $evalPath"
        continue
    }

    # Check for README or description
    $readmePath = Join-Path $skillPath "README.md"
    $hasReadme = Test-Path $readmePath

    Write-Output "  Risk Level    : $riskLevel"
    Write-Output "  Disposition   : $disposition"
    Write-Output "  Has README    : $hasReadme"

    # Proposed SkillIntakeRecord
    $record = @"
  Proposed SkillIntakeRecord:
  {
    "record_id": "sr-$(Get-Date -Format 'yyyyMMddHHmmss')-$skillName",
    "skill_name": "$skillName",
    "source": "skills-inbox/external/$skillName",
    "evaluated_at": "$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssK')",
    "disposition": "$disposition",
    "risk_level": "$riskLevel",
    "rationale": "Auto-classified by skill-intake-scan draft hook. Risk based on name patterns."
  }
"@
    Write-Output $record

    # P0: Critical risk skills - reject immediately
    if ($riskLevel -eq "critical") {
        Write-Output "  [AUDIT] HARD STOP RECOMMENDATION: Reject '$skillName'."
        Write-Output "  [AUDIT]   Name matches critical risk pattern."
        Write-Output "  [AUDIT]   Do NOT clone, install, or execute this skill."
    }

    # P1: High risk skills - defer to Phase 6
    if ($riskLevel -eq "high") {
        Write-Output "  [AUDIT] RECOMMENDATION: Defer '$skillName' to Phase 6."
        Write-Output "  [AUDIT]   Name matches high risk pattern."
        Write-Output "  [AUDIT]   Create SkillIntakeRecord but do NOT install."
    }

    Write-Output ""
}

Write-Output "[AUDIT] Scan complete."
Write-Output "[AUDIT] Next step: create SkillIntakeRecord for each new entry."
Write-Output "[AUDIT]   DO NOT clone, install, or execute any skill."
Write-Output "[AUDIT] STATUS: COMPLETE"
exit 0
