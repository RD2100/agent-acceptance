# DevFrame User Guide — Synthetic Paper Demo

## Quick Start
```bash
cd D:\agent-acceptance
python -m pytest tests/ -q          # 247 PASS expected
python tools/ai_guard.py task .ai/current-task.yaml  # PASS with warnings
```

## What This System Does
Automates AI-assisted coding with GPT review gates:
1. TaskSpec → Code → Tests → Evidence Pack → GPT Review → Accepted/Blocked → Commit
2. Privacy guard prevents paper/secret/private leaks
3. Cold-start via BOOT_CONTEXT.md (no long HANDOFF docs)

## What It Doesn't Do
- No real paper processing (protocol-only, synthetic data)
- No whole-dirty-tree commits
- No guard bypass

## Key Files
- BOOT_CONTEXT.md: cold-start for new agents
- memory/index.md: task/knowledge index
- tools/ai_guard.py: pre-commit security gate
- scripts/review_queue.py: GPT review queue
