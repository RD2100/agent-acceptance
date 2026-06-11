verdict: FAILED

changed files:
- D:\agent-acceptance\_reports\multi-agent-quality-review-a1\QUALITY_REVIEW.md

critical paths:
- D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py
- D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py
- D:\agent-acceptance\scripts\cross_repo_authorization.py
- D:\agent-acceptance\scripts\cross_repo_verify.py
- D:\agent-acceptance\scripts\multi_repo_smoke.py
- D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py
- D:\agent-acceptance\tests\test_multi_agent_dispatch_plan.py
- D:\agent-acceptance\tests\test_cross_repo_execution_guards.py
- D:\agent-acceptance\tests\test_smoke_suite.py
- D:\agent-acceptance\schemas\agent-runtime\multi-agent-gate0-preflight.schema.json
- D:\agent-acceptance\schemas\agent-runtime\multi-agent-dispatch-plan.schema.json

tests run:
- read-only inspection only, per task instruction not to execute external runtime, cross-repo pytest/smoke, live CDP, opencode, or paper workflow.
- Inspected exact required paths:
  - D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py
  - D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py
  - D:\agent-acceptance\scripts\cross_repo_authorization.py
  - D:\agent-acceptance\scripts\cross_repo_verify.py
  - D:\agent-acceptance\scripts\multi_repo_smoke.py
  - D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py
  - D:\agent-acceptance\tests\test_multi_agent_dispatch_plan.py
  - D:\agent-acceptance\tests\test_cross_repo_execution_guards.py
  - D:\agent-acceptance\tests\test_smoke_suite.py
  - D:\agent-acceptance\schemas\agent-runtime\multi-agent-gate0-preflight.schema.json
  - D:\agent-acceptance\schemas\agent-runtime\multi-agent-dispatch-plan.schema.json

output summary:
- P0 findings: none found in read-only inspection.
- P1 finding (blocking): D:\agent-acceptance\scripts\multi_repo_smoke.py:23 and D:\agent-acceptance\scripts\multi_repo_smoke.py:86-99 can convert any non-zero exit from `devframe-control-plane` into `KNOWN_ISSUES`, then return process exit 0 with overall `PASS`. Because the code does not verify expected failure count, known failure signatures, timeout category, or stderr class, a new regression or environment failure in that repo can be hidden as green once execution is human-authorized. This is fake-green resistant enough to block release.
- P2 finding: D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:42-49 and D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:406-417 implement directory/file overlap detection, but D:\agent-acceptance\tests\test_multi_agent_dispatch_plan.py:74-90 only tests identical file conflicts. Directory-vs-file and parent-directory write collisions are not directly locked by regression tests.
- P2 finding: D:\agent-acceptance\scripts\cross_repo_verify.py:84-92 and D:\agent-acceptance\scripts\multi_repo_smoke.py:77-85 do not catch subprocess timeout, missing cwd, or execution exceptions into structured JSON. This fails closed by exception, but leaves weak governance evidence and makes failure classification noisy.
- P3 finding: D:\agent-acceptance\scripts\run_demo.py:25-35, checked through D:\agent-acceptance\tests\test_smoke_suite.py:60-69, always builds a presence-only command that exits 0 even when the external path is absent. The output text says `executed=false`, but demo-level summaries can still read as all-pass for a missing presence check.
- HUMAN_REQUIRED as PASS check: D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py:250-258 maps `human_required` checks to overall `HUMAN_REQUIRED` and exit 2; D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:461-465 maps source preflight human gate to plan `HUMAN_REQUIRED`; D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:511-515 exits 2 for that status. No direct HUMAN_REQUIRED-to-PASS path found.
- Presence-only / dispatch-plan execution check: D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py:260-266 and D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:469-476 set `executed_external_runtime` false; schemas at D:\agent-acceptance\schemas\agent-runtime\multi-agent-gate0-preflight.schema.json:19-22 and D:\agent-acceptance\schemas\agent-runtime\multi-agent-dispatch-plan.schema.json:29-32 require false. Presence-only helpers also emit `executed: False`.
- `--output` exit-code check: D:\agent-acceptance\scripts\multi_agent_gate0_preflight.py:299-304 and D:\agent-acceptance\scripts\multi_agent_dispatch_plan.py:504-515 write output then preserve status-based exits. Tests at D:\agent-acceptance\tests\test_multi_agent_gate0_preflight.py:82-104 and D:\agent-acceptance\tests\test_multi_agent_dispatch_plan.py:93-117 assert return code 2 and file/stdout equivalence for current HUMAN_REQUIRED state.
- Authorization check: D:\agent-acceptance\scripts\cross_repo_authorization.py:71-126 requires audit fields, exact scope, exact repo set, risk acknowledgement, timezone timestamps, expiry after approval, and non-expired records. Tests cover legacy `authorized=true`, UTF-8 BOM legacy, expired authorization, and unknown repo rejection.

artifacts:
- D:\agent-acceptance\_reports\multi-agent-quality-review-a1\QUALITY_REVIEW.md

known gaps:
- No pytest, smoke, cross-repo execution, opencode, live CDP, or paper workflow was run by instruction.
- Review did not inspect secrets or real paper content.
- The blocking P1 requires implementation/test follow-up before this readiness layer should be reported as pass.

technical debt introduced:
- None. This worker only created the quality review report.

governance notes:
- No git operation was performed.
- No forbidden paths were modified.
- No external runtime was executed.
- Verdict is FAILED because open P1 finding blocks under the dispatch plan quality standard.

suggested review focus:
- First review D:\agent-acceptance\scripts\multi_repo_smoke.py known-failure handling and require bounded known-failure matching before any overall PASS.
- Then review dispatch conflict regression coverage for directory/file overlaps.
- Finally review structured exception handling for authorized subprocess execution paths.

suggested next task:
- Fix `multi_repo_smoke.py` so `KNOWN_ISSUES` cannot produce overall PASS unless the actual failure matches an explicit expected count/signature, and add tests for unexpected non-zero, timeout/missing cwd classification, and directory/file write conflicts.
