# Negative Fixture Declaration

This directory is intentionally invalid.
It exists to test that governance validation detects:
- missing executor_id in chain-evidence.json
- run_id mismatch between directory name and chain-evidence.json

This fixture must not be treated as completed run evidence.
This fixture must not support any accepted closure claim.

## Governance Disposition
- classification: negative_test_fixture
- expected_valid: false
- expected_invalid: true
