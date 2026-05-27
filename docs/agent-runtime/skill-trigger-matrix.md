# Skill Trigger Matrix -- RD2100 Agent Runtime v2

> Batch B1R, 2026-05-27
> Phase 0-5: This document provides trigger RECOMMENDATIONS only.
> No skill is auto-triggered. All triggers require human or workflow decision.

## Classification System

| Classification | Meaning | Phase 0-5 Behavior |
|----------------|---------|-------------------|
| **Recommended** | Reviewer recommends using this skill for its purpose | Agent may invoke when task matches trigger |
| **Reference Only** | Skill is documented for awareness | Do NOT invoke. Record only. |
| **Deferred** | May be useful in later phases | Do NOT invoke. Queue for Phase 6+ review. |
| **Forbidden** | Must NOT be used in current phase | Do NOT invoke under any circumstances. |

## Recommended Skills (Phase 0-5)

These are reasoning/workflow skills that do not install tools, modify configs, or execute external code.

### Code Discipline

| Skill | Classification | Trigger Recommendation | Notes |
|-------|:---:|-----------------------|-------|
| `coding-discipline` | Recommended | Non-trivial code generation/modification | Think first, keep simple, precise edits, goal-driven |
| `devprocess` | Recommended | Non-trivial programming tasks | Clarify -> Inspect -> Plan -> Implement -> Verify -> Review |

### Quality

| Skill | Classification | Trigger Recommendation | Notes |
|-------|:---:|-----------------------|-------|
| `ai-code-review` | Recommended | After code generation | 4-level review (P0-P3). Does NOT install anything. |
| `security-checklist` | Recommended | After code generation | 5 security patterns. Does NOT install anything. |
| `performance-lint` | Recommended | After code generation | 5 anti-patterns. Does NOT install anything. |
| `debug-logging` | Recommended | Writing new functions or modifying logic | Key-node debug log insertion. |

### Process

| Skill | Classification | Trigger Recommendation | Notes |
|-------|:---:|-----------------------|-------|
| `diagnose` | Recommended | Bug reported, "diagnose this" | Diagnosis loop: reproduce -> minimize -> hypothesize -> instrument -> fix -> regression-test |
| `learn-plan-execute` | Recommended | Non-trivial tasks: deploy, new feature, architecture change | Learn -> Plan -> Execute. Does NOT install. |
| `create-plan` | Recommended | User asks for a coding task plan | Concise plan for simple tasks |
| `context-snapshot` | Recommended | Approaching context limit | Persist key info. Does NOT write memory. |

### Documentation

| Skill | Classification | Trigger Recommendation | Notes |
|-------|:---:|-----------------------|-------|
| `claude-md-docs` | Recommended | Generate/maintain Markdown docs | Within approved write scope only |
| `changelog-generator` | Recommended | After significant changes | Read-only git analysis, writes changelog |

## Reference Only Skills (Phase 0-5)

Documented for awareness. Do NOT invoke in Phase 0-5.

| Skill | Reason |
|-------|--------|
| `caveman` | Communication style, safe but not needed in bootstrap |
| `codebase-search` | CodeGraph MCP preferred for exploration |
| `doc-coauthoring` | Structured doc workflow, not needed for bootstrap docs |
| `internal-comms` | Internal communication writing, out of scope |
| `domain-name-brainstormer` | Out of scope |
| `web-artifacts-builder` | Out of scope |
| `frontend-design` | Out of scope |
| `canvas-design` | Out of scope |
| `algorithmic-art` | Out of scope |
| `brand-guidelines` | Out of scope |
| `theme-factory` | Out of scope |
| `slack-gif-creator` | Out of scope |

## Deferred Skills (Phase 6+ Review Required)

### Git Operations

| Skill | Reason for Deferral |
|-------|---------------------|
| `claude-git-helper` | Automates git operations including commit. Phase 0-5 forbids commits. |
| `git-guardrails` | Registers hooks. Phase 0-5 forbids hook registration. |
| `gh-address-comments` | Requires gh CLI + PR interaction. Out of bootstrap scope. |
| `gh-fix-ci` | Requires GitHub Actions log access. Out of bootstrap scope. |
| `setup-pre-commit` | Installs husky + lint-staged packages. FORBIDDEN in Phase 0-5. |

### Memory & Evolution

