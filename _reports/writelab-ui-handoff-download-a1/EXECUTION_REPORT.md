# WriteLab UI Handoff Download A1 Execution Report

verdict: PASS

## Scope

Expose the existing metadata-only WriteLab handoff exporter through the diagnosis history UI.

In scope:

- Add a frontend API helper for `GET /api/reports/diagnosis/{report_id}/writelab-handoff.zip`.
- Add a per-report download button in the diagnosis history panel.
- Keep the UI copy explicit: governance handoff packet, metadata only.
- Give icon-only download/delete actions explicit accessible names.
- Verify the frontend action, backend endpoint, and governance validator.

Out of scope:

- Real paper full-text processing.
- External upload, live CDP, or GPT submission.
- Memory writes containing paper content.
- Rebuilding editor/reference/PDF/document-management features.

## Changed Files

- `D:\writelab\frontend\lib\api.ts`
- `D:\writelab\frontend\lib\__tests__\api.test.ts`
- `D:\writelab\frontend\components\DiagnosisHistoryPanel.tsx`
- `D:\writelab\frontend\components\__tests__\DiagnosisHistoryPanel.test.tsx`
- `D:\writelab\frontend\out\` generated static export files refreshed by `npm run build`
- `D:\agent-acceptance\docs\governance\PROGRESS_LOG.md`
- `D:\agent-acceptance\docs\governance\DECISION_LOG.md`
- `D:\agent-acceptance\docs\governance\RISK_REGISTER.md`
- `D:\agent-acceptance\docs\governance\TECH_DEBT.md`
- `D:\agent-acceptance\docs\governance\VERIFY_MATRIX.md`
- `D:\agent-acceptance\docs\governance\HANDOFF.md`
- `D:\agent-acceptance\docs\governance\PAPER_WORKFLOW_HANDOFF.md`

This slice builds on the backend exporter files from `_reports/writelab-exporter-a1/`.

## Critical Paths

- `api.downloadWritelabHandoff(reportId)` fetches the ZIP endpoint as a Blob and preserves the backend filename from `Content-Disposition`.
- `DiagnosisHistoryPanel` adds a download action beside each saved diagnosis report.
- The download action stops propagation so it does not select the report.
- Download failure is shown as an action-level error without replacing the loaded history list.
- Icon-only download/delete actions expose `aria-label` values and are tested by role/name queries.

## Verification

WriteLab frontend:

- `node_modules\.bin\vitest.cmd run --config vitest.config.ts lib\__tests__\api.test.ts` -> 3 passed.
- `node_modules\.bin\vitest.cmd run --config vitest.config.ts components\__tests__\DiagnosisHistoryPanel.test.tsx` -> 8 passed, including accessible-name queries for download/delete actions.
- `node_modules\.bin\vitest.cmd run --config vitest.config.ts` -> 5 files / 32 tests passed.
- `node_modules\.bin\tsc.cmd --noEmit` -> exit 0.
- `npm run build` -> Next.js production build passed and refreshed `frontend\out`.

WriteLab backend:

- `python -m pytest tests\test_diagnosis_reports.py -q` -> 30 passed.
- `python -m pytest tests -q` -> 169 passed, 2 known golden-case warnings.

Cross-repo governance:

- API probe using WriteLab `TestClient` -> status 200, ZIP written to `_reports/writelab-ui-handoff-download-a1/writelab-handoff.zip`.
- `python scripts\validate_writelab_handoff.py _reports\writelab-ui-handoff-download-a1\writelab-handoff.zip --json-output _reports\writelab-ui-handoff-download-a1\VALIDATION_OUTPUT.json` -> `result=pass`.
- Paper safety run -> 51 passed.
- ZIP marker scan -> pass=true; all raw marker hits false.
- Evidence directory marker scan -> pass=true.
- Governance docs updated to record the UI handoff download slice and preserve real-paper human gates.

## Artifacts

- `_reports/writelab-ui-handoff-download-a1/WRITELAB_UI_TEST_OUTPUT.txt`
- `_reports/writelab-ui-handoff-download-a1/API_PROBE_OUTPUT.txt`
- `_reports/writelab-ui-handoff-download-a1/VALIDATION_OUTPUT.json`
- `_reports/writelab-ui-handoff-download-a1/VALIDATION_STDOUT.txt`
- `_reports/writelab-ui-handoff-download-a1/MARKER_SCAN_OUTPUT.txt`
- `_reports/writelab-ui-handoff-download-a1/DIRECTORY_MARKER_SCAN_OUTPUT.txt`
- `_reports/writelab-ui-handoff-download-a1/PAPER_SAFETY_TEST_OUTPUT.txt`
- `_reports/writelab-ui-handoff-download-a1/writelab-handoff.zip`
- `_reports/writelab-ui-handoff-download-a1/HANDOFF_SAFETY_SCAN.json`
- `_reports/writelab-ui-handoff-download-a1/HANDOFF_SAFETY_SCAN.md`
- `_reports/writelab-ui-handoff-download-a1/HASHES.txt`

## Known Gaps

- No live in-app browser smoke was run because no Browser control tool was exposed in this turn and Playwright is not installed in `D:\writelab\frontend`.
- Real paper execution remains blocked unless separately authorized by a current scoped human gate.
- Dirty C4 files remain untouched: `scripts/paper_c4_section_packet_validator.py` and `tests/test_paper_c4_section_review.py`.
- Backend full tests still show two existing golden-case warnings unrelated to the handoff exporter/UI.

## Technical Debt

- P3: Run a live browser smoke for the download button when Browser/Playwright tooling is available.

## Suggested Review Focus

- Confirm the UI copy does not imply real-paper processing or external submission.
- Confirm clicking the download button does not select/delete the report.
- Confirm the frontend helper calls the exact metadata-only backend endpoint.
