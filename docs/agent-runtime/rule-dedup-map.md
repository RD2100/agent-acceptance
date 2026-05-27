# Rule Dedup Map -- R5

> Batch Y (R5), 2026-05-27
> Maps Claude rules to agent-acceptance native rules. Records overlaps. Does NOT copy rules into AGENTS.md.

## 1. Purpose

This document records the relationship between global Claude rules (`C:\Users\RD\.claude\rules\`) and agent-acceptance native rules (`D:\agent-acceptance\rules\`). It identifies overlaps, conflicts, and gaps. It does NOT recommend copying rule text into AGENTS.md — AGENTS.md must remain navigation-only.

## 2. Rule Source Inventory

### Global Claude Rules (C:\Users\RD\.claude\rules\)

| File | Domain | R5 Access | Status |
|------|--------|:---:|--------|
| `blackboard-protocol.md` | Blackboard pointer | reference_only | Pointer to project-rules |
| `executor-agent-pattern.md` | Agent role | reference_only | Defines executor workflow |
| `gsd-tdd.md` | TDD enforcement | reference_only | GSD milestone TDD |
| `self-evolution.md` | Self-evolution | reference_only | Hermes Agent memory model |

### Agent-acceptance Native Rules (D:\agent-acceptance\rules\)

| File | Domain | Rules |
|------|--------|:---:|
| `core.md` | Runtime core | 6 |
| `coding.md` | Code generation | 7 |
| `security.md` | Security hard stops | 8 |
| `review.md` | Review & evidence | 6 |
| `git.md` | Git safety | 6 |
| `research.md` | Read-only exploration | 5 |
| `frontend.md` | Frontend reference | 6 |

## 3. Overlap Map

| Global Rule | Native Rule Overlap | Resolution |
|-------------|---------------------|------------|
| executor-agent-pattern (3-step flow) | core-003 (Phase boundary), review-001 (No fake green) | Native rules are more specific. Global provides role context. No conflict. |
| gsd-tdd (red-green-refactor) | coding-001 (No empty error handling) | Complementary. GSD TDD applies to GSD milestones. Native coding rules apply to all code. |
| self-evolution (3-layer memory) | memory-architecture.md (same model) | Duplicate concept. Native doc is canonical for this runtime. |
| blackboard-protocol (pointer) | memory-architecture.md (Layer 3) | Consistent. Both point to project-rules/blackboard-protocol.md. |

## 4. Conflict Map

| Conflict | Description | Resolution |
|----------|-------------|------------|
| None identified | No direct rule contradictions found between global and native rules | N/A |

## 5. Gap Map

| Gap | Description | Severity |
|-----|-------------|:---:|
| TDD enforcement | gsd-tdd is global-only; no native TDD rule in rules/ | P3 |
| Self-evolution audit rows | self-evolution.md requires audit rows in memory files; not enforced by native rules | P3 |

## 6. AGENTS.md Protection

- AGENTS.md is navigation-only per reviewer decision (Batch C2A)
- Rules MUST NOT be copied into AGENTS.md
- Rule overlap/conflict/gap information stays in this document
- AGENTS.md links to rules/README.md and this document

## 7. Cross-Reference Integrity

All native rule files exist and are consistent with their README.md index. Global Claude rules are referenced but not verified at file level (C:\Users\RD access policy applies).
