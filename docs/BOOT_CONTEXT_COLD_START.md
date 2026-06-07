# BOOT_CONTEXT Cold Start Guide

> Version: v1.0
> For: New Claude Code / coding agents joining the DevFrame project

## What This Is

BOOT_CONTEXT.md is the short cold-start entry point for new agents. Instead of reading the full PROJECT_HISTORY.md (~25K chars), agents start here (3-4K chars) and drill down as needed.

## Agent Reading Order

```
1. BOOT_CONTEXT.md          ← START HERE (3-4K chars, 60 seconds)
2. memory/index.md          ← Find relevant task/knowledge entries
3. memory/tasks/<TASK>.md   ← Current task details (300-800 chars each)
4. memory/knowledge/*.md    ← Topic knowledge (500-1200 chars each)
5. PROJECT_HISTORY.md       ← Full history (only when needed, 25K+)
6. CLAUDE.md                ← Agent behavior protocol
7. docs/WORKFLOW_AUDIT_LEDGER.yaml ← Task state machine records
```

## Role Boundaries

```
Web GPT (ChatGPT):
  Role: REVIEWER, DECISION-MAKER, PLANNER
  Does: Review evidence packs, return accepted/blocked verdicts, authorize next tasks
  Does NOT: Execute git commands, access local repo, run tests, modify files

Claude Code / local agent:
  Role: EXECUTOR
  Does: Read repo files, execute git, run tests, build evidence packs, CDP submit
  Does NOT: Skip GPT review, claim closed without GPT accepted

CDP automation:
  Role: BRIDGE (submit evidence packs to Web GPT, capture replies)
  Does NOT: Handle task handoff, execute code, make decisions
```

## How to Cold Start a New Agent

1. Tell the agent: "You are the DevFrame execution agent at D:\agent-acceptance. Read BOOT_CONTEXT.md, then check memory/index.md for current status."
2. The agent reads BOOT_CONTEXT.md (60 seconds)
3. The agent checks memory/index.md for current focus
4. The agent reads the relevant memory/tasks/*.md for current task details
5. The agent confirms understanding and begins execution

## No More HANDOFF

The old HANDOFF.md workflow is deprecated. Do NOT:
- Generate HANDOFF_V*.md files
- Submit HANDOFF docs to Web GPT for "review"
- Try to make Web GPT execute local git commands
- Use CDP for task handoff

Instead: the local agent reads files from the repo directly. Web GPT only reviews evidence packs.
