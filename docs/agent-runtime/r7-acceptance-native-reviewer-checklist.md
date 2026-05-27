# R7 Acceptance Native Reviewer Checklist -- RD2100 Agent Runtime v2

> Batch Y (R7), 2026-05-27
> 10-step review process for R7 acceptance native outputs.

## Step 1: Scope Check
- [ ] All R7 files exist in approved paths only
- [ ] No writes to scripts/, agent-workqueue/, templates/, runs/
- [ ] No existing acceptance-native files modified

## Step 2: Approved Outputs Check
- [ ] script-safety-record.schema.json: exists, parseable
- [ ] acceptance-script-registry.md: 7 scripts + 5 queues + 3 templates + runs covered
- [ ] workqueue-controlled-use-policy.md: tier semantics, consumption gate
- [ ] run-history-policy.md: historical only, metadata requirements
- [ ] r7-acceptance-native-negative-tests.md: >= 25 scenarios
- [ ] r7-acceptance-native-reviewer-checklist.md: this file

## Step 3: Changed Files Check
- [ ] git status shows only R7 approved outputs
- [ ] 13M + 6U baseline unchanged
- [ ] scripts/ files unchanged
- [ ] agent-workqueue/ files unchanged
- [ ] templates/ files unchanged
- [ ] runs/ files unchanged

## Step 4: Command Audit
- [ ] No PowerShell script execution
- [ ] No WorkQueue consumption
- [ ] No template modification
- [ ] No run history modification
- [ ] No -Real or -Apply flags used

## Step 5: Forbidden Action Check
- [ ] Any script executed? Must be NO
- [ ] Any WorkQueue consumed? Must be NO
- [ ] Any template overwritten? Must be NO
- [ ] Any run history modified? Must be NO
- [ ] Any historical run treated as current? Must be NO
- [ ] Any script output auto-signed as GateResult? Must be NO

## Step 6: Schema Parse Check
- [ ] script-safety-record.schema.json parses
- [ ] execution_status enum valid: not_run, human_required, forbidden
- [ ] allowed_to_run const=false enforced
- [ ] mutation_risk, network_risk, secret_risk all required
- [ ] human_gate_required required

## Step 7: Negative Test Coverage
- [ ] >= 25 negative tests total
- [ ] >= 12 hard stop (BLOCKED)
- [ ] 0 expected_gate_decision = pass
- [ ] Covers: script executed, queue consumed, template overwritten, run history modified, Tier 2 bypass, -Real flag, fake green, record falsification, pipeline execution, historical-as-current

## Step 8: Fake Green Check
- [ ] No script exit code mismatch (FAILED/BLOCKED != PASS)
- [ ] No historical run marked current
- [ ] No "dry-run" claim with actual file writes
- [ ] No execution_status falsification

## Step 9: Human Gate Check
- [ ] All scripts: human_gate_required=true
- [ ] All scripts: allowed_to_run=false
- [ ] All queues: human gate required for consumption
- [ ] All Tier 2 queues: escalation required

## Step 10: Gate Decision Tree

```
Was any script executed?                           -> YES = BLOCKED
Was any WorkQueue consumed?                        -> YES = BLOCKED
Was any template overwritten?                      -> YES = BLOCKED
Was any run history modified?                      -> YES = BLOCKED
Was historical run treated as current?             -> YES = needs_revision
Was script output auto-signed as GateResult?       -> YES = needs_revision
Was allowed_to_run not false?                      -> YES = needs_revision
Is mutation_risk/network_risk/secret_risk missing? -> YES = needs_revision
Was execution_status falsified?                    -> YES = BLOCKED
Was fake green detected?                           -> YES = BLOCKED
Are negative tests < 25?                           -> YES = needs_revision
All pass?                                           -> pass_to_review
```

## Decision: [ ] pass_to_review / [ ] needs_revision / [ ] blocked / [ ] human_required
