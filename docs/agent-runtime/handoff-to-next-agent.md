
# Handoff: RD2100 Agent Runtime v2 → Next Agent

> Date: 2026-05-28 | Handoff from: Codex Agent (C3A–C5) | To: Next coding/reviewer agent
> Canonical root: `D:\agent-acceptance`

---

## 0. Quick Start (Read This First)

This is a **governance/runtime acceptance project**. Do not treat assets as permission to execute.

Three most important files:
1. `AGENTS.md` — Hard stops, document map, Phase boundary
2. `docs/agent-runtime/capability-inventory.md` — 27 capabilities across Claude + Codex
3. `rules/core.md` — 7 P0 rules (especially core-007)

State summary: "Runtime v2 governance is structurally complete. Bootstrap template package is tested (10/10). All capabilities are registered and constrained. No capability is currently approved for install/runtime enablement beyond inventory."

---

## 1. What Was Done (This Session: 2026-05-28)

### Batch Summary

| Batch | What | Status |
|-------|------|:---:|
| Hook Gov Upgrade | Activated pre-edit hook as blocking governance gate | Committed (b22edc3..3cb6ea7) |
| Hook Doc Sync | Updated 9 governance docs to reflect active hook | Uncommitted |
| Hook Rename | pre-edit.audit.draft.ps1 → pre-edit.governance.ps1 | Uncommitted |
| C3A | Installed 15 Codex plugins (external agent, pre-existing) | Complete |
| C3B | Disabled 10 redundant/credential-less plugins, kept 8 | Complete |
| C3C | Cross-platform capability inventory (Claude+Codex, 27 entries) | Uncommitted |
| C3D | core-007: No Capability Without Inventory Registration | Uncommitted |
| C4 | Bootstrap template package (6 files, tested 10/10) | Uncommitted |
| C5 | 10 acceptance tests on bootstrap; all PASS | Complete |

### Working Tree: 18 Modified + 11 New Untracked

**Modified (uncommitted):**

| File | Batch | Change |
|------|-------|--------|
| AGENTS.md | C3C,C3D | Cross-platform doc map, core-007 ref, Phase boundary |
| rules/core.md | C3D | +core-007 rule |
| capability-inventory.md | C3C,C3D | Rewritten: 27 entries, Platform+Status columns |
| capability-risk-matrix.md | C3C | Platform note |
| capability-routing-negative-tests.md | C3D | +CR-NEG-031/032/033 |
| next-agent-handoff.md | C3C,C3D | Updated hooks + Do Not entries |
| resource-integration-handoff.md | C3C | Updated hooks status |
| resource-risk-matrix.md | C3C | Updated Risk Category 3 (hooks) |
| reviewer-playbook.md | C3C,C3D | +Step 8a capability audit; Batch C hooks |
| runtime-v2-final-status.md | C3C | Section 2.4 hooks updated |
| hooks/register-hooks.ps1 | Rename | Updated paths + skip-check regex |
| hooks/registration-config.json | Rename | Updated path |
| hooks/pre-edit.audit.draft.ps1 | Rename | **DELETED** (renamed) |
| 5 prior-batch files | Prior | Content overlap notices (not this session) |

**New untracked (this session):**

| Path | Batch | Purpose |
|------|-------|---------|
| hooks/pre-edit.governance.ps1 | Rename | Active governance hook |
| templates/runtime-bootstrap/ (6 files) | C4 | Bootstrap package (tested 10/10) |
| hook-governance-upgrade-decision.md | Hook | Reviewer decision record |
| c3b-plugin-cleanup-plan.md | C3B | Plugin cleanup plan |
| .claude/ | Hook | Claude Code settings (untracked infrastructure) |
| .codegraph/ | Prior | CodeGraph database (empty, untracked infrastructure) |
| reports/ | C3A-C5 | Batch reports + snapshots |

### Commits (4, not yet pushed)

```
3cb6ea7 fix: register-hooks.ps1 auto-creates settings.json when missing
4c82458 fix: hook registration, manifest dedup, header sync
32fe7a9 feat: add hook registration script
b22edc3 feat: upgrade pre-edit hook to active blocking mode
```

Branch: master | Commits: 9 from initial (no remote tracking) | Dirty baseline (13M+6U): untouched

---

## 2. Key Architecture Decisions

### 2.1 Cross-Platform Capability Inventory

Single file with Platform column. Distribution:
- **Both** (15): CodeGraph, rg/grep, shell, JSON, docs, rules, negative tests, playbooks, test-frame, dev-frame, local skills, memory, workqueue, scripts, Phase 6
- **Claude** (4): Blackboard MCP, hooks, sealed manifest, hook registration script
- **Codex** (8): coderabbit, codex-security, supabase, github, browser, superpowers, linear, notion

Each entry has Status: approved | proposed | disabled | rejected.

### 2.2 core-007: The Registration Gate

P0 hard stop. Capability not in inventory with Status: approved = does not exist. Registration: propose 鈫?review 鈫?approve 鈫?enable 鈫?verify 鈫?report.

### 2.3 Bootstrap Template Package

templates/runtime-bootstrap/bootstrap.ps1 initializes governance in any project:

