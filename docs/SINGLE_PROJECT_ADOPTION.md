# Single-Project Adoption Guide

How to adopt `D:\agent-acceptance` as the agent constraint pack for your project.

## Three Adoption Tiers

### Light — Report Template Only

The agent uses the execution report format but no other constraints.

**Setup**: Copy this into your project's `AGENTS.md`:

```markdown
## Agent Reporting

All non-trivial tasks must report using the format defined in:
`D:\agent-acceptance\docs\EXECUTION_REPORT_TEMPLATE.md`
```

**Cost**: 1 line.
**Gain**: Consistent, scannable reports with Hard Stop Check.
**Missing**: Tier enforcement, command validation, queue automation.

### Standard — Report + Constraints

The agent follows task discipline, hard stops, and Tier rules.

**Setup**: Copy `D:\agent-acceptance\templates\AGENTS.single-project.md` to `<your-project>\AGENTS.md`.

**Cost**: One file copy.
**Gain**: Full Tier 0/1/2 rules, hard stop enforcement, mandatory reports.
**Missing**: Automated queue/batch execution.

### Strict — Full WorkQueue Runner

The agent runs verification through the PowerShell WorkQueue runner.

**Setup**:

1. Copy `AGENTS.single-project.md` to `<your-project>\AGENTS.md`.
2. Create your project-specific queue and batch files (copy from `templates/`).
3. **Important**: Set `runner` in your queue JSON to the absolute path `D:\\agent-acceptance\\scripts\\Run-Batch.ps1` (pointing at the constraint pack, not your project). If you copied the scripts into your project too, relative paths like `scripts/Run-Batch.ps1` also work — Test-WorkQueue auto-discovers them.
4. Add your queue to the agent's default run list.

**Cost**: ~15 min to configure queues and verify paths.
**Gain**: Automated Tier escalation, forbidden-command scan, artifact validation.
**Missing**: None — full constraint pack.

## Quick Start (Standard tier, 30 seconds)

```powershell
copy D:\agent-acceptance\templates\AGENTS.single-project.md D:\your-project\AGENTS.md
```

That's it. The agent will now:
- Read Tier rules before executing
- Report using the Execution Report Template
- Stop and ask before destructive actions

## Adding Your Own Quality Checks

1. Copy `templates\project-batch-quality.json` and edit the tasks.
2. Copy `templates\project-quality.queue.json` and point `task_file` at your batch.
3. Run: `powershell -File D:\agent-acceptance\scripts\Run-WorkQueue.ps1 -QueueFile <your-queue>.queue.json`

See `docs\SINGLE_PROJECT_QUEUE_SPEC.md` for field reference.

## File Map

| File | Purpose | Who reads it |
|------|---------|-------------|
| `templates\AGENTS.single-project.md` | Entry template for any project | Agent (at session start) |
| `docs\AGENT_WORKQUEUE_RULES.md` | Tier 0/1/2 definitions, escalation rules | Agent (every task) |
| `docs\EXECUTION_REPORT_TEMPLATE.md` | Mandatory report structure | Agent (after every task) |
| `docs\SINGLE_PROJECT_QUEUE_SPEC.md` | Queue/batch JSON field reference | Human (when authoring queues) |
| `docs\COMMAND_CHEATSHEET.md` | Copy-paste verification commands | Agent (during task) |
| `templates\project-quality.queue.json` | Queue template for a project | Human → Agent |
| `templates\project-batch-quality.json` | Batch task template for a project | Human → Agent |
| `scripts\Test-WorkQueue.ps1` | Self-test all queue integrity | Agent (smoke check) |
| `scripts\Run-Batch.ps1` | Execute a batch task file | Agent (verification) |
| `scripts\Run-WorkQueue.ps1` | Execute a single queue | Agent (verification) |
| `scripts\Run-QueueGroup.ps1` | Execute multiple queues (serial/parallel) | Agent (verification) |
| `scripts\Run-Smoke.ps1` | Lightweight project smoke test | Agent (quick check) |
| `scripts\Run-AllQueues.ps1` | Run all registered queues | Agent (full verification) |

## FAQ

**Q: Does this require Python?**
A: No. The runner scripts are PowerShell. Batch tasks may call Python if your project uses it.

**Q: Does this require `ai-workflow-hub`?**
A: No. The constraint pack is independent. Some example batch tasks reference `ai-workflow-hub` CLI — replace those with your project's verification commands.

**Q: How do I change the constraint pack path?**
A: Edit `AGENTS.md` — replace `D:\agent-acceptance` with your constraint pack location. You can also set an environment variable: `$env:AGENT_CONSTRAINT_PACK = "D:\agent-acceptance"` and reference it from AGENTS.md.

**Q: What if my queue doesn't appear in Test-WorkQueue?**
A: Test-WorkQueue scans `agent-workqueue/*.queue.json`. Place your queue file there and it will be auto-discovered. The pilot project confirmed this works: one new queue file added 5 checks (PASS=26 → PASS=31).

**Q: Can I run this on Linux/macOS?**
A: The PowerShell scripts require PowerShell 7+. Windows PowerShell 5.1 also works.

**Q: What if I don't want all the rules?**
A: Use the Light tier. You can always upgrade later.
