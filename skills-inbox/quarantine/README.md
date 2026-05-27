# Quarantine Directory

> Part of RD2100 Agent Runtime v2 Phase 6: Source Lock & Quarantine.
> This directory is a DESIGN artifact. No skills have been quarantined yet.

## Purpose

This directory holds cloned external skill repositories under review. It is the isolation zone where Phase 6 static analysis happens before any skill is ever allowed to execute.

## CRITICAL: No Code Execution

**NO files in this directory are ever executed.** The quarantine zone is strictly read-only with the exception of review artifacts written to each skill's `review/` subdirectory. Source code in `repo/` is only ever read via static analysis tools (Read, Grep, Glob).

Violation of this rule is a P0 security incident.

## Directory Structure

```
skills-inbox/quarantine/
  README.md              <- This file
  <skill-name>/           <- One directory per quarantined skill
    .source-lock.json     <- Copy of the SourceLockRecord
    repo/                 <- Read-only git clone at pinned commit
    review/               <- Static review output artifacts
    metadata/             <- Intake metadata copies
```

## Lifecycle

```
 [Clone] --> [Static Review] --> [Decision] --> [Archive | Promote | Delete]
```

### 1. Clone (Phase 6B)

A skill repo is cloned into `repo/` at a specific locked commit SHA. The clone is immediately made read-only. No git operations are performed on the clone after checkout verification.

**Pre-requisite**: Source URL must pass the allowlist check (Phase 6A).

### 2. Static Review (Phase 6C)

Read-only analysis is performed on the `repo/` contents:
- Structural review (file count, binary scan, obfuscation check)
- Tool declaration review (MCP, hooks, UI automation, shell execution)
- Network & external access review (HTTP, API keys, package install)
- Skill manifest integrity review
- Security hotspot scan (injection, path traversal, eval, credentials)

Review artifacts are written to `review/`:
- `static-review.md` -- filled-out checklist
- `tool-manifest.json` -- extracted tool declarations
- `risk-report.md` -- overall risk assessment

### 3. Decision (Phase 6F)

Based on static review results:

- **Archive**: Skill is safe but not needed now. `repo/` stays read-only. Metadata preserved.
- **Promote**: Skill passes all Phase 7 gates. Ready for the Phase 7 installation pipeline. The `repo/` remains in quarantine as an audit record.
- **Delete**: Skill fails critical gates or is malicious. Quarantine directory is removed. Rejection reason is recorded permanently in the SourceLockRecord.

## Permissions

| Path | Permission | Notes |
|------|------------|-------|
| `quarantine/` root | Read | Agent can list contents |
| `<skill>/repo/` | Read-only | No writes, no execution, no git operations |
| `<skill>/review/` | Write | Agent writes review artifacts here |
| `<skill>/metadata/` | Write | Agent writes metadata copies here |
| `<skill>/.source-lock.json` | Write (once) | Written at clone time, never modified |

## Current Status

- **Quarantined skills**: 0
- **Pending reviews**: 0
- **Approved for install**: 0
- **Rejected**: 0

## Related Documents

- `docs/agent-runtime/phase-6-source-lock-quarantine.md` -- Full Phase 6 design
- `schemas/agent-runtime/source-lock-record.schema.json` -- SourceLockRecord contract
- `docs/agent-runtime/external-skill-intake.md` -- Phase 0-5 intake pipeline
- `docs/agent-runtime/integration-contracts.md` -- Contract 6 (SkillIntakeRecord)
- `skills-inbox/allowlist.json` -- Clone allowlist
