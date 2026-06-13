# Open Required Tabs

Current CDP is alive, but the two bound pilot conversations are not visible in
the Chrome target list. Open these exact URLs in the shared Chrome instance:

1. Reviewer binding:
   `https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959`

2. Executor binding:
   `https://chatgpt.com/c/6a28d545-f918-83a5-b122-dc1503386374`

Do not substitute the existing review conversation
`https://chatgpt.com/c/6a297f76-3e7c-83a5-a0e5-b4413d923c7e`.

Do not use the paper conversation
`https://chatgpt.com/c/6a297e5f-c9c8-83a8-b413-a8fc414e0e85`.

After both tabs are open, rerun:

```powershell
python scripts\tab_target_resolver.py --project agent-acceptance
python scripts\multi_agent_gate0_preflight.py --output _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json
python scripts\multi_agent_dispatch_plan.py --preflight _reports\multi-agent-gate0-preflight-a1\PREFLIGHT_CURRENT.json --output _reports\multi-agent-dispatch-plan-a1\DISPATCH_PLAN_CURRENT.json
```

Expected intermediate result before live pilot:

- CDP target resolver has an exact match for both bound conversations.
- Gate 0 is still HUMAN_REQUIRED until run-bound authorization and session
  evidence are written.
- After authorization/session evidence exists, Gate 0 can become PASS and
  dispatch can become READY.
