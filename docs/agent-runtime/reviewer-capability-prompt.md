# Reviewer Capability Prompt -- CR2

> Batch CR-A, 2026-05-27
> Review template for auditing agent capability usage.

## Review Steps

### 1. Check Audit Presence

Is the Capability Routing Audit section present in the ExecutionReport?

- [ ] YES -> proceed
- [ ] NO -> **needs_revision** (missing required audit section)

### 2. Verify Task Type Classification

Does the declared task type match the actual work performed?

- [ ] Task type is one of the 13 defined types
- [ ] Task type matches the primary work performed

### 3. Verify Preferred Capability Selection

Does the expected capability match the routing matrix for this task type?

| Task Type | Expected Preferred | Actual Declared | Match? |
|-----------|-------------------|-----------------|:---:|
| <type> | <from matrix> | <from report> | |

### 4. Verify Status Check Evidence

Is the status check backed by evidence?

- [ ] Evidence column references actual output (not just "checked")
- [ ] Status is consistent with known state (e.g., agent-acceptance CodeGraph has 0 files -> status should be empty)

### 5. Verify Skip Rationale

If preferred capability was skipped:
- [ ] Reason is specific (not "not needed", "too slow")
- [ ] Reason is consistent with known state
- [ ] Fallback is valid per routing matrix

### 6. Verify No Forbidden Usage

Check the Used? column:

- [ ] No forbidden capability appears with Used?=yes
- [ ] test-frame: no aggregator/attribution execution
- [ ] dev-frame: no smoke_test.py execution
- [ ] Local skills: no execution
- [ ] Memory: no used_as_fact
- [ ] Scripts: no execution
- [ ] WorkQueue: no consumption

### 7. Verify Fallback Chain

If fallback was used:
- [ ] Fallback is in the approved fallback chain for this task type
- [ ] Fallback is not also forbidden
- [ ] Fallback risk <= preferred capability risk

### 8. Verify Cross-Task Consistency

If multiple task areas are declared:
- [ ] Each has its own row in the audit
- [ ] No task area was omitted
- [ ] Capability choices are consistent across similar tasks

### 9. Gate Decision

```
Is Capability Routing Audit missing?              -> YES = needs_revision
Is forbidden capability used?                     -> YES = blocked
Is preferred skipped without valid reason?        -> YES = needs_revision
Is fallback not in approved chain?                -> YES = needs_revision
Is status check evidence missing?                 -> YES = needs_revision
Is task type misclassified?                       -> YES = needs_revision
All pass?                                           -> pass
```

## Reviewer Notes Template

```markdown
## Capability Routing Review

### Audit Presence: [ ] YES / [ ] NO
### Task Type Match: [ ] YES / [ ] NO
### Preferred Selection: [ ] CORRECT / [ ] WRONG
### Status Evidence: [ ] PRESENT / [ ] MISSING
### Skip Rationale: [ ] VALID / [ ] INVALID
### Forbidden Usage: [ ] NONE / [ ] FOUND
### Fallback Chain: [ ] VALID / [ ] INVALID

### Decision: pass / needs_revision / blocked
```
