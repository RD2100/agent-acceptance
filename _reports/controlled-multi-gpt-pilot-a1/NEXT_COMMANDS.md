# Next Commands

These commands are local governance checks only unless a later step explicitly
states that human authorization has been recorded.

## 1. Recheck CDP target resolution

```powershell
python scripts\tab_target_resolver.py --project agent-acceptance
```

Required outcome: `match_status` must be `exact_match` for the active binding.

## 2. Recheck Gate 0

```powershell
python scripts\multi_agent_gate0_preflight.py --output _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json
```

Required outcome before dispatch: `overall` must be `PASS`.

If it remains `HUMAN_REQUIRED`, inspect the `run_authorization`,
`live_agent_sessions`, and `independent_session_ids` checks.

## 3. Rebuild dispatch plan

```powershell
python scripts\multi_agent_dispatch_plan.py --preflight _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json --output _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json
python scripts\validate_multi_agent_dispatch_plan.py _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json
```

Required outcome before controlled pilot: `status=READY`,
`human_gate_required=false`, and `executed_external_runtime=false`.

## 4. Controlled pilot readiness gate

```powershell
python scripts\production_readiness_gate.py --mode controlled_pilot --local-evidence _reports\production-readiness-automation-a1\LOCAL_VERIFICATION.json --preflight _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json --dispatch-plan _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json
```

Required outcome: exit code `0`, status `READY`.

## 5. Human authorization text

Use this exact sentence if approving the next live controlled-pilot step:

```text
I authorize CONTROLLED-MULTI-GPT-PILOT-A1 for run_id controlled-multi-gpt-pilot-a1-20260613T061555Z, limited to verifying the two bound ChatGPT sessions, regenerating activation/Gate0/dispatch evidence, and running the controlled pilot within the listed write_set. I acknowledge the external-runtime and evidence-chain risks.
```

This does not authorize formal production promotion or paper workflow execution.
