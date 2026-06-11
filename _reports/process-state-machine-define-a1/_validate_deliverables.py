#!/usr/bin/env python3
"""Validation suite for PROCESS-STATE-MACHINE-DEFINE-A1 deliverables.

Checks:
1. PROCESS_STATE_MACHINE.json parses and has complete structure
2. CHANGED_FILES_SCHEMA.json parses and is valid JSON Schema
3. State machine completeness: all states reachable, all transitions valid
4. changed_files_utils.py works end-to-end
"""

import json
import sys
import tempfile
import os
from pathlib import Path

REPORT_DIR = Path('D:/agent-acceptance/_reports/process-state-machine-define-a1')
results = []


def check(name: str, passed: bool, detail: str = ''):
    status = 'PASS' if passed else 'FAIL'
    results.append({'name': name, 'status': status, 'detail': detail})
    print(f'  [{status}] {name}' + (f' — {detail}' if detail else ''))


print('=' * 60)
print('PROCESS-STATE-MACHINE-DEFINE-A1 Validation Suite')
print('=' * 60)

# ---- Test 1: PROCESS_STATE_MACHINE.json structure ----
print('\n--- PROCESS_STATE_MACHINE.json ---')
psm_path = REPORT_DIR / 'PROCESS_STATE_MACHINE.json'
psm = json.loads(psm_path.read_text(encoding='utf-8'))

check('PSM-01: JSON parses', True)
check('PSM-02: has states array', 'states' in psm and isinstance(psm['states'], list), f'{len(psm.get("states", []))} states')
check('PSM-03: has transitions array', 'transitions' in psm and isinstance(psm['transitions'], list), f'{len(psm.get("transitions", []))} transitions')
check('PSM-04: has invariants array', 'invariants' in psm and isinstance(psm['invariants'], list), f'{len(psm.get("invariants", []))} invariants')
check('PSM-05: has initial_state', psm.get('initial_state') == 'draft', f'initial_state={psm.get("initial_state")}')
check('PSM-06: has final_states', 'closed' in psm.get('final_states', []), f'final_states={psm.get("final_states")}')

# Check all 8 states exist
expected_states = {'draft', 'gate_passing', 'gpt_reviewing', 'accepted', 'accepted_with_limitation', 'blocked', 'human_required', 'closed'}
actual_states = {s['name'] for s in psm['states']}
check('PSM-07: all 8 states defined', actual_states == expected_states, f'missing: {expected_states - actual_states}')

# Check all 10 transitions
check('PSM-08: 10 transitions defined', len(psm['transitions']) == 10, f'count={len(psm["transitions"])}')

# Check transition IDs
t_ids = {t['id'] for t in psm['transitions']}
expected_t_ids = {f'T{i:02d}' for i in range(1, 11)}
check('PSM-09: transition IDs T01-T10', t_ids == expected_t_ids, f'missing: {expected_t_ids - t_ids}')

# Check all transitions reference valid states
valid_transition_states = expected_states | {'*'}
bad_transitions = []
for t in psm['transitions']:
    if t['from'] not in expected_states:
        bad_transitions.append(f'{t["id"]}: from={t["from"]}')
    if t['to'] not in expected_states:
        bad_transitions.append(f'{t["id"]}: to={t["to"]}')
check('PSM-10: all transitions reference valid states', len(bad_transitions) == 0, '; '.join(bad_transitions) if bad_transitions else '')

# Check all transitions have guards
no_guard = [t['id'] for t in psm['transitions'] if not t.get('guard')]
check('PSM-11: all transitions have guards', len(no_guard) == 0, f'missing guard: {no_guard}')

# Check all transitions require evidence
no_evidence = [t['id'] for t in psm['transitions'] if not t.get('evidence_required')]
check('PSM-12: all transitions require evidence', len(no_evidence) == 0, f'missing evidence: {no_evidence}')

# Check all states are reachable from draft
# BFS from draft
reachable = set()
queue = ['draft']
while queue:
    current = queue.pop(0)
    if current in reachable:
        continue
    reachable.add(current)
    for t in psm['transitions']:
        if t['from'] == current and t['to'] not in reachable:
            queue.append(t['to'])
unreachable = expected_states - reachable
check('PSM-13: all states reachable from draft', len(unreachable) == 0, f'unreachable: {unreachable}')

# Check forbidden transitions reference valid states
for ft in psm.get('forbidden_transitions', []):
    if ft['from'] not in expected_states:
        bad_transitions.append(f'forbidden: from={ft["from"]}')
check('PSM-14: forbidden transitions valid', len([b for b in bad_transitions if 'forbidden' in b]) == 0)

# Check invariants have IDs
inv_ids = {inv['id'] for inv in psm['invariants']}
expected_invs = {f'INV-{i:02d}' for i in range(1, 9)}
check('PSM-15: invariants INV-01 to INV-08', inv_ids == expected_invs, f'missing: {expected_invs - inv_ids}')

