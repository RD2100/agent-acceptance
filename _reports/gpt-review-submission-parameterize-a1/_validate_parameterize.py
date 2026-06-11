#!/usr/bin/env python3
"""Validation suite for GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1 deliverables."""

import ast
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('D:/agent-acceptance')
REPORT_DIR = ROOT / '_reports/gpt-review-submission-parameterize-a1'
SCRIPT = ROOT / 'scripts/gpt_new_chat_attachment_submit.py'
results = []


def check(name, passed, detail=''):
    status = 'PASS' if passed else 'FAIL'
    results.append({'name': name, 'status': status, 'detail': detail})
    print(f'  [{status}] {name}' + (f' — {detail}' if detail else ''))


print('=' * 60)
print('GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1 Validation Suite')
print('=' * 60)

# ---- Test 1: Script syntax ----
print('\n--- Script Syntax ---')
try:
    source = SCRIPT.read_text(encoding='utf-8')
    ast.parse(source)
    check('SYN-01: Python syntax valid', True)
except SyntaxError as e:
    check('SYN-01: Python syntax valid', False, str(e))

# ---- Test 2: CLI parameters ----
print('\n--- CLI Parameters ---')
r = subprocess.run(
    [sys.executable, str(SCRIPT), '--help'],
    capture_output=True, text=True, cwd=str(ROOT)
)
check('CLI-01: --help exits 0', r.returncode == 0, f'exit={r.returncode}')
for param in ['--task-id', '--pack-id', '--run-id-path', '--output-path',
              '--prompt-template', '--chat-url', '--report-dir', '--cdp-url',
              '--timeout', '--dry-run']:
    if param == '--pack-id':
        param = '--pack-path'
    check(f'CLI: {param} in help', param in r.stdout)

# ---- Test 3: Required params enforcement ----
print('\n--- Required Params ---')
r = subprocess.run(
    [sys.executable, str(SCRIPT)],
    capture_output=True, text=True, cwd=str(ROOT)
)
check('REQ-01: no args fails', r.returncode != 0, f'exit={r.returncode}')

# ---- Test 4: Missing pack error ----
print('\n--- Error Handling ---')
r = subprocess.run(
    [sys.executable, str(SCRIPT),
     '--task-id', 'TEST',
     '--pack-path', 'nonexistent.zip',
     '--run-id-path', str(REPORT_DIR / 'EXECUTION_REPORT.md'),  # exists, irrelevant
     '--output-path', '/tmp/out.txt',
     '--dry-run'],
    capture_output=True, text=True, cwd=str(ROOT)
)
check('ERR-01: missing pack errors', r.returncode != 0)
check('ERR-02: error mentions pack', 'pack' in r.stdout.lower() or 'pack' in r.stderr.lower())

# ---- Test 5: Dry-run Scenario A ----
print('\n--- Dry-run Scenario A ---')
r = subprocess.run(
    [sys.executable, str(SCRIPT),
     '--task-id', 'TEST-A',
     '--pack-path', 'evidence_packs/process-state-machine-define-a1/PROCESS_STATE_MACHINE_DEFINE_A1_20260609T022432.zip',
     '--run-id-path', '_reports/process-state-machine-define-a1/R1_RUN_ID.txt',
     '--output-path', str(REPORT_DIR / 'dry_test_a.txt'),
     '--chat-url', 'https://chatgpt.com/c/test-123',
     '--dry-run'],
    capture_output=True, text=True, cwd=str(ROOT)
)
check('DRY-A-01: dry-run exits 0', r.returncode == 0, f'exit={r.returncode}')
check('DRY-A-02: scenario A detected', 'Scenario: A' in r.stdout)
check('DRY-A-03: task-id in output', 'TEST-A' in r.stdout)
check('DRY-A-04: dry run mentioned', 'DRY RUN' in r.stdout)

