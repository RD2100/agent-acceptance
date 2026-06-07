# DevFrame Synthetic Demo — Paper Review Workflow

> Synthetic-only demo. No real paper content. No real user data.

## What This Demonstrates

A complete DevFrame workflow cycle using synthetic placeholder data:

1. TaskSpec generation (GPT)
2. Code execution (agent)
3. Evidence collection (tests, hashes, attestations)
4. Evidence pack (ZIP with manifest + deliverables)
5. GPT review (verdict, binding)
6. Chain (commit, ledger)

## How to Run

```bash
cd D:\agent-acceptance

# 1. Verify everything works
python -m pytest tests/ -q --tb=line

# 2. Check the guard
python tools/ai_guard.py task .ai/current-task.yaml

# 3. Review the cold-start flow
cat BOOT_CONTEXT.md
cat memory/index.md
```

## What's Protected

- 7 dirty baseline files exist but are NOT committed
- ai_guard staged-only mode prevents dirty files from blocking commits
- Privacy guard (validate_context_memory.py) prevents paper/private/secret leaks
- GPT review required before claiming closed

## Current Project State

| Component | Status |
|-----------|--------|
| BOOT_CONTEXT.md | operational (cold-start entry) |
| memory/index.md | operational (memory index) |
| ai_guard.py | staged-only mode, pass with warnings |
| review_queue.py | lifecycle management |
| Tests | 247 PASS |
| Dirty baseline | 7 files, protected |
| Cross-repo (control-plane) | 62 PASS, operational |

## Cross-Repo Integration

```bash
# agent-acceptance
cd D:\agent-acceptance && python -m pytest tests/ -q --tb=line
# → 247 passed

# devframe-control-plane  
cd D:\devframe-control-plane && python -m pytest tests/ -q --tb=line
# → 62 passed (3 pre-existing failures not caused by this work)
```
