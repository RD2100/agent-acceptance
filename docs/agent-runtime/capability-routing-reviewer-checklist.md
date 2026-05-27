# Capability Routing Reviewer Checklist -- CR4

> Batch CR-B, 2026-05-27
> 10-step checklist for reviewing capability routing in ExecutionReports.

## Step 1: Audit Section Presence
- [ ] Capability Routing Audit heading exists in report
- [ ] All 6 columns present: Task Area, Expected Capability, Status, Used?, Reason If Not Used, Fallback, Evidence
- [ ] Forbidden capabilities verification table present

## Step 2: Task Type Verification
- [ ] Primary task type matches the majority of work performed
- [ ] If multiple task areas, each has its own row
- [ ] Task type is one of the 13 defined types

## Step 3: Capability Selection Verification
- [ ] Expected capability matches routing matrix for this task type
- [ ] If preferred is CodeGraph, status check was performed
- [ ] If preferred is N/A (not authorized), this is correctly stated

## Step 4: Status Check Evidence
- [ ] Status field is backed by evidence (not "assumed")
- [ ] Evidence is referenced in Evidence column
- [ ] Evidence is verifiable (codegraph_status output, file path, command result)

## Step 5: Skip Rationale Audit
- [ ] Every Used?=no row has Reason If Not Used filled
- [ ] Reason is specific (not "skipped", "not needed", "too slow")
- [ ] Reason is consistent with known capability state

## Step 6: Fallback Chain Audit
- [ ] Fallback matches approved chain in routing matrix
- [ ] Fallback is not also forbidden
- [ ] Fallback risk level is appropriate for the task

## Step 7: Forbidden Capability Audit
- [ ] No forbidden capability appears with Used?=yes
- [ ] Forbidden capabilities verification table is complete

## Step 8: Cross-Reference with Forbidden Action Check
- [ ] Capability audit consistent with forbidden action check in same report
- [ ] No capability audit says "not used" while bash log shows invocation
- [ ] No discrepancy between declared and actual tool usage

## Step 9: Negative Test Coverage Verification
- [ ] If any capability was used outside routing rules, negative test NEG-CR-* covers this case
- [ ] Capability routing negative tests are >= 30 in total

## Step 10: Gate Decision

```
Is Capability Routing Audit missing?                 -> needs_revision
Is forbidden capability used?                        -> blocked
Is preferred skipped without reason?                 -> needs_revision
Is status check evidence missing?                    -> needs_revision
Is task type misclassified?                          -> needs_revision
Is fallback not in approved chain?                   -> needs_revision
Is auto-trigger/auto-execute detected?               -> blocked
Is Phase 6C presented as unblocked?                  -> blocked
All pass?                                              -> pass_to_review
```

## Decision: [ ] pass_to_review / [ ] needs_revision / [ ] blocked / [ ] human_required
