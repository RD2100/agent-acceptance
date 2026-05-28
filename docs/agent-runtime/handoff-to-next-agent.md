# Handoff: RD2100 Agent Runtime v2 ¡ú Next Agent

> **Date**: 2026-05-28 | **Session**: P0 Sync + Plan Auditor + Automation
> **Canonical root**: `D:\agent-acceptance` | **Phase**: 0-5 (bootstrap)

---

## 0. Quick Start (Read This First)

Three most important files (plus one external enforcement):

1. **`AGENTS.md`** ¡ª Hard stops, doc map, Phase boundary, SADP auto-trigger rules
2. **`docs/agent-runtime/sub-agent-dispatch-protocol.md`** ¡ª SADP v1.0: Gate 0, Plan Auditor, dispatch, review, regression
3. **`rules/core.md`** ¡ª 8 P0 rules (core-001 ~ core-008), Veto Contract, Knowledge Metabolism

**State**: "Governance upgraded from declarative to evidence-driven. Plan Auditor added as independent compliance check. Pre-write hook extended to governance files. Session ledger auto-generation in place. Phase-6 historical reports archived."

---

## 1. Current State

| Asset | Count | Notes |
|-------|:----:|-------|
| Core rules | 8 | core-001 ~ core-008 (P0 cap: 7) |
| Lessons learned | 10 | LL-001 ~ LL-010 |
| Capability inventory | 28 | + expiration policy, + Capability Passport |
| JSON schemas | 4 | TaskSpec, ExecutionReport, SessionLedger, AuditRecord |
| Dependency canaries | 4 | CANARY-001 tested, rest defined |
| Bootstrap templates | 7 | + governance-manifest.template.md |
| Git status | 24M + 30U | Working tree dirty, all approved changes |

---

## 2. What Was Done This Session

### P0: Structural Sync (task-p0-sync-001)

After SADP/capability-inventory upgrades, 8 downstream files were out of sync:
- Updated `task-spec.schema.json` (+gate_0.inventory_evidence +conflict_registry)
- Updated `execution-report.schema.json` (+trust_record +fallback_record)
- Rewrote `AGENTS.md` doc map (added SADP, lessons, canaries, manifest, bootstrap, schemas)
- Fixed header counts: 27¡ú28 capabilities, 6¡ú8 rules
- Updated `INSTANTIATION.md` (+governance manifest verification step)
- Created `governance-manifest.md` for this project
- Recorded LL-008 (Structural Inconsistency Cascade)
- **?? LL-009: Plan Agent initially skipped SADP for this task, then retroactively corrected**

### P0: Plan Auditor (task-plan-auditor-001)

LL-009 revealed Plan Agent can self-bypass SADP. Solution: independent Plan Auditor.
- Created `session-ledger.schema.md` ¡ª per-session compliance evidence
- Created `audit-record.schema.md` ¡ª structured audit output (pass/block/escalate)
- Amended SADP ¡ì3.3a: Plan Auditor with decision matrix, anti-bypass, anti-recursion
- Hard rule: "Plan Agent cannot audit its own compliance"
- Recorded LL-010 (Post-Hoc Audit Gap ¡ª can detect, cannot prevent initial write)

### P1: Automation (task-p1-auto-audit-001)

- Created `scripts/New-SessionLedger.ps1` ¡ª auto-generates session_ledger.yaml from git diff
- Extended `hooks/pre-edit.governance.ps1` ¡ª now blocks governance file writes without TaskSpec
- CodeGraph MCP activation deferred (Phase 0-5 constraint)

### P1: Phase-6 Archive

- Moved 15 historical phase-6 reports to `docs/archive/phase-6/`
- Fixed stale reference in handoff-to-next-agent.md

---

## 3. Architecture Decisions

### Governance: Declarative ¡ú Evidence-Driven

| Before | After |
|--------|-------|
| `inventory_checked: true` (boolean) | `inventory_evidence: { queried_sources, matched_capabilities }` |
| Plan Agent self-reviews (SADP ¡ì3.3a) | Plan Auditor independent review (¡ì3.3a), Plan Agent review now ¡ì3.3b |
| Session ledger: manual fill | Auto-generated from git diff |
| Hook: blocks memory/sealed/secrets | Also blocks governance files without TaskSpec |
| Auto-trigger: per-TaskSpec | Cumulative trigger window (anti task-splitting) |

### SADP Dispatch Architecture

```
Plan Agent ¡ú Gate 0 (evidence) ¡ú TaskSpec ¡ú Execute Agent ¡ú ExecutionReport
                  ¡ý                                              ¡ý
            Session Ledger (auto) ¡û©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤©¤ git diff
                  ¡ý
            Plan Auditor (independent)
                  ¡ý
            Pass / Block / Escalate Human
```

