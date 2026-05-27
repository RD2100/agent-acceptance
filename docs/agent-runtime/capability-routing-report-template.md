# Capability Routing Report Template -- CR2

> Batch CR-A, 2026-05-27
> Template for the capability routing section of ExecutionReports.

## Mandatory Section

Every ExecutionReport MUST include the following section verbatim (with values filled in):

```markdown
## Capability Routing Audit

### Pre-Task Declaration

- **Primary Task Type**: <from routing matrix>
- **Expected Capability**: <preferred capability>
- **Status Check**: <command run to check status>
- **Status Result**: <available/stale/empty/forbidden/unavailable>
- **Fallback (if needed)**: <fallback or N/A>
- **Skip Reason (if needed)**: <reason or N/A>

### Forbidden Capabilities Verified

| Capability | Reason Forbidden | Confirmed Not Used? |
|---|---|---|
| <name> | <reason> | yes |

### Routing Table

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| <type> | <preferred> | <status> | yes/no | <reason or N/A> | <fallback or N/A> | <evidence> |

### Capability Skip Log (if any)

CAPABILITY SKIPPED: <capability_name>
REASON: <stale/empty/forbidden/unavailable>
EVIDENCE: <status check output>
FALLBACK: <fallback capability used>
```

## Example: Single Task (CodeGraph empty, using fallback)

```markdown
## Capability Routing Audit

### Pre-Task Declaration

- **Primary Task Type**: code_structure
- **Expected Capability**: CodeGraph
- **Status Check**: codegraph_status
- **Status Result**: empty (agent-acceptance: 0 files indexed)
- **Fallback**: rg + Read
- **Skip Reason**: agent-acceptance CodeGraph index empty (0 files); trusted_for_current_run=false per R4 policy

### Forbidden Capabilities Verified

| Capability | Reason Forbidden | Confirmed Not Used? |
|---|---|---|
| Blackboard MCP | R1-SNAPSHOT-MCP not authorized | yes |
| Scripts | R7 scripts not_run | yes |
| Memory write | R6 write_allowed=false | yes |

### Routing Table

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| code_structure | CodeGraph | empty | no | agent-acceptance index empty (0 files) | rg + Read | codegraph_status output |
```

## Example: Multi-Area Task

```markdown
## Capability Routing Audit

### Routing Table

| Task Area | Expected Capability | Status | Used? | Reason If Not Used | Fallback | Evidence |
|---|---|---|---|---|---|---|
| doc_policy | Runtime Docs + rg | available | yes | N/A | N/A | docs/ path reference |
| string_search | rg | available | yes | N/A | N/A | rg output |
| file_read | Read | available | yes | N/A | N/A | file path |
```

## Audit Completeness Checklist

Before submitting ExecutionReport, verify:

- [ ] Capability Routing Audit section present
- [ ] Primary task type declared
- [ ] Status check performed and evidenced
- [ ] Routing table has at least 1 row
- [ ] All Used?=no rows have Reason If Not Used filled
- [ ] All Used?=no rows have Fallback filled (or N/A if no fallback)
- [ ] Evidence column populated for all rows
- [ ] Forbidden capabilities table present
- [ ] No forbidden capability marked Used?=yes