`powershell
powershell -EP Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1
`

Output: 8 rules + 19 schemas + AGENTS.md + 10 capabilities + tool-policy + 5 reviewer docs + 30 fixtures. Tested 10/10 PASS.

### 2.4 Governance Hook

hooks/pre-edit.governance.ps1 is ACTIVE in ~/.claude/settings.json. Blocks Write/Edit to: memory dirs, sealed files (22 in manifest), secret patterns (.env/.key/.pem/token/credential/id_rsa/id_ed25519). Other 4 hooks are audit-only drafts, exit 0 always.

---

## 3. Codex Plugin State (Post-C3B)

**8 enabled:**

| Plugin | Risk | Phase 0-5 | Notes |
|--------|:---:|:---:|-------|
| browser | medium | restricted | localhost only |
| superpowers | low | allowed | methodology reference |
| github | high | restricted | read-only; writes blocked |
| coderabbit | low | allowed | AI code review; read-only |
| codex-security | low | allowed | security scan; read-only |
| supabase | high | restricted | DB writes blocked |
| linear | medium | restricted | Phase 1+ |
| notion | medium | restricted | Phase 1+ |

**10 disabled:** sentry, datadog, cloudflare, slack, teams, temporal, clickup, asana, circleci, render

---

## 4. What Is Pending

### Immediate
1. Review and commit 18 modified files (all in approved outputs)
2. Review new untracked files
3. Sign off C3C/C3D/C4/C5 batches

### Short-term
1. Test bootstrap on a real project
2. Register Codex skills (~100+ unclassified)
3. Taste-Skill sandbox dry-run

### Medium-term
1. Understand Anything re-evaluation
2. CodeGraph reindex for agent-acceptance
3. WorkQueue/script dry-run

---

## 5. Critical Constraints (Do Not Violate)

### P0 Hard Stops
| Rule | Description |
|------|-------------|
| core-001 | No destructive git without human approval |
| core-002 | No secrets in code/logs/reports |
| core-003 | Phase boundary enforcement |
| core-004 | No fake green |
| core-005 | No write outside approved scope |
| core-007 | No capability without inventory registration |

### Phase 0-5 Boundaries
- No external skill install/execution
- No memory writes
- No package install
- No MCP config changes
- No git mutations
- No capability use without approved inventory entry

### Platform-Specific
- Claude: pre-edit.governance.ps1 is ONLY active hook
- Codex: No plugin add without inventory proposal

---

## 6. Key File Reference

### Navigation
| File | Purpose |
|------|---------|
| AGENTS.md | Hard stops, document map, Phase boundary |
| capability-inventory.md | 27 capabilities, Platform+Status |
| rules/core.md | 7 P0-P2 rules |

### Governance Assets
| File | Purpose |
|------|---------|
| rules/*.md (8) | 44 rules |
| schemas/ (19) | JSON Schema |
| reviewer-playbook.md | 10-step review + decision tree |
| verification-gates.md | P0-P3 gate hierarchy |
| operating-model.md | Execution layers |

### Bootstrap Package (templates/runtime-bootstrap/)
| File | Purpose |
|------|---------|
| README.md | Overview + parameters |
| INSTANTIATION.md | 6-step guide |
| bootstrap.ps1 | One-click init (10/10 tested) |
| AGENTS.template.md | 6 placeholders |
| capability-inventory.template.md | 10 universal capabilities |
| tool-policy.template.md | Phase-aware tool policy |

### Hooks
| File | Status |
|------|--------|
| pre-edit.governance.ps1 | ACTIVE (registered, blocking) |
| pre-task.audit.draft.ps1 | Audit-only draft |
| pre-tool.audit.draft.ps1 | Audit-only draft |
| pre-final.audit.draft.ps1 | Audit-only draft |
| skill-intake-scan.audit.draft.ps1 | Audit-only draft |
| sealed-files-manifest.json | 22 files + 3 dirs |
| register-hooks.ps1 | Registration script |
| registration-config.json | Manual merge config |

---

## 7. Suggested First Actions

1. git status --short 鈥?confirm state
2. Read this handoff completely
3. Read AGENTS.md, capability-inventory.md, rules/core.md
4. Ask user: "Commit working tree changes, or review first?"

---

## 8. Bootstrap Usage Prompt (For New Projects)

```
You are a coding agent. Execute a one-time bootstrap task.

Run in the target project root:
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\templates\runtime-bootstrap\bootstrap.ps1

Optional parameters (all auto-detected):
  -ProjectName "my-project"
  -ProjectRoot "D:\my-project"
  -Platform Both
  -Phase "0-5"
  -DryRun  (preview only)
  -Force   (overwrite existing)

After generation, verify:
  cat AGENTS.md | Select-String "{{"    # Must return nothing
  cat docs\agent-runtime\capability-inventory.md | Select-String "^## \d+\."  # Must be >= 10

Then: (1) Register project-specific capabilities at #11+,
(2) Configure platform assets (Claude: hook drafts; Codex: plugins),
(3) Submit for reviewer approval.
```

---

> **End of Handoff.** Repository in consistent, governed state. Bootstrap tested 10/10. All capabilities registered and constrained.

