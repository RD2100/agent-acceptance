# Task-to-Capability Routing Matrix -- CR1

> Batch CR-A, 2026-05-27
> Maps 13 task types to preferred, fallback, and forbidden capabilities.

## Routing Rules

### 1. Structural Code Understanding
- **Task examples**: "how does X work", "what calls Y", "architecture of Z", "trace this flow"
- **Preferred**: CodeGraph (codegraph_context, codegraph_search)
- **Pre-check**: codegraph_status — verify files_indexed > 0, target_root matches, freshness != stale/unknown/empty
- **Fallback**: rg for symbol patterns + Read for relevant files
- **Forbidden**: CodeGraph without freshness check, CodeGraph overriding filesystem, large-scale grep as first choice
- **Evidence**: codegraph_status output or fallback reason

### 2. Literal String / Pattern Search
- **Task examples**: "find all files containing X", "search for pattern Y", "where is string Z used"
- **Preferred**: rg / Grep
- **Pre-check**: none (always available)
- **Fallback**: Select-String (PowerShell)
- **Forbidden**: CodeGraph (wrong tool for literal search)
- **Evidence**: command + match count

### 3. File Content Reading
- **Task examples**: "read file X", "show me the contents of Y"
- **Preferred**: Read tool
- **Pre-check**: file not in secret list (.env, *.key, *.pem, token, credential)
- **Fallback**: Get-Content (PowerShell)
- **Forbidden**: reading secret files
- **Evidence**: file path + line range

### 4. Schema Validation
- **Task examples**: "validate schema X", "check JSON structure", "audit schemas"
- **Preferred**: ConvertFrom-Json (PowerShell) + schema docs
- **Pre-check**: file exists, file is valid JSON
- **Fallback**: manual structural review
- **Forbidden**: executing custom validation scripts without approval
- **Evidence**: parse result + any enum/constraint violations

### 5. Documentation / Policy Lookup
- **Task examples**: "what is the policy for X", "find the contract for Y", "what phase allows Z"
- **Preferred**: Runtime Docs + rg for specific sections
- **Pre-check**: doc exists (test -f)
- **Fallback**: Read + manual search
- **Forbidden**: memory as fact for current policy, CodeGraph for doc search
- **Evidence**: doc path + section reference

### 6. Rule / Gate Enforcement
- **Task examples**: "check if this violates any rule", "what gate applies", "is this P0 or P1"
- **Preferred**: Runtime Rules + verification-gates.md
- **Pre-check**: rule file exists
- **Fallback**: docs search for gate definitions
- **Forbidden**: memory as rule source, self-approving gates
- **Evidence**: rule ID + file reference + gate decision

### 7. Negative Test Reference
- **Task examples**: "what negative tests cover X", "find NEG scenarios for capability Y"
- **Preferred**: Negative Tests files (r0- through r7- negative tests)
- **Pre-check**: test file exists
- **Fallback**: N/A
- **Forbidden**: executing negative tests as actual tests
- **Evidence**: test ID + expected_gate_decision

### 8. Blackboard / Shared State
- **Task examples**: "check Blackboard state", "verify session registration"
- **Preferred**: N/A (R1-SNAPSHOT-MCP not authorized)
- **Pre-check**: R1 policy docs
- **Fallback**: filesystem snapshot (Test-Path, Get-FileHash on state.json)
- **Forbidden**: any bb_* call, server.py execution, MCP registration, state mutation
- **Evidence**: R1 policy reference + filesystem checks

### 9. test-frame Evidence
- **Task examples**: "use test-frame for validation", "check test results"
- **Preferred**: R2 policy docs (historical evidence only)
- **Pre-check**: D:\test-frame exists
- **Fallback**: historical reports directory listing
- **Forbidden**: aggregator execution, attribution execution, CLI execution, test execution, producing GateResult
- **Evidence**: R2 doc reference + directory listing

### 10. dev-frame Orchestration
- **Task examples**: "check dev-frame health", "validate orchestration"
- **Preferred**: R3 policy docs + historical smoke_report.txt
- **Pre-check**: D:\dev-frame exists
- **Fallback**: directory listing
- **Forbidden**: smoke_test.py execution, ai-workflow-hub execution, ai-workflow-hub-e2e execution, producing GateResult
- **Evidence**: R3 doc reference + smoke_report.txt timestamp

### 11. Local Skill Judgment
- **Task examples**: "should I use skill X", "is skill Y safe"
- **Preferred**: R5 intake docs + skill-trigger-matrix.md
- **Pre-check**: skill listed in R5 classification
- **Fallback**: skill manifest (system prompt)
- **Forbidden**: executing skill, auto-loading skill, skill-installer
- **Evidence**: R5 doc reference + skill classification

### 12. Memory Reference
- **Task examples**: "what does memory say about X", "check historical context"
- **Preferred**: R6 policy docs (read-only reference)
- **Pre-check**: memory file exists, stale_risk assessed
- **Fallback**: filesystem/git verification
- **Forbidden**: used_as_fact, memory write, bb_solidify_knowledge
- **Evidence**: R6 doc reference + stale_risk + conflict_check

### 13. Scripts / WorkQueue
- **Task examples**: "run smoke test", "process work queue"
- **Preferred**: N/A (not authorized for execution)
- **Pre-check**: R7 policy docs, ScriptSafetyRecord exists
- **Fallback**: N/A
- **Forbidden**: script execution without ScriptSafetyRecord + human gate, queue consumption
- **Evidence**: R7 doc reference + ScriptSafetyRecord (if applicable)

## Routing Summary Table

| # | Task Type | Preferred | Pre-check | Fallback | Forbidden |
|---|-----------|-----------|-----------|----------|-----------|
| 1 | Code structure | CodeGraph | status + freshness | rg + Read | CodeGraph w/o freshness |
| 2 | String search | rg/Grep | none | Select-String | CodeGraph for literal |
| 3 | File read | Read | no secrets | Get-Content | read secrets |
| 4 | Schema validation | ConvertFrom-Json | file exists + JSON | manual review | custom script |
| 5 | Doc/policy lookup | Runtime Docs + rg | doc exists | Read + search | memory as fact |
| 6 | Rule enforcement | Rules + gates | rule exists | doc search | self-approval |
| 7 | Negative tests | Negative test files | file exists | N/A | execute tests |
| 8 | Blackboard | N/A (not authorized) | R1 policy | FS snapshot | bb_* calls |
| 9 | test-frame | R2 policy docs | path exists | dir listing | execute tools |
| 10 | dev-frame | R3 policy + smoke report | path exists | dir listing | execute smoke_test.py |
| 11 | Local skill | R5 intake + matrix | skill listed | manifest | execute/load |
| 12 | Memory | R6 policy docs | file + risk check | filesystem/git | used_as_fact |
| 13 | Scripts/Queue | N/A (not authorized) | R7 policy + SSR | N/A | execute/consume |
