# Self-Evolution Quarantine Policy -- R5

> Batch Y (R5), 2026-05-27
> Governs self-evolution and memory-writing skills. Default: quarantine. No auto-evolution.

## 1. Quarantined Skills

The following skills are quarantined by default in R5:

| Skill | Risk | Reason | Quarantine Condition |
|-------|:---:|--------|---------------------|
| skill-auto-evolve | high | GEPA self-evolution; mutates skill definitions | Requires agent-state.db write approval |
| skill-evolver | high | Manages mutation/evaluation/selection lifecycle | Requires agent-state.db write approval |
| recursive-improve | high | May attempt to write rules or memory files | Requires memory write approval |
| dream-reflection | high | Cross-session pattern detection; may trigger writes | Requires memory write approval |
| skill-usage-tracker | medium | Records skill usage to agent-state.db | Requires agent-state.db write approval |

## 2. Quarantine Conditions

A quarantined skill may ONLY move from `defer` to `candidate` when:

1. The specific write operation it performs is explicitly approved for the current phase
2. A ScriptSafetyRecord is defined for the skill execution
3. Reviewer explicitly authorizes the skill evaluation
4. No auto-trigger is enabled -- all triggers are manual or reviewer-initiated

## 3. Self-Evolution Lock

The self-evolution loop described in `self-evolution.md` (global Claude rule) is **suspended** in Phase 0-5 and R0-R7 design phases:

- Task summary: permitted (documentation only)
- Recursive reflection: **deferred** (may trigger rule/memory writes)
- Memory write: **forbidden** (Phase 0-5 memory freeze)
- Skill evolution check: **deferred** (requires agent-state.db)
- Memory audit row: **deferred** (requires memory write)

## 4. What IS Permitted (R5)

- Classifying self-evolution skills as `defer`
- Documenting quarantine conditions
- Defining ScriptSafetyRecord templates for future evaluation
- Including self-evolution skills in negative test scenarios

## 5. What IS NOT Permitted (R5)

- Executing any quarantined skill
- Auto-evolving any skill definition
- Auto-writing memory based on task outcomes
- Recording skill execution results to agent-state.db
- Triggering recursive-improve or dream-reflection

## 6. Future Unlock Path

Self-evolution capabilities may be unlocked in future phases ONLY after:

1. Phase 0-5 memory freeze is lifted (separate reviewer decision)
2. agent-state.db write policy is defined and approved
4. Each skill passes quarantine review individually
5. ScriptSafetyRecord exists for each skill
6. Human gate is established for each execution
