---
name: agent-acceptance
description: Formal SADP development workflow with audit gates. Use when user says "@go", requests formal task execution with audit trail, wants TaskSpec+ExecutionReport+Audit chain, or needs evidence-based delivery with P0 safety gates. NOT for casual conversation or trivial edits.
---

# agent-acceptance 鈥?SADP Workflow

Formal development protocol: Gate 0 鈫?TaskSpec 鈫?Execute 鈫?ExecutionReport 鈫?Audit 鈫?Pass/Block/Escalate.

## Trigger

This workflow activates on:
- `@go` command
- User asks for "formal workflow", "SADP", "with audit", "task dispatch"
- User wants evidence-based delivery with independent audit

## Pre-flight: Gate 0

Before any work, verify:
1. Project has `AGENTS.md` referencing `rules/core.md`. If not, offer bootstrap.
2. No uncommitted governance changes (`rules/`, `AGENTS.md`, `hooks/`).
3. Task has a TaskSpec with: id, description, intent, write_set, success criteria.
4. Staged diff scanned by `sadp-audit.ps1` 鈥?PASS.

Gate 0 is **not optional**. Blocked means blocked.

## Workflow

### 1. TaskSpec
```yaml
id: string
description: string
intent: string
write_set: [file_paths]
success: [criteria]
risk: low | medium | high
```

### 2. Execute
Implement per TaskSpec. Collect evidence: diffs, command output, exit codes.

### 3. ExecutionReport
```yaml
task_id: string
status: passed | failed | blocked
changes: [files]
evidence: [artifacts]
issues: [findings]
```

### 4. Audit (Plan Auditor)
Independent review against:
- P0 hard stops (no violations)
- TaskSpec coverage (all files in write_set)
- Evidence quality (not "looks correct")
- No fake green (FAILED != PASS)
- Secret safety (sadp-audit.ps1)

Verdict: **PASS** | **BLOCKED** | **ESCALATE**

## P0 Hard Stops (BLOCK delivery if violated)

| # | Rule |
|---|------|
| 1 | No destructive git without human approval |
| 2 | No secrets in code, logs, or reports |
| 3 | No command injection or path traversal |
| 4 | No fake green |
| 5 | No write to files outside TaskSpec write_set |
| 6 | No capability without inventory registration |

## Secret Safety (always active during workflow)

| # | Rule |
|---|------|
| 1 | Never write real API keys into repo files |
| 2 | .env.example only placeholders: `__REPLACE_WITH_YOUR_OWN_KEY__` |
| 3 | Treat "example", "sample", "template", "packaging", "docker", "README" as secret-sensitive |
| 4 | Run `sadp-audit.ps1` before git add/commit |
| 5 | Suspected secret 鈫?STOP immediately |
| 6 | Committed secret 鈫?REVOKE/ROTATE before cleaning history |
| 7 | Scanning is mandatory, not optional |


## Dispatch (Automated)

Do NOT output TaskSpec as plain text for manual copy. Use `opencode run`:

```powershell
# Dispatch to audit/execution agent
opencode run -m "deepseek/deepseek-v4-pro" -c "任务描述 + 文件路径"

# Resume existing session
opencode run -s <session_id> -c "继续指令"
```

### Standard dispatch pattern

1. Write TaskSpec JSON to `tasks/t-<id>.json`
2. Dispatch: `opencode run -m "deepseek/deepseek-v4-pro" -c "阅读 tasks/t-<id>.json，执行任务，将 ExecutionReport 写入 tasks/t-<id>-result.md"`
3. Poll result file or check session output
4. Load ExecutionReport → Audit → PASS/BLOCK/ESCALATE

### Model selection

| Task | Model |
|------|-------|
| Execution (coding) | `deepseek/deepseek-v4-pro` |
| Audit (review) | `deepseek/deepseek-v4-pro` |
| Planning (TaskSpec) | current agent |

### Verification

After dispatch, the current agent must:
- Confirm result file exists
- Read ExecutionReport
- Run independent spot checks (not just trust the report)
- Issue final verdict
## Verification Rule

Every claim needs: command + exit code + output summary. "Looks correct" is invalid evidence.

## Post-completion

After non-trivial work, auto-write summary report 鈫?dispatch to audit agent 鈫?apply fixes 鈫?verify.

Full protocol: `docs/agent-runtime/sub-agent-dispatch-protocol.md`
Full rules: `rules/core.md`, `rules/security.md`