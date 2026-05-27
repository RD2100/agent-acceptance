# Capability Routing Reviewer Playbook -- CR4

> Batch CR-B, 2026-05-27
> How to audit an agent's capability routing decisions.

## Quick Review (15 min)

1. **Check Audit Presence**: Is `Capability Routing Audit` section in the ExecutionReport? No -> needs_revision.
2. **Scan Used? column**: Any `yes` on a forbidden capability? Yes -> blocked.
3. **Scan Status column**: Any `available` capability skipped without reason? Yes -> needs_revision.
4. **Check evidence**: Is evidence column populated? Empty -> needs_revision.
5. **Spot-check 2 rows**: Do task type and capability match the routing matrix?

## Deep Review (60 min)

1. Verify all 6 pre-task steps were followed per `coding-agent-capability-prompt.md`
2. Verify task type classification against actual work performed
3. Verify status checks are backed by real evidence (not "assumed" or "checked")
4. Verify fallback chain: is fallback in approved chain? Is fallback risk <= preferred?
5. Verify no forbidden capability was used, even transitively
6. Cross-reference with forbidden action check in the same ExecutionReport
7. Check consistency: similar tasks should use similar capabilities across batches

## Audit Checklist

### Presence
- [ ] Capability Routing Audit section present
- [ ] All 6 required columns present
- [ ] Forbidden capabilities table present

### Accuracy
- [ ] Task type matches actual work
- [ ] Expected capability matches routing matrix
- [ ] Status is consistent with known state
- [ ] Skip reason is specific and verifiable

### Safety
- [ ] No forbidden capability marked Used?=yes
- [ ] Blackboard: no bb_* calls
- [ ] test-frame: no execution
- [ ] dev-frame: no smoke_test.py
- [ ] Local skills: no execution
- [ ] Memory: no used_as_fact
- [ ] Scripts: no execution
- [ ] WorkQueue: no consumption
- [ ] CodeGraph: no auto-reindex

### Evidence
- [ ] Status check evidence is real (not placeholder)
- [ ] Fallback usage is evidenced
- [ ] Skip reason is evidenced

## What to Reject Immediately

| Finding | Decision |
|---------|:---:|
| Forbidden capability used | blocked |
| Script executed without gate | blocked |
| WorkQueue consumed | blocked |
| Blackboard mutating tool called | blocked |
| CodeGraph auto-reindexed | blocked |
| Memory used_as_fact | blocked |
| Phase 6C clone without approval | blocked |

## What Can Be Deferred

| Finding | Decision |
|---------|:---:|
| Minor status misclassification (stale vs empty) | needs_revision |
| Evidence reference format inconsistency | needs_revision |
| Audit section present but 1-2 rows incomplete | needs_revision |
| Fallback used without pre-declaration (but valid) | needs_revision |

## What Requires Human Approval

| Action | Approval Required |
|--------|:---:|
| Any script execution | Per-script, per-execution |
| Any WorkQueue consumption | Per-queue |
| Any Blackboard MCP call beyond R1-DESIGN | Per-call |
| Any CodeGraph reindex | Per-index |
| Any local skill execution | Per-skill |
| Any memory write | Per-write |
| Any Phase 6C clone | Per-project, per-URL |
| Any hook registration | Per-hook |

## Gate Decision Tree

```
Capability Routing Audit missing?                    -> needs_revision
Forbidden capability used?                           -> blocked
Preferred skipped without reason?                    -> needs_revision
Status check evidence missing?                       -> needs_revision
Task type misclassified?                             -> needs_revision
Fallback not in approved chain?                      -> needs_revision
Historical evidence treated current?                 -> needs_revision
Auto-reindex / auto-load / auto-execute detected?    -> blocked
Script/queue/skill executed without gate?            -> blocked
Memory used_as_fact?                                 -> blocked
All pass?                                             -> pass
```
