# CR0 Capability Inventory Reviewer Checklist

> Batch CR-A, 2026-05-27
> 10-step review for CR0 capability inventory.

## Step 1: Coverage Check
- [ ] All 17 capabilities registered
- [ ] No capability omitted from inventory

## Step 2: Schema Check
- [ ] capability-record.schema.json parses
- [ ] auto_use_allowed const=false enforced
- [ ] execution_allowed const=false enforced
- [ ] mutation_allowed const=false enforced

## Step 3: Access Mode Check
- [ ] Every capability has default_access_mode
- [ ] Critical/high capabilities are NOT read_write or enabled

## Step 4: Risk Level Check
- [ ] Every capability has default_risk
- [ ] Critical/High capabilities have human_gate_required=true
- [ ] Risk levels match R0-R7 resource registry

## Step 5: Preferred/Forbidden Check
- [ ] Every capability has preferred_for tasks defined
- [ ] Every capability has forbidden_for tasks defined
- [ ] Structural code understanding -> CodeGraph preferred
- [ ] Literal search -> rg/Grep preferred

## Step 6: Fallback Check
- [ ] Every capability with must_explain_if_skipped=true has fallback
- [ ] Fallback capabilities are lower risk than preferred
- [ ] No fallback loops (A -> B -> A)

## Step 7: Evidence Check
- [ ] Every capability has evidence_required defined
- [ ] Evidence is collectible in current phase

## Step 8: Forbidden Action Check
- [ ] No capability has execution_allowed=true
- [ ] No capability has auto_use_allowed=true
- [ ] No capability has mutation_allowed=true

## Step 9: Cross-Reference Check
- [ ] Capability inventory consistent with R0 resource registry
- [ ] Capability risk matrix consistent with R0 resource risk matrix
- [ ] Access modes consistent with R1-R7 phase policies

## Step 10: Gate Decision

```
Is any capability missing from inventory?         -> YES = needs_revision
Does schema fail to parse?                          -> YES = needs_revision
Is auto_use/execution/mutation not false?          -> YES = needs_revision
Is critical/high capability missing human gate?    -> YES = needs_revision
All pass?                                            -> pass_to_review
```

## Decision: [ ] pass_to_review / [ ] needs_revision / [ ] blocked
