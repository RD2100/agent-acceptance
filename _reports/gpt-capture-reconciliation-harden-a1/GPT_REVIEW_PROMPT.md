# GPT Review Prompt — GPT-CAPTURE-RECONCILIATION-HARDEN-A1

**task_id**: `GPT-CAPTURE-RECONCILIATION-HARDEN-A1`
**run_id**: `{{RUN_ID}}`
**generated_at**: `{{TIMESTAMP}}`

---

You are reviewing the deliverables for task `GPT-CAPTURE-RECONCILIATION-HARDEN-A1` (hardening plan P1-1, Task 3).

## Task Objective

Create a GPT capture reconciliation report generator that scans all GPT review records in the project and produces an end-to-end audit reconciliation report. The report must answer the core audit question: "Does every GPT review request have a complete Submission -> Capture -> Verification -> Verdict chain?"

## Expected Deliverables

1. `scripts/generate_reconciliation_report.py` — Reconciliation report generator
2. `GPT_CAPTURE_RECONCILIATION_REPORT.json` — Machine-readable report (JSON)
3. `GPT_CAPTURE_RECONCILIATION_REPORT.md` — Human-readable report (Markdown)
4. `_validate_reconciliation.py` — Validation script
5. `EXECUTION_REPORT.md` — Execution report

## Review Criteria

Please evaluate:

1. **Completeness**: Does the report cover ALL known GPT review records across the project?
2. **Accuracy**: Are the summary counts (submissions, captures, verified, verdicts, orphans) correct and consistent?
3. **Anomaly Classification**: Are all anomalies properly tagged with type, severity, and explanation?
4. **Authorization Chain**: Is the next_task_authorization chain traced and validated?
5. **Pre-standardization Handling**: Are pre-standardization tasks (AA-*, HANDOFF-PIPELINE-REFACTOR-A1) explicitly identified and explained?
6. **Schema Compliance**: Does the JSON report follow the structure defined in hardening plan §5.4?
7. **Code Quality**: Is the generator script well-structured, documented, and maintainable?

## Evidence Pack Manifest

{{PACK_MANIFEST}}

## Response Format

Please respond with:
1. `overall_judgment`: accepted | accepted_with_limitation | blocked | human_required
2. `evidence_pack_reviewed: true`
3. `attachment_reviewed: true`
4. `blocking_issues`: list or "none"
5. `required_fixes`: list or "none"
6. `limitations`: list (if any)
7. `next_task_authorization`: { task_id, authorized, execute_immediately, ask_before_starting }

run_id: {{RUN_ID}}
task_id: GPT-CAPTURE-RECONCILIATION-HARDEN-A1

END_OF_GPT_RESPONSE
