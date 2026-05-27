# Capability Fallback Policy -- CR1

> Batch CR-A, 2026-05-27
> Defines fallback rules when preferred capabilities cannot be used.

## Fallback Chain

For each capability, the fallback chain is ordered by preference:

| Preferred | Fallback 1 | Fallback 2 | Never Fallback To |
|-----------|------------|------------|-------------------|
| CodeGraph | rg + Read | Grep (bash) | memory, stale CodeGraph without freshness |
| rg/Grep | Select-String | manual Read | CodeGraph (wrong tool type) |
| Read | Get-Content | N/A | read secrets |
| ConvertFrom-Json | manual structural review | N/A | custom script execution |
| Runtime Docs + rg | Read + manual search | N/A | memory as current policy |
| Rules + gates | docs search | N/A | self-approval, memory as rule |
| Negative Tests | N/A | N/A | execute as actual tests |
| Blackboard (N/A) | FS snapshot | N/A | bb_* calls, server.py |
| test-frame (R2 docs) | directory listing | N/A | aggregator/attribution/CLI execution |
| dev-frame (R3 docs) | smoke_report.txt (historical) | directory listing | smoke_test.py execution |
| Local Skills (R5 docs) | skill manifest (system prompt) | N/A | execution, auto-load |
| Memory (R6 docs) | filesystem/git verification | N/A | used_as_fact, memory write |
| Scripts (N/A) | N/A | N/A | execution without gate |

## Fallback Rules

### Rule F1: Stale Capability -> Fallback
If preferred capability exists but freshness is stale/unknown, use fallback. Do NOT attempt to use the stale capability and "mark it as best-effort".

### Rule F2: Empty Capability -> Fallback
If preferred capability exists but has no usable data (e.g., CodeGraph with 0 files indexed), use fallback. Do NOT reindex without approval.

### Rule F3: Forbidden Capability -> Fallback
If preferred capability is forbidden in the current phase, use its fallback. Do NOT attempt to "temporarily use" the forbidden capability.

### Rule F4: Unavailable Capability -> Fallback
If preferred capability tool is not present or not accessible, use fallback. Record as verification_gap.

### Rule F5: Fallback Must Be Permitted
The fallback capability must be permitted in the current phase. If the fallback is also forbidden, escalate to human_required.

### Rule F6: Explain Every Skip
Every capability skip (preferred not used) must be logged with reason and evidence. "Skipped because faster" is not a valid reason if the preferred capability is available.

### Rule F7: No Capability Stacking
Do not use multiple capabilities sequentially "just to be safe". Use the preferred if available, or exactly one fallback. Stacking increases risk without improving correctness.

## Examples

### Example 1: Code Structure Task, CodeGraph Available
```
Task: "Explain how Run-WorkQueue.ps1 dispatches tasks"
Preferred: CodeGraph
Status: codegraph_status shows dev-frame 410 files, freshness=current
Decision: Use CodeGraph
Audit: CodeGraph | available | yes | N/A | N/A
```

### Example 2: Code Structure Task, CodeGraph Empty
```
Task: "How does AGENTS.md reference rules?"
Preferred: CodeGraph (agent-acceptance index)
Status: codegraph_status shows agent-acceptance 0 files
Decision: Skip CodeGraph, use fallback
Reason: empty (0 files indexed)
Audit: CodeGraph | empty | no | index empty, 0 files | rg + Read
```

### Example 3: Blackboard Task
```
Task: "Check current Blackboard session state"
Preferred: N/A (Blackboard MCP not authorized)
Status: R1-SNAPSHOT-MCP not authorized
Decision: Use filesystem snapshot fallback
Reason: forbidden (R1-SNAPSHOT-MCP not authorized)
Audit: N/A | forbidden | no | R1-SNAPSHOT-MCP not authorized | FS snapshot
```
