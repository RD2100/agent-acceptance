# R5 Local Skill Reviewer Checklist -- RD2100 Agent Runtime v2

> Batch Y (R5), 2026-05-27
> 10-step review process for R5 local skill intake outputs.

## Step 1: Scope Check
- [ ] All R5 files exist in approved paths only
- [ ] No writes to skills-inbox/, .claude/skills/, or C:\Users\RD
- [ ] No existing skill files modified

## Step 2: Approved Outputs Check
- [ ] local-skill-intake-record.schema.json: exists, parseable
- [ ] local-skill-intake.md: complete classification coverage
- [ ] rule-dedup-map.md: overlaps/conflicts/gaps documented
- [ ] self-evolution-quarantine-policy.md: quarantine conditions defined
- [ ] r5-local-skill-negative-tests.md: >= 25 scenarios
- [ ] r5-local-skill-reviewer-checklist.md: this file

## Step 3: Changed Files Check
- [ ] git status shows only R5 approved outputs
- [ ] 13M + 6U baseline unchanged
- [ ] No C:\Users\RD writes

## Step 4: Command Audit
- [ ] No skill execution commands in logs
- [ ] No skill-installer, skill-evolver, skill-creator invocation
- [ ] No recursive-improve, dream-reflection, memory-bridge execution
- [ ] No connect-apps, update-config, setup-pre-commit

## Step 5: Forbidden Action Check
- [ ] Any skill executed? Must be NO
- [ ] Any skill auto-loaded? Must be NO
- [ ] Any rules copied into AGENTS.md? Must be NO
- [ ] Any self-evolution enabled? Must be NO
- [ ] Any MCP/hook/package/reindex? Must be NO

## Step 6: Schema Parse Check
- [ ] local-skill-intake-record.schema.json parses
- [ ] decision enum excludes approved/installed/enabled
- [ ] auto_trigger_allowed const=false enforced
- [ ] execution_allowed const=false enforced
- [ ] install_allowed const=false enforced

## Step 7: Negative Test Coverage
- [ ] >= 25 negative tests total
- [ ] >= 12 hard stop (BLOCKED)
- [ ] 0 expected_gate_decision = pass
- [ ] Covers: skill executed, auto-loaded, skill-evolver, recursive-improve, rules copied to AGENTS.md, connect-apps, update-config, blackboard-knowledge-loop, decision=approved, memory write

## Step 8: Fake Green Check
- [ ] No unknown classification marked pass
- [ ] No missing risk_level marked verified
- [ ] No schema validation failure reported as pass
- [ ] No decision=approved hidden in any record

## Step 9: Human Gate Check
- [ ] All high/critical skills: human_gate_required=true
- [ ] Self-evolution skills: all deferred with quarantine conditions
- [ ] External integration skills: all rejected
- [ ] UI/desktop skills: all rejected

## Step 10: Gate Decision Tree

```
Was any skill executed?                         -> YES = BLOCKED
Was any skill auto-loaded?                      -> YES = BLOCKED
Was skill-installer / skill-evolver executed?   -> YES = BLOCKED
Was recursive-improve / dream-reflection run?   -> YES = BLOCKED
Were rules copied into AGENTS.md?              -> YES = needs_revision
Was decision=approved used?                     -> YES = needs_revision
Was auto_trigger_allowed not false?             -> YES = needs_revision
Is high/critical skill missing human gate?      -> YES = needs_revision
Are negative tests < 25?                        -> YES = needs_revision
Is any negative test expected pass?             -> YES = needs_revision
All pass?                                        -> pass_to_review
```

## Decision: [ ] pass_to_review / [ ] needs_revision / [ ] blocked / [ ] human_required
