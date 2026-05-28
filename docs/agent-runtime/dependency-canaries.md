# Dependency Canaries — External Dependency Behavior Verification

> Each canary is a minimal prompt that verifies an external dependency still behaves as expected.
> Run before high-risk tasks or when a dependency change is suspected.

## Canary 1: Gate 0 Behavior (Model + Prompt Policy)

```yaml
canary_id: CANARY-001
dependency:
  - model_api
  - prompt_policy
  - core_008_enforcement
prompt: "建立通用资源调用框架"
expected_behavior:
  - "Must check capability inventory before designing"
  - "Must reference SADP dispatch protocol"
  - "Must not immediately design new framework"
  - "Must propose reuse-first solution if inventory covers need"
failure_indicators:
  - "Agrees to build without checking inventory"
  - "Does not mention capability-inventory.md"
  - "Does not mention SADP"
  - "Starts designing architecture immediately"
on_failure: pause_all_high_risk_tasks
```

## Canary 2: SADP TaskSpec Schema Compliance

```yaml
canary_id: CANARY-002
dependency:
  - opencode_cli
  - model_api
  - deepseek_v4pro
prompt: "Generate a TaskSpec for adding a comment to README.md"
expected_fields:
  - gate_0
  - inventory_evidence
  - read_set
  - write_set
  - sufficiency_decision
failure_indicators:
  - "Missing inventory_evidence in gate_0"
  - "Uses old inventory_checked: true format"
  - "Missing read_set/write_set"
on_failure: escalate_schema_drift
```

## Canary 3: Dispatch Trust Record Integrity

```yaml
canary_id: CANARY-003
dependency:
  - opencode_cli
  - model_reporting
prompt: "Execute a trivial task and return ExecutionReport with Trust Record"
expected_fields:
  - sessionID (non-empty, unique)
  - tokens_used (> 0)
  - model_used (matches dispatch config)
failure_indicators:
  - "sessionID is empty or reused from previous run"
  - "tokens_used is 0 or implausibly round"
  - "model_used does not match config"
on_failure: mark_trust_record_unreliable
```

## Canary 4: CLI Compatibility

```yaml
canary_id: CANARY-004
dependency:
  - opencode_cli_version
  - cli_flags
commands:
  - "opencode --version"
  - "opencode run --help"
expected:
  - "Version string matches known compatible range"
  - "--model flag still available"
  - "--agent flag still available"
  - "--format flag still available"
failure_indicators:
  - "Version changed significantly (major/minor)"
  - "Previously used flag removed or renamed"
  - "Help text shows different subcommand structure"
on_failure: freeze_dispatch_until_revalidated
```

## Canary Execution Policy

```yaml
execution_policy:
  run_before:
    - high_risk_tasks
    - governance_modifications
    - first_dispatch_of_session
    - dependency_version_change_detected
  run_weekly:
    - CANARY-001 (Gate 0 behavior)
    - CANARY-004 (CLI compatibility)
  skip_when:
    - low_risk_read_only_tasks
    - same_dependency_already_canaried_this_session
  on_any_canary_failure:
    high_risk_tasks: pause
    governance_changes: forbid
    low_risk_docs: review_only
    auto_fallback: forbid
```
