# Smoke Validation Policy -- R3

> Batch X (R3), 2026-05-27
> Governs smoke_test.py and smoke_report.txt in the dev-frame adapter context.

## 1. smoke_test.py is Forbidden by Default

`D:\dev-frame\smoke_test.py` must not be executed in R3. The script performs cross-project verification (CodeGraph type-check, ai-workflow-hub state machine tests, ai-workflow-hub-e2e evidence integrity tests). Running it would execute tests in three projects -- all of which are forbidden in R3 and would violate R2 boundaries.

## 2. smoke_report.txt is Historical Evidence Only

The existing `smoke_report.txt` (2026-05-27, 3/3 PASS) is a historical artifact. It captures the state of dev-frame at that moment. It has NOT been regenerated in the current Runtime v2 session.

## 3. smoke_report Must Never Be Treated as Current Pass

- The report timestamp (2026-05-27) is the authoritative freshness indicator
- It CANNOT be used to claim "dev-frame smoke validation passed today"
- It CAN be referenced as "historical smoke validation: 3/3 PASS on 2026-05-27"

## 4. Running smoke_test.py Requires ScriptSafetyRecord

Before smoke_test.py can be executed in any future phase:

```json
{
  "record_id": "SSR-smoke-test-001",
  "script_path": "D:\\dev-frame\\smoke_test.py",
  "script_description": "Cross-project smoke validation: CodeGraph type-check, ai-workflow-hub tests, ai-workflow-hub-e2e tests",
  "expected_side_effects": [
    "Writes smoke_report.txt to D:\\dev-frame\\",
    "Executes npx tsc --noEmit in codegraph/",
    "Executes pytest in ai-workflow-hub/",
    "Executes pytest in ai-workflow-hub-e2e/"
  ],
  "timeout_seconds": 300,
  "rollback": "Delete generated smoke_report.txt; no other state modified",
  "human_gate_required": true,
  "preconditions": [
    "R3 exit gate passed",
    "R4 CodeGraph stale-aware policy active",
    "Reviewer explicitly approves smoke validation run"
  ]
}
```

## 5. Running smoke_test.py Requires Human Gate

Even with ScriptSafetyRecord, execution requires:
1. Reviewer explicitly approves the smoke validation run
2. Approval is per-run (not blanket)
3. Approval scope is limited to smoke_test.py only (not arbitrary scripts)
4. Pre/post git status required

## 6. Pre-Run: Expected Side Effects Must Be Documented

Before execution:
- List all files that will be written
- List all commands that will run
- List all directories that will be accessed
- Document expected runtime

## 7. Post-Run: EvidenceIndex Required

After execution:
- EvidenceIndex must record: run_id, timestamp, exit_code, output_summary
- smoke_report.txt checksum recorded
- Any unexpected output flagged
- Any deviation from expected side effects flagged

## 8. Failure Must Never Be Fake Green

The exit code contract applies:
- Exit 0 = PASS
- Exit non-zero = FAILED or BLOCKED
- FAILED/BLOCKED must not be reported as PASS
- If smoke_test.py cannot run (missing deps), report BLOCKED, not SKIPPED

## 9. Smoke Validation Result Must Not Auto-Advance GateResult

- Smoke validation result is EvidenceIndex input
- Reviewer evaluates the evidence and produces GateResult
- Smoke validation does NOT automatically produce PASS/FAIL for any gate

## 10. Smoke Validation Must Not Modify dev-frame

Beyond generating smoke_report.txt (documented expected side effect), smoke_test.py must not:
- Modify any source file in dev-frame
- Modify any configuration
- Install or update dependencies
- Change git state