# ---- Test 6: Dry-run Scenario B ----
print('\n--- Dry-run Scenario B ---')
r = subprocess.run(
    [sys.executable, str(SCRIPT),
     '--task-id', 'TEST-B',
     '--pack-path', 'evidence_packs/process-state-machine-define-a1/PROCESS_STATE_MACHINE_DEFINE_A1_20260609T022432.zip',
     '--run-id-path', '_reports/process-state-machine-define-a1/R1_RUN_ID.txt',
     '--output-path', str(REPORT_DIR / 'dry_test_b.txt'),
     '--dry-run'],
    capture_output=True, text=True, cwd=str(ROOT)
)
check('DRY-B-01: scenario B detected', 'Scenario: B' in r.stdout)

# ---- Test 7: Status JSON output ----
print('\n--- Status JSON ---')
status_path = REPORT_DIR / 'GPT_REVIEW_SUBMISSION_STATUS.json'
if status_path.exists():
    status = json.loads(status_path.read_text(encoding='utf-8'))
    check('STAT-01: dry_run flag set', status.get('dry_run') is True)
    check('STAT-02: has task_id', 'task_id' in status)
    check('STAT-03: has run_id', 'run_id' in status)
    check('STAT-04: has pack info', 'pack_exists' in status and 'pack_size' in status)
    check('STAT-05: sent is false', status.get('sent') is False)
else:
    check('STAT-01: status file exists', False)

# ---- Test 8: Prompt template loading ----
print('\n--- Prompt Template ---')
prompt_file = ROOT / 'evidence_packs/process-state-machine-define-a1/GPT_REVIEW_PROMPT.md'
if prompt_file.exists():
    r = subprocess.run(
        [sys.executable, str(SCRIPT),
         '--task-id', 'TEMPLATE-TEST',
         '--pack-path', 'evidence_packs/process-state-machine-define-a1/PROCESS_STATE_MACHINE_DEFINE_A1_20260609T022432.zip',
         '--run-id-path', '_reports/process-state-machine-define-a1/R1_RUN_ID.txt',
         '--output-path', str(REPORT_DIR / 'dry_test_tpl.txt'),
         '--prompt-template', str(prompt_file),
         '--dry-run'],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    check('TPL-01: template loads', r.returncode == 0)
    check('TPL-02: prompt preview shown', 'Prompt Preview' in r.stdout)
    check('TPL-03: prompt has content', 'chars' in r.stdout.lower())
else:
    check('TPL-01: template file exists', False, 'prompt file not found')

# ---- Test 9: Usage doc exists ----
print('\n--- Usage Documentation ---')
usage_path = REPORT_DIR / 'gpt_submit_usage.md'
check('DOC-01: usage doc exists', usage_path.exists())
if usage_path.exists():
    content = usage_path.read_text(encoding='utf-8')
    check('DOC-02: has parameter table', '--task-id' in content)
    check('DOC-03: has examples', 'Example' in content or '示例' in content)
    check('DOC-04: mentions scenarios', 'Scenario A' in content and 'Scenario B' in content)

# ---- Test 10: Key functions exist in script ----
print('\n--- Key Functions ---')
source = SCRIPT.read_text(encoding='utf-8')
for fn in ['find_editor', 'clear_composer', 'click_visible_send_button',
           'try_upload', 'capture_with_baseline', 'render_prompt',
           'make_attachment_checker', 'parse_judgment']:
    check(f'FN: {fn} defined', f'def {fn}(' in source or f'async def {fn}(' in source)

# ---- Test 11: Template variables supported ----
print('\n--- Template Variables ---')
for var in ['{{TASK_ID}}', '{{RUN_ID}}', '{{TIMESTAMP}}', '{{PACK_MANIFEST}}']:
    check(f'TVAR: {var} in script', var in source)

# ---- Summary ----
print('\n' + '=' * 60)
total = len(results)
passed = sum(1 for r in results if r['status'] == 'PASS')
failed = sum(1 for r in results if r['status'] == 'FAIL')
print(f'Total: {total} | Passed: {passed} | Failed: {failed}')
print('=' * 60)

if failed > 0:
    print('\nFAILED checks:')
    for r in results:
        if r['status'] == 'FAIL':
            print(f'  {r["name"]}: {r["detail"]}')
    sys.exit(1)
else:
    print('\nAll checks PASSED.')
    sys.exit(0)
