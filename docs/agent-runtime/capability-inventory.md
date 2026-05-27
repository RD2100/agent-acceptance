# Capability Inventory -- CR0

> Batch CR-A, 2026-05-27
> 17 capabilities registered. All: auto_use_allowed=false, execution_allowed=false, mutation_allowed=false.

## 1. CodeGraph
- **Type**: code_intelligence
- **Access**: read_only
- **Risk**: high
- **Preferred for**: structural code understanding, symbol lookup, caller/callee analysis
- **Forbidden for**: literal string search, current fact without freshness check, overriding filesystem/git
- **Fallback**: rg, Read, Grep
- **Human gate**: yes (reindex)
- **Must explain if skipped**: yes
- **Evidence**: codegraph_status output, index_freshness, target_root match

## 2. rg / Grep / Read (filesystem search)
- **Type**: search
- **Access**: read_only
- **Risk**: low
- **Preferred for**: literal string search, pattern matching, file content reading
- **Forbidden for**: structural code understanding (use CodeGraph first), secret file reading
- **Fallback**: Select-String (PowerShell)
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: command output

## 3. PowerShell read-only commands
- **Type**: shell
- **Access**: read_only
- **Risk**: medium
- **Preferred for**: Test-Path, Get-Content, Get-FileHash, Measure-Object, Get-ChildItem
- **Forbidden for**: Set-Content, Remove-Item, Invoke-WebRequest, Start-Process, script execution
- **Fallback**: bash test/ls/wc
- **Human gate**: yes (any write command)
- **Must explain if skipped**: no
- **Evidence**: command output

## 4. JSON Schema Validation
- **Type**: validation
- **Access**: read_only
- **Risk**: low
- **Preferred for**: schema parse audit, JSON structure validation, enum constraint check
- **Forbidden for**: schema modification without approval
- **Fallback**: manual review
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: ConvertFrom-Json output, parse result

## 5. Runtime Docs
- **Type**: documentation
- **Access**: read_only
- **Risk**: low
- **Preferred for**: policy lookup, contract reference, gate definition, phase boundary check
- **Forbidden for**: current fact without cross-reference, overriding schemas
- **Fallback**: direct file read
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: doc path + section reference

## 6. Runtime Rules
- **Type**: rules
- **Access**: read_only
- **Risk**: low
- **Preferred for**: rule violation check, coding standard, security hard stop, review gate
- **Forbidden for**: overriding reviewer decision, auto-approving gates
- **Fallback**: docs search
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: rule ID + file reference

## 7. Negative Tests
- **Type**: testing
- **Access**: reference_only
- **Risk**: low
- **Preferred for**: validating reviewer checklists, gate enforcement testing
- **Forbidden for**: execution, substituting for actual tests
- **Fallback**: N/A
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: test ID + expected_gate_decision

## 8. Reviewer Playbooks
- **Type**: review
- **Access**: reference_only
- **Risk**: low
- **Preferred for**: reviewer decision-making, gate evaluation
- **Forbidden for**: auto-approving gates, skipping reviewer
- **Fallback**: verification-gates.md
- **Human gate**: no
- **Must explain if skipped**: no
- **Evidence**: playbook reference + decision path

## 9. Blackboard MCP
- **Type**: mcp
- **Access**: snapshot_only (R1-DESIGN), forbidden (R1-SNAPSHOT-MCP not authorized)
- **Risk**: critical
- **Preferred for**: N/A (not authorized in current phase)
- **Forbidden for**: bb_solidify_knowledge, bb_share_knowledge, bb_claim_file, bb_release_file, any mutating bb_* call, MCP registration, server.py execution
- **Fallback**: filesystem snapshot (R1-SNAPSHOT-FS)
- **Human gate**: yes (any bb_* call beyond R1-DESIGN permitted list)
- **Must explain if skipped**: no (not expected to be used)
- **Evidence**: R1 policy docs, state.json checksum

## 10. test-frame
- **Type**: evidence
- **Access**: read_only (docs + directory listing)
- **Risk**: high
- **Preferred for**: evidence provider candidate reference
- **Forbidden for**: aggregator execution, attribution execution, CLI execution, orchestrator execution, test execution, producing GateResult
- **Fallback**: historical evidence (reports/test-results directory listing)
- **Human gate**: yes (any execution)
- **Must explain if skipped**: no
- **Evidence**: R2 policy docs

## 11. dev-frame
- **Type**: orchestration
- **Access**: read_only (docs + directory listing)
- **Risk**: high
- **Preferred for**: orchestration adapter candidate reference
- **Forbidden for**: smoke_test.py execution, ai-workflow-hub execution, ai-workflow-hub-e2e execution, producing GateResult
- **Fallback**: historical smoke_report.txt
- **Human gate**: yes (any execution)
- **Must explain if skipped**: no
- **Evidence**: R3 policy docs

## 12. Local Skills
- **Type**: skill
- **Access**: reference_only
- **Risk**: high
- **Preferred for**: skill classification reference, R5 intake lookup
- **Forbidden for**: execution, auto-load, installation, skill-evolver, recursive-improve, skill-installer
- **Fallback**: N/A
- **Human gate**: yes (any skill execution)
- **Must explain if skipped**: no (not expected to be used)
- **Evidence**: R5 intake docs

## 13. RD2100 Memory
- **Type**: memory
- **Access**: read_only
- **Risk**: high
- **Preferred for**: context reference (read-only)
- **Forbidden for**: used_as_fact, memory write, bb_solidify_knowledge, agent-state.db write
- **Fallback**: filesystem/git verification
- **Human gate**: yes (any write)
- **Must explain if skipped**: no
- **Evidence**: R6 policy docs, stale_risk, conflict_check

## 14. WorkQueue
- **Type**: workqueue
- **Access**: read_only (inspect definitions)
- **Risk**: high
- **Preferred for**: queue definition reference
- **Forbidden for**: task dispatch, queue consumption, queue modification
- **Fallback**: N/A
- **Human gate**: yes (any consumption)
- **Must explain if skipped**: no
- **Evidence**: R7 policy docs

## 15. Scripts (PowerShell runners)
- **Type**: script
- **Access**: human_gated (not_run)
- **Risk**: high
- **Preferred for**: N/A (not authorized for execution)
- **Forbidden for**: execution without ScriptSafetyRecord + human gate, Run-AllQueues, Run-QueueGroup
- **Fallback**: N/A
- **Human gate**: yes (per-script, per-execution)
- **Must explain if skipped**: no
- **Evidence**: R7 ScriptSafetyRecord

## 16. Hooks Draft
- **Type**: hook
- **Access**: reference_only (audit-only draft)
- **Risk**: medium
- **Preferred for**: audit draft reference
- **Forbidden for**: registration, execution, blocking (exit 1), file modification
- **Fallback**: N/A
- **Human gate**: yes (any registration)
- **Must explain if skipped**: no
- **Evidence**: hook file + AUDIT-ONLY DRAFT header

## 17. Phase 6 SourceLock / Quarantine
- **Type**: source_lock
- **Access**: reference_only (design only)
- **Risk**: critical
- **Preferred for**: external skill intake planning reference
- **Forbidden for**: clone, install, execute, enable MCP, run external code
- **Fallback**: N/A
- **Human gate**: yes (clone, any Phase 6C action)
- **Must explain if skipped**: no
- **Evidence**: Phase 6 design docs, SourceLockRecord schema
