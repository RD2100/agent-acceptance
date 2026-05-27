# Run History Policy -- R7

> Batch Y (R7), 2026-05-27
> Governs historical run artifacts. All runs are historical evidence only.

## 1. Run History Status

The `runs/` directory contains historical execution artifacts. These are records of past agent-acceptance script executions. They have NOT been produced in the current Runtime v2 session.

## 2. Historical Evidence Only

All files in `runs/` are classified as:
- `historical`: produced before or outside current Runtime v2 session
- `stale_or_unknown`: freshness cannot be verified within current session
- `read_only`: no modification permitted

## 3. What Historical Runs CAN Be Used For

- Reference for understanding script output format
- Context for what tasks were previously executed
- Evidence that a capability existed at a point in time

## 4. What Historical Runs CANNOT Be Used For

- Current pass/fail determination (NOT a GateResult)
- Claiming "the system is currently passing"
- Substituting for an approved current run
- EvidenceIndex entries marked as "current" or "verified"
- Justifying skipping a current validation

## 5. Required Metadata

Any reference to a historical run must include:
- `run_id` or path identifier
- `timestamp` (when was it produced)
- `source` (which script produced it)
- `freshness` (must be `stale_or_unknown`)
- `reviewer_annotation` (required before use in any gate)

## 6. Run History Integrity

- Run history files must not be modified
- Run history files must not be deleted
- New run history can only be created by approved script execution (future phase)
- Historical runs must not be mixed with current runs in the same EvidenceIndex entry

## 7. Forbidden Actions

- Modify any file in runs/
- Delete any file in runs/
- Treat historical run as current pass
- Use historical run to skip current validation
- Overwrite historical run with new data
- Claim "verified" status for historical run without reviewer approval
