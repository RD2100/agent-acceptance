# CodeGraph Stale-aware Policy -- R4

> Batch X (R4), 2026-05-27
> R4 = stale-aware policy only. No reindex. No init. No DB modification.

## 1. CodeGraph Role

CodeGraph is a **code intelligence candidate**, NOT a source of truth. CodeGraph results are advisory only. They do not override filesystem, git status, or direct command output.

## 2. Fact Priority Chain

When resolving any question about code state, the following priority order applies:

1. **current filesystem** (`Test-Path`, `Get-Content`, `ls`)
2. **git status** (`git status --short`, `git log`, `git diff`)
3. **current command output** (actual tool execution result)
4. **CodeGraph index** (only if `trusted_for_current_run=true` AND `index_freshness=current`)
5. **RD2100 memory** (read-only, Phase 0-5)
6. **external documentation**

CodeGraph at priority 4 means: even a perfectly fresh index is BELOW filesystem and git. A stale index is BELOW memory.

## 3. Target Root Rules

- Each CodeGraph index has exactly one `target_root` (the directory it indexes)
- The index represents code state at the time it was last indexed
- If `target_root` has changed (new commits, file modifications) since indexing, the index is **stale**
- `target_root_status` must be verified before trusting any index

## 4. Index Freshness Rules

| Freshness | Condition | trusted_for_current_run |
|-----------|-----------|:---:|
| `current` | Index DB modification time within 1 hour of target_root's last git commit | may be `true` after verification |
| `stale` | Index exists but modification time >1 hour behind git commit | must be `false` |
| `unknown` | Cannot verify freshness (sqlite3 unavailable, timestamp unreadable) | must be `false` |
| `empty` | Index exists but 0 files indexed | must be `false` |
| `not_applicable` | No codegraph.db exists | must be `false` |

## 5. Stale / Unknown / Empty Index Handling

- **stale**: Set `trusted_for_current_run=false`. Do NOT auto-reindex. Use Grep/Read as fallback.
- **unknown**: Set `trusted_for_current_run=false`. Record as `verification_gap`. Do NOT auto-reindex.
- **empty**: Set `trusted_for_current_run=false`. Record as `verification_gap`. Do NOT trigger reindex.
- **current**: May set `trusted_for_current_run=true` after freshness is independently verified (not just from codegraph_status).

## 6. Reindex Human Gate

Reindex requires ALL of:
1. Reviewer explicitly approves the reindex in batch scope
2. Pre/post `git status --short` recorded
3. EvidenceIndex record created for the reindex operation
4. No concurrent writes to target_root
5. Target root verified unchanged during reindex

**Automatic reindex is permanently forbidden.** Even in future phases, no tool or script may trigger reindex without explicit human approval.

## 7. EvidenceIndex Integration

When CodeGraph query results are used as evidence, the EvidenceIndex entry MUST include:
- `index_path`: which codegraph.db was queried
- `index_freshness`: current/stale/unknown/not_applicable
- `query_timestamp`: when the query was made
- `result_summary`: what was found
- If freshness is stale/unknown, this must be noted in the EvidenceIndex status field

## 8. When human_required

- Reindex requested (any index)
- Index freshness disputed (agent claims current, reviewer sees stale)
- Multiple indexes disagree on the same code fact
- CodeGraph result contradicts filesystem or git observation
- CodeGraph used as sole evidence for a gate decision

## 9. When blocked

- Auto-reindex detected (any mechanism)
- Index deleted or .codegraph DB modified without approval
- CodeGraph result used to override filesystem/git fact
- Reindex performed without EvidenceIndex record
- CodeGraph claimed as source of truth over filesystem/git
- CodeGraph used to automatically approve R3 adapter

## 10. Registered Indexes (R4)

| Index | Path | DB Size | Files | Status | Trusted |
|-------|------|:---:|:---:|--------|:---:|
| agent-acceptance | `.codegraph/codegraph.db` | 139 KB | 0 | empty | false |
| dev-frame | `D:\dev-frame\.codegraph\codegraph.db` | 13.5 MB | 410 | present | needs verification |
| test-frame | `D:\test-frame\.codegraph\codegraph.db` | 1.8 MB | 102 | present | needs verification |
| codegraph-impl | `D:\dev-frame\codegraph\` | N/A | N/A | forbidden (source code) | N/A |
