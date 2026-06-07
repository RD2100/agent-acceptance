# GROUP-01 R4 Delta Note

This R4 pack supersedes earlier GROUP-01 attempts.

Confirmed changes in this pack:
- Negative GROUP-01 tests now use real fail-closed assertions via `pytest.raises(AssertionError)` where invalid input is expected.
- `TARGETED_TEST_OUTPUT.txt` shows `60 passed` and no `PytestReturnNotNoneWarning` for GROUP-01 test files.
- `FULL_TEST_OUTPUT.txt` / `TEST_OUTPUT.txt` still show `170 passed, 21 warnings`; those warnings are from non-GROUP-01 legacy files such as `tests/test_framework_usage.py` and `tests/test_paper_acceptance_contracts.py`.
- `BYPASS_CHECK_OUTPUT.txt` remains a GROUP-01 selected-files-only PASS.
- `BYPASS_SCOPE_NOTE.txt` remains included.
