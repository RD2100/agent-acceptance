# Local Skill Intake Policy -- R5

> Batch Y (R5), 2026-05-27
> R5 = reference and classify only. No execution, no auto-load, no install.

## 1. R5 Boundary

R5 classifies local skills from the system prompt skill manifest and user-level skill directories. Skills are classified as reference_only, candidate, defer, or reject. No skill is executed, auto-loaded, or installed.

**R5 does NOT authorize**: execution, auto-trigger, install, MCP enable, hook registration, code modification outside approved scope.

## 2. Decision Enum

| Decision | Meaning | Action |
|----------|---------|--------|
| `reference_only` | Skill documented for awareness only | Record name and purpose |
| `candidate` | Skill is safe for deeper review in future phase | Full classification, defer evaluation |
| `defer` | Skill requires quarantine or human gate before evaluation | Queue for future phase |
| `reject` | Skill is unsafe, incompatible, or permanently out of scope | Record rejection reason |

**NOT allowed in R5**: `approved`, `installed`, `enabled`, `active`, `auto_trigger_enabled`.

## 3. Classification by Skill Type

### Coding Skills (decision: candidate)
- coding-discipline, devprocess -- reasoning workflows, no external execution
- claude-refactor, claude-lint-fix -- modify code; require approved scope check (defer if scope uncontrolled)

### Quality Skills (decision: candidate)
- ai-code-review, security-checklist, performance-lint -- analysis only, no mutation
- diagnose -- diagnosis loop; safe as reasoning pattern

### Process Skills (decision: defer)
- learn-plan-execute, create-plan -- planning workflows; safe but defer full evaluation
- recursive-improve -- may attempt to write rules/memory (**defer, high risk**)

### Git Skills (decision: defer)
- claude-git-helper, git-guardrails -- git operations; **defer** (Phase 0-5 forbids git mutations)
- setup-pre-commit -- installs packages; **reject**

### Memory Skills (decision: defer)
- memory-bridge -- may attempt memory/DB writes; **defer**
- dream-reflection -- cross-session pattern writes; **defer**

### Evolution Skills (decision: defer or reject)
- skill-auto-evolve -- GEPA self-evolution; **defer** (requires agent-state.db writes)
- skill-evolver -- mutation/evaluation lifecycle; **defer**
- skill-creator -- creates new skill definitions; **defer**
- skill-installer -- installs from external sources; **reject** (Phase 0-5 critical risk)
- skill-share -- shares on Slack (network); **reject**
- skill-usage-tracker -- writes to agent-state.db; **defer**

### External Integration (decision: reject)
- connect-apps -- Composio CLI; **reject** (external service, P0 risk)
- blackboard-knowledge-loop -- may trigger bb_solidify; **defer**
- update-config -- MCP config mutation; **reject**

### UI / Desktop (decision: reject)
- Any skill using computer-use, UI-TARS, desktop automation -- **reject** (critical)

### Design, Media, Document Processing (decision: reference_only)
- frontend-design, canvas-design, algorithmic-art, pdf, docx, pptx, xlsx, brand-guidelines, theme-factory, slack-gif-creator, paperjsx
- **reference_only** -- domain-specific, out of Runtime v2 bootstrap scope

### Utilities (decision: reference_only)
- caveman, domain-name-brainstormer, file-organizer, tailored-resume-generator, grill-me
- **reference_only** -- low risk but out of scope

## 4. Self-Evolution Quarantine

Skills in the "evolution" category (skill-auto-evolve, skill-evolver, recursive-improve, dream-reflection, memory-bridge) are **quarantined by default**. They must not be candidate unless:
1. Memory write is explicitly approved for the phase
2. Agent-state.db write is explicitly approved
3. Separate human gate authorizes each execution

See `self-evolution-quarantine-policy.md` for full quarantine rules.

## 5. Classification Summary

| Category | reference_only | candidate | defer | reject |
|----------|:---:|:---:|:---:|:---:|
| Coding | 0 | 2 | 2 | 0 |
| Quality | 0 | 4 | 0 | 0 |
| Process | 0 | 2 | 1 | 0 |
| Git | 0 | 0 | 2 | 1 |
| Memory | 0 | 0 | 2 | 0 |
| Evolution | 0 | 0 | 4 | 2 |
| External | 0 | 0 | 1 | 2 |
| UI/Desktop | 0 | 0 | 0 | 0 (all reject by default) |
| Design/Media/Doc | 12 | 0 | 0 | 0 |
| Utilities | 5 | 0 | 0 | 0 |
| **Total** | **17** | **8** | **12** | **5** |

## 6. Hard Constraints

- `auto_trigger_allowed` is always `false` in R5
- `execution_allowed` is always `false` in R5
- `install_allowed` is always `false` in R5
- No skill may be executed during R5 classification
- No skill files may be modified or created