# Check authorization mechanism
check('PSM-16: has authorization_mechanism', 'authorization_mechanism' in psm)
check('PSM-17: has review_round_limit', psm.get('review_round_limit', {}).get('max_rounds') == 3)

# ---- Test 2: CHANGED_FILES_SCHEMA.json ----
print('\n--- CHANGED_FILES_SCHEMA.json ---')
cfs_path = REPORT_DIR / 'CHANGED_FILES_SCHEMA.json'
cfs = json.loads(cfs_path.read_text(encoding='utf-8'))

check('CFS-01: JSON parses', True)
check('CFS-02: has $schema', '$schema' in cfs)
check('CFS-03: has title', cfs.get('title') == 'ChangedFilesEvidence')
check('CFS-04: has required fields', set(cfs.get('required', [])) == {'schema_version', 'task_id', 'snapshot_before', 'snapshot_after', 'changes'})
check('CFS-05: has changes.items with properties', 'properties' in cfs.get('properties', {}).get('changes', {}).get('items', {}))
check('CFS-06: has change_type enum', set(cfs['properties']['changes']['items']['properties']['change_type'].get('enum', [])) == {'added', 'modified', 'deleted', 'renamed', 'permission_changed'})
check('CFS-07: has conditional validations (allOf)', 'allOf' in cfs['properties']['changes']['items'])

# Try jsonschema validation of the schema itself
try:
    import jsonschema
    # Validate a sample against the schema
    sample = {
        'schema_version': '1.0.0',
        'task_id': 'TEST-TASK',
        'snapshot_before': '2026-06-09T00:00:00+00:00',
        'snapshot_after': '2026-06-09T01:00:00+00:00',
        'changes': [
            {
                'path': 'test/file.py',
                'change_type': 'added',
                'sha256_before': None,
                'sha256_after': 'a' * 64,
                'size_before': None,
                'size_after': 100,
                'tracked': True,
                'rename_from': None,
                'permission_before': None,
                'permission_after': None,
                'evidence_ref': None,
                'state_transition_ref': None,
            }
        ],
        'summary': {
            'total_added': 1,
            'total_modified': 0,
            'total_deleted': 0,
            'total_renamed': 0,
            'total_permission_changed': 0,
            'total_changes': 1,
        },
        'metadata': {
            'generator': 'test',
            'generated_at': '2026-06-09T01:00:00+00:00',
            'project_root': '/test',
        },
    }
    # Remove $schema for validation (to avoid network fetch)
    cfs_copy = json.loads(json.dumps(cfs))
    cfs_copy.pop('$schema', None)
    cfs_copy.pop('$id', None)
    jsonschema.validate(sample, cfs_copy)
    check('CFS-08: sample validates against schema (jsonschema)', True)
except ImportError:
    check('CFS-08: sample validates against schema (jsonschema)', False, 'jsonschema not installed — structural check only')
except Exception as e:
    check('CFS-08: sample validates against schema (jsonschema)', False, str(e)[:100])

# ---- Test 3: changed_files_utils.py end-to-end ----
print('\n--- changed_files_utils.py ---')
sys.path.insert(0, str(REPORT_DIR))
from changed_files_utils import (
    generate_changed_files_evidence,
    validate_changed_files,
    summarize_changes,
    diff_snapshots,
)

before = {
    'file_a.py': {'sha256': 'a' * 64, 'size': 100, 'tracked': True},
    'file_b.py': {'sha256': 'b' * 64, 'size': 200, 'tracked': True},
}
after = {
    'file_a.py': {'sha256': 'c' * 64, 'size': 150, 'tracked': True},  # modified
    'file_c.py': {'sha256': 'd' * 64, 'size': 300, 'tracked': True},  # added
    # file_b.py deleted
}

changes = diff_snapshots(before, after)
check('UTIL-01: diff detects correct changes', len(changes) == 3, f'{len(changes)} changes detected')

change_types = {c['path']: c['change_type'] for c in changes}
check('UTIL-02: change types correct', change_types == {'file_a.py': 'modified', 'file_b.py': 'deleted', 'file_c.py': 'added'})

evidence = generate_changed_files_evidence('TEST-TASK', before, after, run_id='TEST-RUN')
check('UTIL-03: generate returns valid structure', 'changes' in evidence and 'summary' in evidence)
check('UTIL-04: summary correct', evidence['summary']['total_changes'] == 3)

validation = validate_changed_files(evidence)
check('UTIL-05: self-validation passes', validation['valid'], f'errors: {validation["errors"]}')

summary_text = summarize_changes(evidence)
check('UTIL-06: summarize produces text', len(summary_text) > 50 and 'TEST-TASK' in summary_text)

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