| Skill | Reason for Deferral |
|-------|---------------------|
| `memory-bridge` | May attempt to write memory or agent-state.db. |
| `recursive-improve` | May attempt to write rules or memory files. |
| `dream-reflection` | May attempt cross-session pattern writes. |
| `skill-auto-evolve` | Requires skill execution tracking in agent-state.db (forbidden). |
| `skill-evolver` | Manages skill mutation lifecycle. Out of bootstrap scope. |
| `skill-usage-tracker` | Writes to agent-state.db (forbidden). |

### External Integration

| Skill | Reason for Deferral |
|-------|---------------------|
| `connect-apps` | Connects to external services via Composio. P0 risk. |
| `sentry-triage` | Requires Composio CLI + Sentry access. Out of scope. |
| `pr-review-ci-fix` | Requires Composio CLI + PR/CI access. Out of scope. |
| `web-learn-debug` | May trigger external web searches. |
| `webapp-testing` | Requires Playwright browser automation. Out of scope. |

### Platform-Specific

| Skill | Reason for Deferral |
|-------|---------------------|
| `claude-api-builder` | API interface design. Out of bootstrap scope. |
| `claude-asset-manager` | Game asset management. Out of scope. |
| `claude-comfy-workflow` | ComfyUI workflow. Out of scope. |
| `claude-file-templates` | Template generation. May write outside approved scope. |
| `claude-project-rules` | May modify CLAUDE.md or .claude/rules/. |
| `claude-lint-fix` | May auto-fix code outside approved scope. |
| `claude-refactor` | May refactor code outside approved scope. |
| `claude-notes` | May write to .claude/notes/. |
| `codebase-migrate` | Large-scale migration. Out of bootstrap scope. |
| `improve-codebase-architecture` | Architecture changes. Out of bootstrap scope. |

## Forbidden Skills (Phase 0-5)

Must NOT be invoked under any circumstances.

| Skill | Reason |
|-------|--------|
| `skill-installer` | Installs skills from external sources. CRITICAL risk. Requires Phase 6+ quarantine pipeline. |
| `skill-creator` | Creates new skill definitions. Out of bootstrap scope. |
| `skill-share` | Shares skills on Slack. Network + external service risk. |
| `update-config` | Modifies Claude Code harness settings.json. MCP config mutation. |
| `docs-manager` | May modify project.md, process.md, CLAUDE.md. Writes outside approved scope. |
| `claude-task-tracker` | May write task state files outside approved scope. |
| `file-organizer` | May move/delete files. Destructive operation risk. |
| `tailored-resume-generator` | Out of scope. |
| `grill-me` | Interview workflow. Not needed in bootstrap. |

### Document Processing Skills (Forbidden)

| Skill | Reason |
|-------|--------|
| `pdf` | PDF manipulation. Out of bootstrap scope. |
| `docx` | Word document manipulation. Out of bootstrap scope. |
| `pptx` | Presentation manipulation. Out of bootstrap scope. |
| `xlsx` | Spreadsheet manipulation. Out of bootstrap scope. |
| `paperjsx` | Office/PDF report generation. Out of bootstrap scope. |

### MCP/Computer-Use Skills (Forbidden)

Any skill that uses `mcp__computer-use__*` tools (UI-TARS, screen control, keyboard/mouse automation) is **FORBIDDEN** in all phases unless explicitly approved by reviewer for a specific task.

## Auto-Trigger Policy (Phase 0-5)

Phase 0-5 does NOT support automatic skill triggering. All skill invocations require:

1. **Explicit user request** (user says "/skill-name" or "use X skill")
2. **Workflow decision** (agent proposes, reviewer approves in batch plan)
3. **Mandatory code-quality skills** (`coding-discipline`, `devprocess`, `ai-code-review`, `security-checklist`, `performance-lint`, `debug-logging`) may be invoked by the agent as reasoning workflows during approved code tasks, but must not trigger any of the forbidden actions listed in `tool-policy.md`.

## Risk Summary

| Risk Level | Count | Examples |
|------------|:-----:|----------|
| Recommended | ~12 | coding-discipline, devprocess, ai-code-review |
| Reference Only | ~12 | caveman, codebase-search, brand-guidelines |
| Deferred | ~20 | claude-git-helper, memory-bridge, connect-apps |
| Forbidden | ~20 | skill-installer, update-config, computer-use skills |

## Related Documents

- `tool-policy.md` -- Phase 0-5 tool restrictions
- `external-skill-intake.md` -- Skill intake policy (reference_only/candidate/defer/reject)
- `integration-contracts.md` -- Contract 6 (SkillIntakeRecord), Contract 7 (ToolRiskRecord)
