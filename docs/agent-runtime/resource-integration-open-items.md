# Resource Integration Open Items -- RD2100 Agent Runtime v2

> Batch Z, 2026-05-27
> 10 open items identified during the final audit.

---

## Open Item Index

| # | ID | Title | Phase | Severity | Status |
|---|----|-------|:-----:|:--------:|--------|
| 1 | OI-001 | Phase 6C Source URL + Clone Approval | 6C | BLOCKER | PENDING |
| 2 | OI-002 | R1 Blackboard SNAPSHOT-MCP Authorization | R1 | HIGH | PENDING |
| 3 | OI-003 | R5 Local Skill Evolution Quarantine Enforcement | R5 | MEDIUM | ACTIVE |
| 4 | OI-004 | R6 Memory Write Path Audit | R6 | MEDIUM | MONITOR |
| 5 | OI-005 | R7 Script Execution Gate Process Definition | R7 | HIGH | PENDING |
| 6 | OI-006 | WorkQueue Dry-Run Authorization Path | R7 | MEDIUM | PENDING |
| 7 | OI-007 | CodeGraph Reindex Decision for Empty Index | R4 | LOW | DEFERRED |
| 8 | OI-008 | Hooks Directory Governance | R0 | MEDIUM | MONITOR |
| 9 | OI-009 | Rules Conflict Resolution Process | R5 | LOW | OPEN |
| 10 | OI-010 | Phase 6A Deferred Skills Re-evaluation | 6A | MEDIUM | PENDING |

---

## OI-001: Phase 6C Source URL + Clone Approval

**Severity**: BLOCKER
**Phase**: 6C
**Description**: Phase 6C Source Lock & Quarantine is structurally designed (SourceLockRecord schema exists, static review checklist defined, gate decision workflow modeled) but no source URL has been approved and no clone into quarantine has been executed. This blocks all Phase 6+ capability installation.
**Dependencies**: Phase 6A approval matrix decisions (Taste-Skill approved, Understand Anything approved, others deferred). Human reviewer must authorize source URLs.
**Resolution**: Assign a Phase 6C-designated agent batch. Require explicit human approval of source URLs before any `git clone` into quarantine. Follow the Phase 6 Source Lock & Quarantine protocol.
**Impact if Unresolved**: No skill installation. No Phase 7 advancement.

---

## OI-002: R1 Blackboard SNAPSHOT-MCP Authorization

**Severity**: HIGH
**Phase**: R1
**Description**: The Blackboard MCP resource is pre-registered (outside the R0-R7 lifecycle) but the R1 snapshot must confirm mcp_status="disabled". The schema enforces this, but the runtime state of the MCP server must be independently verified by the R1 reviewer.
**Dependencies**: Blackboard MCP server pre-registration state. Reviewer must verify actual mcp_status matches the "disabled" requirement.
**Resolution**: R1 gate review must independently confirm mcp_status. If MCP is pre-registered and active, R1 cannot proceed until the environment is corrected.
**Impact if Unresolved**: R1 boundary violation. Cannot proceed to R2.

---

## OI-003: R5 Local Skill Evolution Quarantine Enforcement

**Severity**: MEDIUM
**Phase**: R5
**Description**: Self-evolution skills (skill-auto-evolve, skill-evolver, recursive-improve, dream-reflection) are classified as deferred/rejected in R5 schemas with next_phase_blocked=true. However, these skills exist as system-prompt skills and could theoretically be auto-triggered by context. The schema does not prevent them from being invoked at the Claude Code harness level -- it only documents that invocation is a violation.
**Dependencies**: Claude Code skill auto-trigger behavior. Reviewer monitoring of skill invocation logs.
**Resolution**: Monitor session logs for unapproved skill invocation. If detected, treat as hard stop per NEG-R5-003, NEG-R5-004, NEG-R5-016, NEG-R5-025.
**Impact if Unresolved**: Unauthorized self-evolution could mutate agent behavior without human review.

---

## OI-004: R6 Memory Write Path Audit

**Severity**: MEDIUM
**Phase**: R6
**Description**: MemoryContextRecord enforces write_allowed=false and access_mode=read_only via schema consts. However, the memory system spans multiple layers (files at C:\Users\RD\.claude\, agent-state.db, Blackboard knowledge) and a write to any of these layers would be a violation that must be detected post-hoc.
**Dependencies**: Actual filesystem state of C:\Users\RD memory paths. Session audit logs.
**Resolution**: Each batch's post-task `git status` (or equivalent filesystem check) should verify no unexpected files appeared in memory paths. Each reviewer checklist should include this check.
**Impact if Unresolved**: Undetected memory corruption could poison cross-session context.

---

## OI-005: R7 Script Execution Gate Process Definition

