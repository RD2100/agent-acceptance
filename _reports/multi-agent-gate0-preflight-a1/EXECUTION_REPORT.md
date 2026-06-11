# Execution Report: multi-agent-gate0-preflight-a1

verdict: PASS

## Scope

Add a read-only Gate 0 preflight for the multi-agent / multi-GPT pilot.

This slice does not run `opencode`, `D:\dev-frame\ai-workflow-hub`, cross-repo pytest/smoke, live CDP, or paper workflow execution.

Follow-up update: the CLI now supports `--output <path>` so the preflight report can be written as a durable JSON evidence artifact while preserving stdout and exit-code semantics.

## Changed Files

- `scripts/multi_agent_gate0_preflight.py`
- `schemas/agent-runtime/multi-agent-gate0-preflight.schema.json`
- `schemas/agent-runtime/README.md`
- `tests/test_multi_agent_gate0_preflight.py`
- `tests/test_smoke_suite.py`
- `docs/MULTI_AGENT_MULTI_GPT_PILOT_PLAN.md`
- `_reports/multi-agent-gate0-preflight-a1/GATE0_PREFLIGHT.json`

## Critical Paths

- `multi_agent_gate0_preflight.evaluate_preflight(...)`
- `multi_agent_gate0_preflight._validate_bindings(...)`
- `multi_agent_gate0_preflight._validate_capability_inventory(...)`
- `multi_agent_gate0_preflight._validate_tool_policy(...)`

## Tests Run

```powershell
python -m pytest tests\test_multi_agent_gate0_preflight.py tests\test_conversation_registry.py tests\test_cross_repo_execution_guards.py tests\test_smoke_suite.py -q
```

Result: 76 passed.

```powershell
python -m compileall scripts\multi_agent_gate0_preflight.py scripts\validate_conversation_registry.py
```

Result: exit 0.

CLI probe:

```powershell
python scripts\multi_agent_gate0_preflight.py --output _reports\multi-agent-gate0-preflight-a1\GATE0_PREFLIGHT.json
```

Result: `LASTEXITCODE=2`, `overall=HUMAN_REQUIRED`, `executed_external_runtime=false`, `human_gate_required=true`.

Output check:

```powershell
python -c "import json; from pathlib import Path; p=Path(r'_reports\multi-agent-gate0-preflight-a1\GATE0_PREFLIGHT.json'); data=json.loads(p.read_text(encoding='utf-8')); print(data['overall'], data['executed_external_runtime'], data['human_gate_required'], data['agent_count'], len(data['checks']))"
```

Result: `HUMAN_REQUIRED False True 1 9`.

## Output Summary

The current repository is governed but not ready for real multi-agent pilot execution:

- root conversation binding validates;
- governed runtime scope is present;
- one local agent remains `pending_manual_binding`;
- pilot has fewer than two independently bound agents;
- CAP-029 is usable for Gate 0 but not execution (`status=proposed`, `usable_for_execution=false`);
- tool policy contains the required runtime and authorization gates.
- the preflight report validates against `schemas/agent-runtime/multi-agent-gate0-preflight.schema.json`.

## Artifacts

- `_reports/multi-agent-gate0-preflight-a1/EXECUTION_REPORT.md`
- `_reports/multi-agent-gate0-preflight-a1/GATE0_PREFLIGHT.json`

## Known Gaps

- No real independent GPT conversation binding is present for two agents.
- `dev-frame-opencode Dispatch` remains proposed and not executable.
- No external runtime execution was attempted.

## Technical Debt Introduced

None.

## Governance Notes

`HUMAN_REQUIRED` is the expected current result. It is not a failure and not permission to execute. It means the pilot needs manual binding and capability approval before execution.

## Suggested Review Focus

- Confirm the preflight cannot execute external runtimes.
- Confirm `HUMAN_REQUIRED` is emitted for pending bindings and non-executable CAP-029.
- Confirm synthetic complete two-agent fixtures pass while duplicate agent IDs and missing bindings block.
