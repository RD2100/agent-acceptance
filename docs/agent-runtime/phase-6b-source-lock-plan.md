## 注意：本文与 phase-6b-handoff.md 存在内容重叠
## 两者同属 Phase 6B，描述同一批项目（Taste-Skill + Understand Anything）的 source lock 规划；plan 包含详细计划 JSON 结构和 gate 条件，handoff 包含交接上下文
# Phase 6B Source Lock Plan -- RD2100 Agent Runtime v2

> Date: 2026-05-27
> Agent: 6B-Plan Agent
> Purpose: Phase 6B source lock planning for 2 medium-risk projects approved by reviewer (2026-05-27). NO clone is performed in this phase.

## Overview

Phase 6B produces source lock plans only. This phase receives projects approved for `source_lock_planning` from Phase 6A, generates a detailed plan JSON for each project, and establishes the gate criteria that must be satisfied before any clone operation can proceed in Phase 6C.

## Approval Trace

Both projects were approved for `source_lock_planning` in Phase 6A:

| Project | Risk | Phase 6A Decision | Date |
|---------|------|-------------------|------|
| Taste-Skill | medium | `approve_for_source_lock_planning` | 2026-05-27 |
| Understand Anything | medium | `approve_for_source_lock_planning` | 2026-05-27 |

Source documents:
- `docs/agent-runtime/phase-6a-approval-matrix.md` -- Reviewer decisions with signatures
- `skills-inbox/allowlist.draft.json` -- `planning_approved` status for both entries

## Projects Deferred (Not in Scope)

The following 3 projects were deferred by the reviewer and are excluded from Phase 6B:

| # | Project | Risk | Reason |
|---|---------|------|--------|
| 1 | ECC | high | External code execution capability. Re-evaluate after medium-risk cycle completes. |
| 3 | AnySearch Skill | high | Web search integration requiring network isolation patterns. Re-evaluate after medium-risk cycle completes. |
| 9 | addyosmani-agent-skills-zh | high | Broad scope with unknown tool surface. Re-evaluate after sub-skill categorization methodology is defined. |

## Planning Template Description

Each plan JSON follows the format defined in `schemas/agent-runtime/source-lock-record.schema.json` with Phase 6B-specific extensions:

### Core Fields
- `plan_id`: Unique plan identifier (format: `SLP-<source_name>-<date>`)
- `source_name`: Project name matching candidate-index and allowlist entries
- `source_url_from_user_input`: Placeholder -- URL not provided in candidate index; must be supplied by human before Phase 6C
- `approval_source`: Traceability back to Phase 6A reviewer decisions
- `planned_quarantine_path`: Target path inside `skills-inbox/quarantine/<project>/repo/`

### Safety Fields (ALL enforced as `false`)
- `clone_allowed`: false
- `install_allowed`: false
- `execute_allowed`: false
- `mcp_enable_allowed`: false

### Template Fields (NOT for execution)
- `clone_command_template`: Contains `DO NOT RUN - TEMPLATE ONLY` marker
- `commit_sha_status`: `unknown_until_clone` -- will be resolved in Phase 6C

### Review Framework
- `static_review_checklist`: 8 standard checks for Phase 6C static analysis
- `forbidden_actions`: 5 actions prohibited at all Phase 6 stages
- `required_human_gate_before_clone`: 4 gates requiring explicit human approval before Phase 6C

## Phase 6C Gate

Before any clone operation in Phase 6C, the following must ALL be true:

1. **Source URL supplied**: Human reviewer provides the canonical source URL for each project
2. **allowlist.draft.json verified**: Entry verified against the provided URL
3. **Phase 6C explicit approval**: Separate human approval received for each clone operation
4. **Quarantine directory prepared**: Target path created with read-only permissions for agent
5. **Plan file reviewed**: Phase 6B plan JSON reviewed and accepted by human reviewer
6. **NO clone has occurred**: Verify no clone has been executed in Phase 6B

## Status

| Plan ID | Source Name | Plan File | Status |
|---------|-------------|-----------|--------|
| SLP-Taste-Skill-20260527 | Taste-Skill | `skills-inbox/source-lock-plans/Taste-Skill.plan.json` | plan_created_pending_human_review |
| SLP-Understand-Anything-20260527 | Understand Anything | `skills-inbox/source-lock-plans/Understand-Anything.plan.json` | plan_created_pending_human_review |

## References

- `docs/agent-runtime/phase-6a-approval-matrix.md` -- Phase 6A reviewer decisions
- `docs/agent-runtime/phase-6-source-lock-quarantine.md` -- Full Phase 6 quarantine design
- `skills-inbox/allowlist.draft.json` -- Allowlist with reviewer decisions applied
- `skills-inbox/external/candidate-index.md` -- Candidate registry with dispositions
- `skills-inbox/source-lock-requests/Taste-Skill.request.json` -- Original intake request
- `skills-inbox/source-lock-requests/Understand-Anything.request.json` -- Original intake request

---

> **IMPORTANT: Phase 6B produces plans only. All clone commands in plan files are TEMPLATES marked DO NOT RUN. No clone, install, or execution has been performed. Phase 6C requires separate human approval before any clone operation.**
