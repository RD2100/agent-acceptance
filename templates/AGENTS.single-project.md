# AGENTS.md — Single-Project Agent Constraint Pack

> Copy this file to any project root to enforce agent execution discipline.
> Reads `D:\agent-acceptance` as the constraint authority. No install, no deps.

## Constraint Pack Path

The path `D:\agent-acceptance` below is the **constraint pack root**. If your constraint pack lives elsewhere, replace all occurrences in this file. Alternatively, set the environment variable:

```powershell
$env:AGENT_CONSTRAINT_PACK = "D:\agent-acceptance"
```

## Minimum Read

Before any non-trivial task, read these **two** files:

1. `D:\agent-acceptance\docs\AGENT_WORKQUEUE_RULES.md` — Tier 0/1/2 rules, escalation signals
2. `D:\agent-acceptance\docs\EXECUTION_REPORT_TEMPLATE.md` — mandatory report format

## Task Discipline (every non-trivial task)

1. **Define scope** before writing code: what, why, boundaries, forbidden actions.
2. **State verification command** up front. Copy-paste from `D:\agent-acceptance\docs\COMMAND_CHEATSHEET.md`.
3. **Run the stated verification** after changes. Do not skip.
4. **Report** using the Execution Report Template. Must include:
   - Executive Decision: `pass / blocked / needs review`
   - Reviewer Index
   - Evidence (exact commands + output summaries)
   - Hard Stop Check
   - Remaining Risks (max 5)

## Hard Stops

Before these actions, **stop and request user confirmation**:

- `commit`, `push`, `reset --hard`, `branch -D`, `clean -f`
- `cleanup --apply`, `review-recovered --apply`
- Real backend / E2E calls with budget
- Deleting artifacts or historical evidence
- Modifying skill files, memory files, or `.claude/`

## Verification

Preferred entry points (from repo root, PowerShell):

```powershell
# Self-test the constraint pack
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Test-WorkQueue.ps1

# Run one batch
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Run-Batch.ps1 -TaskFile D:\agent-acceptance\scripts\examples\batch-local-quality.json

# Run one queue
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\scripts\Run-WorkQueue.ps1 -QueueFile D:\agent-acceptance\agent-workqueue\local-quality.queue.json
```

## Project-specific quality

To define your own checks, copy and adapt:

- `D:\agent-acceptance\templates\project-quality.queue.json` → your project's queue
- `D:\agent-acceptance\templates\project-batch-quality.json` → your project's task batch

See `D:\agent-acceptance\docs\SINGLE_PROJECT_ADOPTION.md` for full details.

## Do NOT

- Execute Tier 2 items without explicit ACK
- Report PASS when checks failed
- Skip the Hard Stop Check in reports
- Modify source outside task boundaries
- Introduce new tools or daemons without approval
