"""conftest.py — Shared fixtures for GPT review regression tests."""

import sys
import pytest
from pathlib import Path

# Add scripts/ to sys.path for imports
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


@pytest.fixture
def valid_accepted_reply():
    """VRT-001: Complete valid GPT reply with verdict = accepted."""
    return """overall_judgment: accepted
evidence_pack_reviewed: true
attachment_reviewed: true
blocking_issues:

none
required_fixes:

none
limitations:

none

run_id: TEST_RUN_ID_001_RD
task_id: TEST-TASK-A1

next_task_authorization:
task_id: NEXT-TASK-A1
authorized: yes
execute_immediately: yes
ask_before_starting: no

END_OF_GPT_RESPONSE"""


@pytest.fixture
def valid_accepted_with_limitation_reply():
    """VRT-002: Complete valid reply with limitations."""
    return """overall_judgment: accepted_with_limitation
evidence_pack_reviewed: true
attachment_reviewed: true
blocking_issues:

none
required_fixes:

none
limitations:

limitation 1: some limitation
limitation 2: another limitation

run_id: TEST_RUN_ID_002_RD
task_id: TEST-TASK-A2

next_task_authorization:
task_id: NEXT-TASK-A2
authorized: yes
execute_immediately: yes
ask_before_starting: no

END_OF_GPT_RESPONSE"""


@pytest.fixture
def reply_missing_run_id():
    """VRT-003: Reply with missing run_id."""
    return """overall_judgment: accepted
evidence_pack_reviewed: true
blocking_issues:
none
required_fixes:
none

task_id: TEST-TASK-A3

next_task_authorization:
task_id: NEXT-TASK-A3
authorized: 已授权

END_OF_GPT_RESPONSE"""


@pytest.fixture
def reply_wrong_run_id():
    """VRT-004: Reply with mismatched run_id."""
    return """overall_judgment: accepted
evidence_pack_reviewed: true
blocking_issues:
none
required_fixes:
none

run_id: WRONG_RUN_ID_RD
task_id: TEST-TASK-A4

next_task_authorization:
task_id: NEXT-TASK-A4
authorized: 已授权

END_OF_GPT_RESPONSE"""


@pytest.fixture
def reply_missing_end_marker():
    """VRT-005: Reply without END_OF_GPT_RESPONSE marker."""
    return """overall_judgment: accepted
evidence_pack_reviewed: true
blocking_issues:
none
required_fixes:
none

run_id: TEST_RUN_ID_005_RD
task_id: TEST-TASK-A5

next_task_authorization:
task_id: NEXT-TASK-A5
authorized: 已授权"""


@pytest.fixture
def reply_invalid_verdict():
    """VRT-007/010: Reply with invalid verdict values."""
    return """overall_judgment: rejected
evidence_pack_reviewed: true
blocking_issues:
none
required_fixes:
none

run_id: TEST_RUN_ID_007_RD
task_id: TEST-TASK-A7

END_OF_GPT_RESPONSE"""


@pytest.fixture
def reply_uppercase_verdict():
    """VRT-007: Reply with uppercase verdict (flattening attack)."""
    return """overall_judgment: ACCEPTED
evidence_pack_reviewed: true
blocking_issues:
none
required_fixes:
none

run_id: TEST_RUN_ID_007B_RD
task_id: TEST-TASK-A7B

next_task_authorization:
task_id: NEXT-TASK
authorized: yes

END_OF_GPT_RESPONSE"""


@pytest.fixture
def reply_truncated():
    """VRT-009: Truncated reply — verdict present but cut short."""
    return """overall_judgment: accepted_with_limitation
evidence_pack_reviewed: true
blocking_issues:
none
required_fixes:
none
limitations:
some lim"""


@pytest.fixture
def valid_evidence_pack(tmp_path):
    """PGT-001: Create a complete valid evidence pack structure."""
    pack = tmp_path / "valid_pack"
    pack.mkdir()

    # Required files
    (pack / "CLOSURE_REPORT.md").write_text("# Closure Report\n")
    (pack / "GPT_REVIEW_PROMPT.md").write_text("# GPT Review Prompt\n")
    (pack / "PACK_MANIFEST.md").write_text("# Pack Manifest\n| SHA-256 |\n|---------|\n")
    (pack / "SAFETY_ATTESTATION.md").write_text("# Safety Attestation\ntrue\n")

    # Required directories
    ad = pack / "actual_deliverables"
    ad.mkdir()
    (ad / "deliverable1.py").write_text("# deliverable 1\n")
    (ad / "deliverable2.py").write_text("# deliverable 2\n")
    (ad / "deliverable3.py").write_text("# deliverable 3\n")
    (ad / "deliverable4.py").write_text("# deliverable 4\n")

    reports = pack / "reports"
    reports.mkdir()
    (reports / "TARGETED_TEST_OUTPUT.txt").write_text("All tests PASS\n")
    (reports / "TEST_OUTPUT.txt").write_text("All tests PASS\n")

    return str(pack)


@pytest.fixture
def empty_evidence_pack(tmp_path):
    """PGT-004: Create an empty evidence pack directory."""
    pack = tmp_path / "empty_pack"
    pack.mkdir()
    return str(pack)


@pytest.fixture
def pack_missing_manifest(tmp_path):
    """PGT-002: Evidence pack missing PACK_MANIFEST.md."""
    pack = tmp_path / "no_manifest_pack"
    pack.mkdir()

    (pack / "CLOSURE_REPORT.md").write_text("# Closure Report\n")
    (pack / "GPT_REVIEW_PROMPT.md").write_text("# GPT Review Prompt\n")
    (pack / "SAFETY_ATTESTATION.md").write_text("# Safety\ntrue\n")

    ad = pack / "actual_deliverables"
    ad.mkdir()
    (ad / "file1.py").write_text("# file\n")

    reports = pack / "reports"
    reports.mkdir()
    (reports / "TEST_OUTPUT.txt").write_text("PASS\n")

    return str(pack)
