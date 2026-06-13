# Next Commands

The controlled pilot now has two current live ChatGPT session bindings.
The only remaining Gate 0 blocker is run-bound human authorization.

## 1. Record Human Authorization

Template:

```powershell
Get-Content _reports\controlled-multi-gpt-pilot-a1\HUMAN_AUTHORIZATION_TEMPLATE.json
```

The template is intentionally `authorized=false`. A human operator must create
`_reports\controlled-multi-gpt-pilot-a1\HUMAN_AUTHORIZATION.json` with
`authorized=true`, the same run_id, a current timestamp, a future expiry, and
risk acknowledgement.

Exact authorization sentence:

```text
I authorize CONTROLLED-MULTI-GPT-PILOT-A1 for run_id controlled-multi-gpt-pilot-a1-20260613T061555Z, limited to updating the activation authorization record, regenerating Gate0/dispatch evidence, and running the controlled pilot within the listed write_set. I acknowledge the external-runtime and evidence-chain risks.
```

## 2. Update Activation Authorization

After the authorization JSON exists, update
`_reports\multi-agent-multi-gpt-pilot-a1\ACTIVATION_RECORD.json` so
`authorization.evidence_file` points to it and the authorization fields match.

Required activation fields:

- `authorization.authorized=true`
- `authorization.authorizing_task=CONTROLLED-MULTI-GPT-PILOT-A1`
- `authorization.exact_command` includes `controlled-multi-gpt-pilot-a1-20260613T061555Z`
- `authorization.expected_write_set` is non-empty
- `authorization.evidence_file=_reports/controlled-multi-gpt-pilot-a1/HUMAN_AUTHORIZATION.json`
- `authorization.risk_acknowledged=true`

## 3. Rerun Gate 0

```powershell
python scripts\multi_agent_gate0_preflight.py --output _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json
```

Required outcome: `overall=PASS`.

## 4. Rebuild Dispatch Plan

```powershell
python scripts\multi_agent_dispatch_plan.py --preflight _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json --output _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json
python scripts\validate_multi_agent_dispatch_plan.py _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json
```

Required outcome: dispatch plan `status=READY`.

## 5. Controlled Pilot Readiness Gate

```powershell
python scripts\production_readiness_gate.py --mode controlled_pilot --local-evidence _reports\production-readiness-automation-a1\LOCAL_VERIFICATION.json --preflight _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json --dispatch-plan _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json
```

Required outcome: exit code `0`, status `READY`.

This does not authorize formal production promotion or paper workflow execution.