**Severity**: HIGH
**Phase**: R7
**Description**: Scripts (Run-WorkQueue.ps1, Run-Smoke.ps1, etc.) have ScriptSafetyRecord schemas with allowed_to_run=false and execution_status=not_run. The process for graduating a script to human_required (and eventually to a permitted run) needs clear gate definitions: what evidence is required, who must approve, and what monitoring is needed during execution.
**Dependencies**: ScriptSafetyRecord approval process definition. Human gate workflow.
**Resolution**: Define the script execution gate process as a Phase 7 deliverable. Minimum: ScriptSafetyRecord with all risks assessed, -DryRun flag enforced, human gate per-run, evidence collected (pre/post git status, exit code, output log).
**Impact if Unresolved**: Script execution without defined gate process creates undefined risk.

---

## OI-006: WorkQueue Dry-Run Authorization Path

**Severity**: MEDIUM
**Phase**: R7
**Description**: 5 workqueue JSON files exist (local-quality, release-readiness, recovery-regression, cleanup-dryrun, docs-quality) but are registered-only and not consumed. The path to authorized dry-run WorkQueue consumption needs definition: which queue first, what preconditions, what success criteria, and what escalation tiers.
**Dependencies**: ScriptSafetyRecord for Run-WorkQueue.ps1. Human gate approval per batch.
**Resolution**: Define WorkQueue dry-run process as part of Phase 7 exit criteria. Start with lowest-risk queue (cleanup-dryrun.queue.json) with -DryRun. Require per-queue human gate.
**Impact if Unresolved**: WorkQueue remains registered but unused, providing no value.

---

## OI-007: CodeGraph Reindex Decision for Empty Index

**Severity**: LOW
**Phase**: R4
**Description**: The agent-acceptance CodeGraph index has 0 files indexed (empty). The schema enforces trusted_for_current_run=false. codegraph-stale-policy.md says "do NOT trigger reindex" for empty indexes. The empty index means CodeGraph cannot serve as an intelligence layer for agent-acceptance until reindexed -- but reindex requires 5 preconditions including human approval.
**Dependencies**: Human approval for reindex. sqlite3 availability (or equivalent tool) for verifying db state.
**Resolution**: Defer to Phase 7+. When reindex is approved, verify target_root is unchanged, create EvidenceIndex record, run reindex under human supervision, verify index status post-reindex, and update trusted_for_current_run accordingly.
**Impact if Unresolved**: CodeGraph cannot be used for agent-acceptance code search (Grep/Read remain functional fallbacks).

---

## OI-008: Hooks Directory Governance

**Severity**: MEDIUM
**Phase**: R0
**Description**: The `hooks/` directory exists as an untracked directory in the dirty baseline. While no hooks are currently registered (no .git/hooks/ modified), the directory's content and purpose need documentation. The resource-risk-matrix.md Risk Category 3 covers hook registration but not the existence of hook templates/specs.
**Dependencies**: Content audit of hooks/ directory.
**Resolution**: When hooks are eventually reviewed (Phase 7+), classify each hook script, create ToolRiskRecords, and require ScriptSafetyRecords before any hook activation.
**Impact if Unresolved**: Unknown hooks directory content could contain dangerous configurations.

---

## OI-009: Rules Conflict Resolution Process

**Severity**: LOW
**Phase**: R5
**Description**: NEG-R5-024 identifies the risk of rule conflicts between global rules (C:\Users\RD\.claude\rules\) and native rules (rules/). The negative test expects conflicts to be documented with resolution, but the process for resolution is not yet defined.
**Dependencies**: Full audit of all rule files. Conflict detection mechanism.
**Resolution**: When rules are activated (Phase 7+), run a rule dedup check: for each native rule, check if a conflicting global rule exists. Document conflicts with explicit precedence (native over global for agent-acceptance scope; global over native for cross-project behavior). Produce a rule-dedup-map artifact.
**Impact if Unresolved**: Ambiguous rule precedence could cause inconsistent agent behavior.

---

## OI-010: Phase 6A Deferred Skills Re-evaluation

**Severity**: MEDIUM
**Phase**: 6A
**Description**: Phase 6A approval matrix deferred 3 skills (ECC, AnySearch Skill, addyosmani-agent-skills-zh). These need re-evaluation against updated criteria when the project reaches Phase 6F (approval for install). The basis for deferral was "insufficient evaluation data" -- these skills may need additional static review.
**Dependencies**: Phase 6C static review results. Updated risk criteria.
**Resolution**: Schedule re-evaluation as part of Phase 6F gate. If additional data is available (community feedback, security audits), incorporate. Apply the same approval matrix criteria.
**Impact if Unresolved**: Deferred skills remain unavailable, which may be acceptable if they were not critical path.

---

## Auditor Notes

- OI-001 is the only true blocker. All other items can be resolved in later phases without blocking R0-R7 gate advancement.
- OI-003 and OI-004 require monitoring (not active remediation) in current phase.
- OI-005, OI-006, OI-007, OI-009 are process-definition items suitable for Phase 7 planning.
- No open item requires immediate action to pass R0-R7 gates.
