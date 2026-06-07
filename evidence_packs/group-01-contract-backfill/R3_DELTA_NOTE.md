# GROUP-01 R3 Delta Note

This R3 pack supersedes earlier GROUP-01 review attempts.

Confirmed changes in this pack:
- The 10 GROUP-01 test files under `actual_deliverables/tests/` no longer return `(True, message)` or `(False, message)` tuples from `test_*` functions.
- `TARGETED_TEST_OUTPUT.txt` shows `60 passed in 0.32s` with no `PytestReturnNotNoneWarning` for GROUP-01 test files.
- `FULL_TEST_OUTPUT.txt` / `TEST_OUTPUT.txt` show `170 passed, 21 warnings`; remaining warnings are outside GROUP-01 scope.
- `BYPASS_CHECK_OUTPUT.txt` is now a selected-files-only PASS for GROUP-01.
- `BYPASS_SCOPE_NOTE.txt` is included in this pack and explains why scoped bypass evidence is used.
- No runs/* evidence rewrites, HANDOFF deletion, archive hooks, tools governance files, memory outputs, or paper validator residuals are included in GROUP-01 diff.
