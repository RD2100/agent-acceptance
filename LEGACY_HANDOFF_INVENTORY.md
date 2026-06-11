# Legacy Handoff Inventory

> Status: inventory only
> Task: HANDOFF-PIPELINE-REFACTOR-A1
> Scope: list legacy handoff/history materials without modifying them.

No legacy files were deleted, moved, renamed, rewritten, or marked during this inventory.

| Path | Purpose | Possible stale risk | Audit/reference use | Current replacement authority |
|---|---|---:|---|---|
| `HANDOFF.md` | Legacy coding-agent handoff | High | Historical agent context | `HANDOFF_SOURCE_OF_TRUTH.md` + GPT-approved handoff artifacts |
| `HANDOFF_V5.md` | Legacy handoff version | High | Historical transition record | `HANDOFF_SOURCE_OF_TRUTH.md` + GPT-approved handoff artifacts |
| `HANDOFF_V6.md` | Legacy handoff version | High | Historical transition record | `HANDOFF_SOURCE_OF_TRUTH.md` + GPT-approved handoff artifacts |
| `PROJECT_HISTORY.md` | Long project history | Medium/High | Audit trail and historical research | P0 evidence packs, verified GPT verdicts, `.ai/tasks/`, `_reports/PAPER_PROJECT_INDEX.json` |
| `PROJECT_HISTORY_FINAL.md` | Legacy final history snapshot | High | Historical snapshot only | P0 evidence packs and current ledgers |
| `HISTORY_ANALYSIS.md` | Historical analysis | Medium | Analysis reference | Current source map and stale check |
| `BOOT_CONTEXT.md` | Cold-start context | Medium | P1 only if GPT-approved and stale-checked | `HANDOFF_SOURCE_OF_TRUTH.md`, stale check, P0 sources |
| root `GPT_*.txt` | Legacy/ad-hoc GPT captures | Medium/High | Reference only unless verified | `evidence_packs/**/GPT_REVIEW_RESULT*.txt` verified by `scripts/verify_gpt_reply.py` |
| `_reports/*gpt_response*.txt` | Captured review responses | Medium | Secondary review reference | Bound source map entries with sha256 |
| `memory/index.md` | Memory recall index | Medium | Recall layer | P0/P1 sources for status/verdict/test claims |
| `.claude/skills/claude-memory-compiler/knowledge/**` | Compiled memory knowledge | Medium | Recall layer | P0/P1 sources for status/verdict/test claims |

## Risk summary

- Multiple legacy handoff/history files exist at repository root.
- They are useful for audit, but must not be treated as current authority.
- Current authority hierarchy is defined in `HANDOFF_SOURCE_OF_TRUTH.md`.
- Legacy files should only receive SUPERSEDED/LEGACY notices after explicit user authorization; this task phase did not modify them.
