# Agent Role Boundaries

> Version: v1.0
> Purpose: Prevent role confusion that caused the HANDOFF workflow failure

## The Problem

We spent 6+ rounds trying to automate a HANDOFF workflow: GPT generates HANDOFF → CDP submit to new conversation → new GPT continues execution. This failed because:

1. Web GPT has no local repo access — cannot execute git/pytest
2. CDP is fragile — element selectors change, modals block, content doesn't persist
3. Role confusion — treating Web GPT as executor instead of reviewer

## Correct Roles

| Role | Who | Does | Does NOT |
|------|-----|------|----------|
| Reviewer | Web GPT | Review evidence packs, return verdicts, authorize tasks, generate TaskSpecs | Execute git, run tests, modify files, access local repo |
| Executor | Claude Code | Read repo, write code, run tests, build evidence packs, CDP submit, git commit | Skip GPT review, claim closed without GPT accepted |
| Bridge | CDP Playwright | Upload evidence pack ZIP, type review prompt, capture GPT reply | Handle task handoff, execute code, make decisions |

## Rules

1. **Web GPT stays in its lane.** It is the reviewer, not the executor.
2. **Claude Code owns execution.** All git/code/test operations happen locally.
3. **CDP is the bridge.** Only for submitting evidence packs and capturing GPT replies.
4. **BOOT_CONTEXT + memory/ is the handoff.** No more HANDOFF.md generation.
5. **No CDP-based handoff automation.** The local agent reads files directly.