### Key Principles

1. **Evidence Over Assertion** ¡ª no boolean self-attestation
2. **Cumulative Impact Over Local Compliance** ¡ª task splitting = same governance
3. **Imported Governance Is Locked** ¡ª Bootstrap manifest hash-locks P0 rules
4. **Independent Evidence Before Acceptance** ¡ª Plan Agent cannot self-audit

---

## 4. What Remains

### P1 (functional gaps)
| # | Item | Status | Blocker |
|---|------|--------|---------|
| 1 | CodeGraph MCP activation | DB 14.8MB exists | Phase 0-5 MCP constraint |
| 2 | Bootstrap real-project test | Template tested 10/10 | Needs external project |
| 3 | ~100+ skills ¡ú capability inventory | Codex plugins installed | Manual classification effort |
| 4 | WorkQueue SADP integration | 5 queues + 7 scripts | Script execution restricted |

### P2 (nice to have)
| # | Item | Status |
|---|------|--------|
| 5 | Capability Passport: 21 entries still unknown | Summary table created, individual verification pending |
| 6 | Draft hooks registration (4 audit hooks) | Human gate required |
| 7 | opencode dedicated agent | Hung per LL-005 |
## 5. Critical Constraints

### P0 Hard Stops
- core-001: No destructive git without human approval
- core-002: No secrets in code/logs/reports
- core-003: Phase boundary enforcement
- core-007: No capability without inventory registration
- core-008: Resource Sufficiency ¡ª Prove Gap Before Any Action

### Phase 0-5 Boundary (Still Active)
- No external skill install/execution
- No memory writes (read-only)
- No package install (npm, pip, yarn)
- No MCP config changes
- No git commit/push without human gate
- Dirty baseline (24M + 30U): do not touch
- Capability registration requires inventory entry + reviewer approval

### SADP Auto-Triggers
- 3+ files modified ¡ú SADP required
- Governance file touched ¡ú SADP + full regression
- Protected file touched ¡ú exclusive lock + audit
- Cumulative write_set ¡Ý 3 across tasks ¡ú SADP triggered
- Plan Agent cannot self-audit (¡ì3.3a hard rule)

### Model Dispatch Limits
- DeepSeek v4-pro: ¡Ü2 files, ¡Ü30s, no .ps1 (LL-002, LL-003)
- DeepSeek chat: 3-5 files, slower
- Codex direct: 6+ files, .ps1 files, governance modifications

---

## 6. Key File Reference

### Navigation
| File | Purpose |
|------|---------|
| `AGENTS.md` | Hard stops, doc map, Phase boundary |
| `rules/core.md` | 8 P0 rules + Veto Contract |
| `docs/agent-runtime/sub-agent-dispatch-protocol.md` | SADP v1.0 (Gate 0 ¡ú Plan Auditor ¡ú regression) |
| `docs/agent-runtime/capability-inventory.md` | 28 capabilities + expiration policy |
| `docs/agent-runtime/lessons-learned.md` | LL-001 ~ LL-010 |
| `docs/agent-runtime/session-ledger.schema.md` | Auto-generated compliance evidence |
| `docs/agent-runtime/audit-record.schema.md` | Plan Auditor output schema |
| `docs/agent-runtime/dispatch-model-profiles.md` | Model limits + failure patterns |
| `docs/agent-runtime/dependency-canaries.md` | 4 canaries for external dependency health |
| `docs/agent-runtime/governance-manifest.md` | Protected section hashes + drift detection |

### External Enforcement (Non-Agent-Triggered)
| File | Purpose |
|------|---------|
| scripts/sadp-audit.ps1 | External SADP compliance check (v2: write_set cross-reference) |
| .git/hooks/pre-commit | Git hook ¡ú sadp-audit.ps1 (blocks commit on SADP violation) |

### Automation
| File | Purpose |
|------|---------|
| `scripts/New-SessionLedger.ps1` | Auto-generate session ledger from git diff |
| `hooks/pre-edit.governance.ps1` | Pre-write gate (memory/sealed/secrets/governance) |
| `templates/runtime-bootstrap/bootstrap.ps1` | One-click governance deployment |

### Schemas
| File | Key Fields |
|------|-----------|
| `schemas/agent-runtime/task-spec.schema.json` | gate_0.inventory_evidence, conflict_registry |
| `schemas/agent-runtime/execution-report.schema.json` | trust_record, fallback_record |

---

## 7. Suggested First Action

`@go` ¡ª triggers SADP dispatch for the next P1 task. Or target:
- **Highest impact**: CodeGraph MCP activation (needs Phase exit or human gate waiver)
- **Quickest win**: Bootstrap real-project test
- **Most pending**: ~100+ skills classification

