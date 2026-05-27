# R4 CodeGraph Reviewer Checklist -- RD2100 Agent Runtime v2

> Batch X (R4), 2026-05-27
> 10-step review process for R4 CodeGraph outputs.

## Step 1: Index Path Registration

Verify all 4 CodeGraph indexes are registered with correct paths.

| Index | Path | Registered? |
|-------|------|:---:|
| agent-acceptance | `.codegraph/codegraph.db` | [ ] |
| dev-frame | `D:\dev-frame\.codegraph\codegraph.db` | [ ] |
| test-frame | `D:\test-frame\.codegraph\codegraph.db` | [ ] |
| codegraph-impl | `D:\dev-frame\codegraph\` | [ ] |

## Step 2: Target Root Clarity

Verify each index has a clear `target_root` that matches the actual project root.

| Index | target_root | Matches? |
|-------|-------------|:---:|
| agent-acceptance | `D:\agent-acceptance` | [ ] |
| dev-frame | `D:\dev-frame` | [ ] |
| test-frame | `D:\test-frame` | [ ] |
| codegraph-impl | `D:\dev-frame\codegraph` | [ ] |

## Step 3: Index Status

Verify `index_status` is explicitly set (not defaulted, not omitted).

| Index | Status | Correct? |
|-------|--------|:---:|
| agent-acceptance | empty | [ ] |
| dev-frame | present | [ ] |
| test-frame | present | [ ] |
| codegraph-impl | N/A (forbidden) | [ ] |

## Step 4: Freshness Verification

Verify `index_freshness` is explicitly set and matches the index's actual state.

| Index | Freshness | Verified? |
|-------|-----------|:---:|
| agent-acceptance | not_applicable (empty) | [ ] |
| dev-frame | needs verification | [ ] |
| test-frame | needs verification | [ ] |
| codegraph-impl | not_applicable | [ ] |

## Step 5: trusted_for_current_run Audit

Verify the rule: `trusted_for_current_run=true` ONLY when `index_freshness=current`.

| Index | Freshness | trusted? | Rule Violation? |
|-------|-----------|:---:|:---:|
| agent-acceptance | empty/not_applicable | false | [ ] |
| dev-frame | TBD | false (until verified) | [ ] |
| test-frame | TBD | false (until verified) | [ ] |
| codegraph-impl | N/A | false | [ ] |

## Step 6: Reindex Audit

Verify no reindex occurred during R4.

- [ ] No `codegraph init` command executed
- [ ] No `codegraph reindex` command executed
- [ ] No codegraph.db modification timestamp changed during R4
- [ ] No new codegraph.db created

## Step 7: .codegraph Integrity

Verify no .codegraph files were modified.

- [ ] `.codegraph/codegraph.db` checksum unchanged
- [ ] `.codegraph/.gitignore` unchanged
- [ ] No new files in `.codegraph/`

## Step 8: Stale/Unknown Detection

Verify no stale or unknown index was treated as current fact.

- [ ] No CodeGraph result used to claim "the code says X" without freshness check
- [ ] No CodeGraph result used to override `Test-Path` or `git status`
- [ ] All CodeGraph-derived claims are tagged with index freshness

## Step 9: Cross-Project Coverage

Verify all 4 projects are covered. Verify no project's CodeGraph was used to justify actions in another project without freshness verification.

## Step 10: Gate Decision Tree

```
Was any reindex performed?                  -> YES = BLOCKED
Was any .codegraph DB modified?             -> YES = BLOCKED
Was CodeGraph used to override filesystem?  -> YES = BLOCKED
Is trusted_for_current_run=true with        -> YES = needs_revision
  stale/unknown/empty freshness?
Is any index missing from registry?         -> YES = needs_revision
Are negative tests < 20?                    -> YES = needs_revision
Was CodeGraph result presented as fact      -> YES = needs_revision
  without freshness metadata?
Was CodeGraph used to auto-approve R3?      -> YES = needs_revision
Is CodeGraph status omitted from report?    -> YES = needs_revision
Was CodeGraph query failure marked pass?    -> YES = needs_revision
All pass?                                    -> pass_to_review
Insufficient local facts for risk decision? -> human_required
```

## Decision: [ ] pass_to_review / [ ] needs_revision / [ ] blocked / [ ] human_required
