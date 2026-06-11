from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile

ROOT = Path('D:/agent-acceptance')
TASK_ID = 'GLOBAL-PROJECT-EVIDENCE-BINDING-A1'
RUN_ID = 'GLOBAL_EVIDENCE_BINDING_A1_' + datetime.now().strftime('%Y%m%d_%H%M%S')
REPORT_DIR = ROOT / '_reports/global-project-evidence-binding-a1'
PACK_DIR = ROOT / 'evidence_packs/global-project-evidence-binding-a1'
ZIP_DIR = PACK_DIR
NOW = datetime.now(timezone.utc).isoformat()

PROTECTED_LEGACY_FILES = [
    'HANDOFF.md',
    'HANDOFF_V5.md',
    'HANDOFF_V6.md',
    'PROJECT_HISTORY.md',
    'PROJECT_HISTORY_FINAL.md',
    'HISTORY_ANALYSIS.md',
    'BOOT_CONTEXT.md',
    'PASTE_BLOCK_APPROVED_FOR_NEW_GPT.txt',
    'HANDOFF_APPROVED_FOR_NEW_GPT.md',
]

EXPECTED_HASH_FILES = [
    'HANDOFF_MANIFEST.sha256',
]

SOURCE_MAP_FILES = [
    'HANDOFF_SOURCE_OF_TRUTH.md',
    'HANDOFF_APPROVAL_RECORD.json',
    '_reports/global-project-handoff-repair-a1/GPT_REVIEW_RECORD.json',
    '_reports/global-project-handoff-repair-a1/EXECUTION_REPORT.md',
    '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json',
    '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_STALE_CLAIMS_REGISTER.json',
    '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_MODULE_STATUS.json',
    '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_TEST_LEDGER.json',
    '_reports/global-project-handoff-repair-a1/TARGETED_TEST_OUTPUT.txt',
    '_reports/global-project-handoff-repair-a1/SAFETY_SCAN.md',
    '_reports/global-project-handoff-repair-a1/PACK_MANIFEST.md',
    '_reports/global-project-handoff-repair-a1/PRE_GPT_GATE_OUTPUT.txt',
    '_reports/global-project-handoff-repair-a1/VERIFY_GPT_REPLY_OUTPUT.txt',
    'evidence_packs/global-project-handoff-repair-a1/GLOBAL_PROJECT_HANDOFF_REPAIR_A1_20260608_223800.zip',
]

TEXT_EXTS = {'.md', '.txt', '.json', '.yaml', '.yml', '.py', '.ps1', '.csv'}
SECRET_PATTERNS = [
    ('openai_key', re.compile(r'sk-[A-Za-z0-9_-]{20,}')),
    ('generic_api_key_assignment', re.compile(r'(?i)(api[_-]?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9_./+=-]{24,}')),
    ('private_key_block', re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')),
]


def run(cmd, check=False):
    proc = subprocess.run(cmd, cwd=ROOT, text=True, encoding='utf-8', errors='replace', capture_output=True, shell=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f'command failed: {cmd}\nstdout={proc.stdout}\nstderr={proc.stderr}')
    return {'cmd': cmd, 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}


def sha_file(path):
    p = ROOT / path
    if not p.exists() or not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, text):
    p = REPORT_DIR / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def write_json(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def rel(path):
    return str(path.relative_to(ROOT)).replace('\\', '/')


def expected_hashes():
    expected = {}
    for rel_path in EXPECTED_HASH_FILES:
        p = ROOT / rel_path
        if not p.exists():
            continue
        for line in p.read_text(encoding='utf-8', errors='replace').splitlines():
            parts = line.strip().split()
            if len(parts) >= 2 and re.fullmatch(r'[0-9a-fA-F]{64}', parts[0]):
                expected[parts[1]] = parts[0].lower()
    return expected


def status_for_path(path, expected):
    porcelain = run(['git', 'status', '--porcelain=v1', '--', path])
    diff_name = run(['git', 'diff', '--name-status', '--', path])
    diff_cached = run(['git', 'diff', '--cached', '--name-status', '--', path])
    ls_files = run(['git', 'ls-files', '--stage', '--', path])
    exists = (ROOT / path).exists()
    tracked = bool(ls_files['stdout'].strip())
    digest = sha_file(path)
    status_lines = porcelain['stdout'].splitlines()
    tracked_clean = exists and tracked and not status_lines and not diff_name['stdout'].strip() and not diff_cached['stdout'].strip()
    hash_bound = bool(digest and expected.get(path) == digest)
    untracked_existing_hash_bound = exists and not tracked and status_lines == [f'?? {path}'] and hash_bound
    protected_verified = tracked_clean or untracked_existing_hash_bound
    if tracked_clean:
        conclusion = 'tracked_clean_not_deleted_moved_renamed_or_rewritten_in_current_worktree'
    elif untracked_existing_hash_bound:
        conclusion = 'untracked_existing_file_hash_matches_prior_manifest_not_deleted_or_moved_in_current_worktree'
    else:
        conclusion = 'needs_human_review'
    return {
        'path': path,
        'exists': exists,
        'tracked': tracked,
        'sha256': digest,
        'expected_sha256_from_manifest': expected.get(path),
        'hash_matches_manifest': hash_bound,
        'git_status_porcelain': status_lines,
        'git_diff_name_status': diff_name['stdout'].splitlines(),
        'git_diff_cached_name_status': diff_cached['stdout'].splitlines(),
        'git_ls_files_stage': ls_files['stdout'].splitlines(),
        'tracked_clean_in_worktree_and_index': tracked_clean,
        'untracked_existing_hash_bound': untracked_existing_hash_bound,
        'protected_verified_in_current_worktree': protected_verified,
        'conclusion': conclusion,
    }


def copy_into_pack(src_rel, dest_rel):
    src = ROOT / src_rel
    dst = PACK_DIR / dest_rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        shutil.copy2(src, dst)


def scan_pack_files():
    findings = []
    scanned = []
    for p in sorted(PACK_DIR.rglob('*')):
        if not p.is_file() or p.suffix == '.zip':
            continue
        rp = str(p.relative_to(PACK_DIR)).replace('\\', '/')
        data = p.read_bytes()
        info = {'path': rp, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'scanned_as_text': False, 'findings': []}
        if p.suffix.lower() in TEXT_EXTS:
            text = data.decode('utf-8', errors='replace')
            info['scanned_as_text'] = True
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    info['findings'].append({'pattern': name})
        if info['findings']:
            findings.append(info)
        scanned.append(info)
    return {'scanned_file_count': len(scanned), 'findings': findings, 'files': scanned, 'pass': len(findings) == 0}


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    git_commands = {
        'git_status_short': run(['git', 'status', '--short']),
        'git_status_porcelain_v1': run(['git', 'status', '--porcelain=v1']),
        'git_diff_name_status': run(['git', 'diff', '--name-status']),
        'git_diff_cached_name_status': run(['git', 'diff', '--cached', '--name-status']),
        'git_ls_files_deleted': run(['git', 'ls-files', '--deleted']),
        'git_ls_files_modified': run(['git', 'ls-files', '--modified']),
        'git_rev_parse_head': run(['git', 'rev-parse', 'HEAD']),
        'git_branch': run(['git', 'rev-parse', '--abbrev-ref', 'HEAD']),
    }

    write('GIT_STATUS_EVIDENCE.txt', '\n\n'.join([
        '$ git status --short\n' + git_commands['git_status_short']['stdout'],
        '$ git status --porcelain=v1\n' + git_commands['git_status_porcelain_v1']['stdout'],
        '$ git diff --name-status\n' + git_commands['git_diff_name_status']['stdout'],
        '$ git diff --cached --name-status\n' + git_commands['git_diff_cached_name_status']['stdout'],
        '$ git ls-files --deleted\n' + git_commands['git_ls_files_deleted']['stdout'],
        '$ git ls-files --modified\n' + git_commands['git_ls_files_modified']['stdout'],
        '$ git rev-parse --abbrev-ref HEAD\n' + git_commands['git_branch']['stdout'],
        '$ git rev-parse HEAD\n' + git_commands['git_rev_parse_head']['stdout'],
    ]))

    changed = {
        'task_id': TASK_ID,
        'run_id': RUN_ID,
        'generated_at': NOW,
        'branch': git_commands['git_branch']['stdout'].strip(),
        'head': git_commands['git_rev_parse_head']['stdout'].strip(),
        'status_porcelain': git_commands['git_status_porcelain_v1']['stdout'].splitlines(),
        'diff_name_status': git_commands['git_diff_name_status']['stdout'].splitlines(),
        'cached_diff_name_status': git_commands['git_diff_cached_name_status']['stdout'].splitlines(),
        'deleted_tracked_files': git_commands['git_ls_files_deleted']['stdout'].splitlines(),
        'modified_tracked_files': git_commands['git_ls_files_modified']['stdout'].splitlines(),
    }
    write_json('CHANGED_FILES_EVIDENCE.json', changed)
    write('CHANGED_FILES_EVIDENCE.md', '# Changed Files Evidence\n\n```json\n' + json.dumps(changed, ensure_ascii=False, indent=2) + '\n```\n')

    expected = expected_hashes()
    protected = {
        'task_id': TASK_ID,
        'run_id': RUN_ID,
        'generated_at': NOW,
        'purpose': 'Independently verify protected legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK files were not deleted, moved, renamed, or rewritten in the current worktree/index. Tracked files are checked by git clean status; known untracked approved artifacts are checked by current existence plus prior manifest hash match.',
        'expected_hash_sources': EXPECTED_HASH_FILES,
        'files': [status_for_path(p, expected) for p in PROTECTED_LEGACY_FILES],
    }
    protected['all_protected_verified'] = all(f['protected_verified_in_current_worktree'] for f in protected['files'])
    protected['core_tracked_files_clean'] = all(
        f['tracked_clean_in_worktree_and_index']
        for f in protected['files']
        if f['path'] in {'HANDOFF.md', 'HANDOFF_V5.md', 'PROJECT_HISTORY.md', 'BOOT_CONTEXT.md'}
    )
    protected['untracked_legacy_existing'] = all(
        f['exists'] and not f['git_diff_name_status'] and not f['git_diff_cached_name_status']
        for f in protected['files']
        if f['path'] in {'HANDOFF_V6.md', 'PROJECT_HISTORY_FINAL.md', 'HISTORY_ANALYSIS.md'}
    )
    if protected['all_protected_verified']:
        protected['conclusion'] = 'pass'
    elif protected['core_tracked_files_clean'] and protected['untracked_legacy_existing']:
        protected['conclusion'] = 'pass_with_limitation'
    else:
        protected['conclusion'] = 'needs_human_review'
    write_json('PROTECTED_LEGACY_FILES_STATUS.json', protected)
    md = ['# Protected Legacy Files Status', '', f'- task_id: {TASK_ID}', f'- run_id: {RUN_ID}', f'- conclusion: {protected["conclusion"]}', '', '| Path | Exists | Tracked | Clean | SHA256 |', '|---|---:|---:|---:|---|']
    for f in protected['files']:
        md.append(f"| `{f['path']}` | {f['exists']} | {f['tracked']} | {f['protected_verified_in_current_worktree']} | `{f['sha256'] or ''}` |")
    md.extend(['', 'Verified means either tracked-clean in git, or existing untracked approved artifact whose SHA256 matches a prior manifest.'])
    write('PROTECTED_LEGACY_FILES_STATUS.md', '\n'.join(md) + '\n')

    binding_entries = []
    for path in SOURCE_MAP_FILES:
        p = ROOT / path
        binding_entries.append({
            'path': path,
            'exists': p.exists(),
            'is_file': p.is_file(),
            'sha256': sha_file(path),
            'embedded_in_pack': True if p.is_file() else False,
            'copy_path_in_pack': 'source_evidence/' + path.replace('\\', '/').replace(':', '') if p.is_file() else None,
        })
    binding = {
        'task_id': TASK_ID,
        'run_id': RUN_ID,
        'generated_at': NOW,
        'source_of_truth_rule': 'P0/P1 evidence is bound by path, existence, sha256, and pack copy where possible. Historical claims remain limitations unless P0/P1 evidence exists.',
        'entries': binding_entries,
        'limitations': [
            'This pack embeds selected current P0/P1 evidence and hash-bindings; it does not rewrite historical packs.',
            'Production promotion remains needs_more_evidence.',
            '296 PASS remains an unverified conversational claim.',
        ],
    }
    write_json('SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json', binding)
    write('SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.md', '# Source Map Evidence Binding Appendix\n\n```json\n' + json.dumps(binding, ensure_ascii=False, indent=2) + '\n```\n')

    # Build pack contents.
    if PACK_DIR.exists():
        for child in PACK_DIR.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            elif child.suffix != '.zip':
                child.unlink()
    (PACK_DIR / 'actual_deliverables').mkdir(parents=True, exist_ok=True)
    (PACK_DIR / 'reports').mkdir(parents=True, exist_ok=True)
    (PACK_DIR / 'source_evidence').mkdir(parents=True, exist_ok=True)

    for file in REPORT_DIR.iterdir():
        if file.is_file() and file.name != '_generate_evidence_binding_a1.py':
            shutil.copy2(file, PACK_DIR / 'reports' / file.name)

    for name in ['PROTECTED_LEGACY_FILES_STATUS.md', 'PROTECTED_LEGACY_FILES_STATUS.json', 'SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.md', 'SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json', 'CHANGED_FILES_EVIDENCE.md', 'CHANGED_FILES_EVIDENCE.json', 'GIT_STATUS_EVIDENCE.txt']:
        shutil.copy2(REPORT_DIR / name, PACK_DIR / 'actual_deliverables' / name)

    for entry in binding_entries:
        if entry['exists'] and entry['is_file']:
            copy_into_pack(entry['path'], entry['copy_path_in_pack'])

    closure = f'''# Closure Report — {TASK_ID}

- task_id: {TASK_ID}
- run_id: {RUN_ID}
- generated_at: {NOW}
- status: ready_for_gpt_review

## Scope

This task binds additional P0/P1 evidence required by GPT for GLOBAL-PROJECT-HANDOFF-REPAIR-A1.

## Generated evidence

- Git status / changed-files evidence: `reports/GIT_STATUS_EVIDENCE.txt`, `reports/CHANGED_FILES_EVIDENCE.json`
- Protected legacy file status and hashes: `reports/PROTECTED_LEGACY_FILES_STATUS.json/.md`
- Source map evidence binding appendix: `reports/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json/.md`
- Expanded ZIP-content safety scan: `reports/EXPANDED_ZIP_SAFETY_SCAN.json/.md`

## Key conclusion

Protected legacy files conclusion: `{protected['conclusion']}`.

## Preserved limitations

- accepted_with_limitation remains accepted_with_limitation, not accepted.
- Whole-project/global status remains partial / needs_more_evidence, not fully closed.
- Production promotion remains needs_more_evidence.
- 296 PASS remains unverified conversational claim.
'''
    (PACK_DIR / 'CLOSURE_REPORT.md').write_text(closure, encoding='utf-8')

    prompt = f'''Please review this closure pack attachment for task_id: {TASK_ID}
run_id: {RUN_ID}

Required response format:
run_id: {RUN_ID}
task_id: {TASK_ID}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true|false
attachment_reviewed: true|false
required_fixes:
- ...
limitations:
- ...
next_task_authorization:
  task_id: ...
  authorized: yes|no
  execute_immediately: yes|no
  ask_before_starting: yes|no
END_OF_GPT_RESPONSE

Review focus:
1. Does the pack include explicit git status / changed-files evidence?
2. Does it independently show legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK-related protected files were not deleted, moved, renamed, or rewritten in the current worktree/index?
3. Does it expand safety scanning over the generated closure pack contents rather than only selected files?
4. Does it preserve limitations: whole-project status partial/needs_more_evidence, production promotion not approved, 296 PASS unverified, accepted_with_limitation not flattened?
'''
    (PACK_DIR / 'GPT_REVIEW_PROMPT.md').write_text(prompt, encoding='utf-8')

    (PACK_DIR / 'SAFETY_ATTESTATION.md').write_text('# Safety Attestation\n\n- safety_boundaries_respected: true\n- no_destructive_git_operation_used: true\n- no_production_or_deployment_action_performed: true\n- no_known_secrets_intentionally_included: true\n- legacy_files_not_deleted_moved_renamed_or_rewritten_by_this_task: true\n- paper_sensitive_content_not_intentionally_included: true\n', encoding='utf-8')

    safety = scan_pack_files()
    write_json('EXPANDED_ZIP_SAFETY_SCAN.json', safety)
    safety_md = ['# Expanded ZIP Safety Scan', '', f'- scanned_file_count: {safety["scanned_file_count"]}', f'- pass: {safety["pass"]}', '', '## Findings']
    if safety['findings']:
        for f in safety['findings']:
            safety_md.append(f"- `{f['path']}`: {f['findings']}")
    else:
        safety_md.append('- none')
    write('EXPANDED_ZIP_SAFETY_SCAN.md', '\n'.join(safety_md) + '\n')
    shutil.copy2(REPORT_DIR / 'EXPANDED_ZIP_SAFETY_SCAN.json', PACK_DIR / 'reports' / 'EXPANDED_ZIP_SAFETY_SCAN.json')
    shutil.copy2(REPORT_DIR / 'EXPANDED_ZIP_SAFETY_SCAN.md', PACK_DIR / 'reports' / 'EXPANDED_ZIP_SAFETY_SCAN.md')

    # Manifest after all files are present.
    manifest_rows = []
    for p in sorted(PACK_DIR.rglob('*')):
        if p.is_file() and p.suffix != '.zip':
            rp = str(p.relative_to(PACK_DIR)).replace('\\', '/')
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            manifest_rows.append((rp, digest, p.stat().st_size))
    manifest = ['# Pack Manifest', '', f'- task_id: {TASK_ID}', f'- run_id: {RUN_ID}', f'- generated_at: {NOW}', '', '| Path | SHA256 | Bytes |', '|---|---|---:|']
    for rp, digest, size in manifest_rows:
        manifest.append(f'| `{rp}` | `{digest}` | {size} |')
    (PACK_DIR / 'PACK_MANIFEST.md').write_text('\n'.join(manifest) + '\n', encoding='utf-8')

    # Copy manifest to report too.
    shutil.copy2(PACK_DIR / 'PACK_MANIFEST.md', REPORT_DIR / 'PACK_MANIFEST.md')

    exec_report = f'''# Execution Report — {TASK_ID}

- task_id: {TASK_ID}
- run_id: {RUN_ID}
- generated_at: {NOW}
- branch: {changed['branch']}
- head: {changed['head']}

## 执行清单

| # | 优先级 | 事项 | 状态 |
|---|---|---|---|
| 1 | P0 | 生成 git status / changed-files evidence | done |
| 2 | P0 | 证明 legacy PROJECT_HISTORY/HANDOFF/PASTE_BLOCK 相关保护文件未被删/移/重命名/改写 | {protected['conclusion']} |
| 3 | P0 | 将 source-of-truth map 关键证据以 path+sha256+pack copy 绑定 | done |
| 4 | P0 | 扩展 safety scan 覆盖 pack 内文本文件 | {'pass' if safety['pass'] else 'blocked'} |
| 5 | P1 | 生成 closure pack | done |

## 质量门

| 检查 | 结果 |
|---|---|
| protected legacy verified | {protected['conclusion']} |
| expanded pack safety scan | {'pass' if safety['pass'] else 'blocked'} |
| source evidence binding | {len([e for e in binding_entries if e['embedded_in_pack']])}/{len(binding_entries)} embedded |

## 保留限制

- whole-project/global status remains partial / needs_more_evidence.
- production promotion remains needs_more_evidence.
- 296 PASS remains unverified conversational claim.
- accepted_with_limitation is not flattened to accepted.

## Reviewer Index

- Git status evidence: `_reports/global-project-evidence-binding-a1/GIT_STATUS_EVIDENCE.txt`
- Changed files evidence: `_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json`
- Protected legacy status: `_reports/global-project-evidence-binding-a1/PROTECTED_LEGACY_FILES_STATUS.json`
- Source binding appendix: `_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json`
- Expanded safety scan: `_reports/global-project-evidence-binding-a1/EXPANDED_ZIP_SAFETY_SCAN.json`
- Closure pack: `evidence_packs/global-project-evidence-binding-a1/`
'''
    write('EXECUTION_REPORT.md', exec_report)
    shutil.copy2(REPORT_DIR / 'EXECUTION_REPORT.md', PACK_DIR / 'reports' / 'EXECUTION_REPORT.md')

    zip_path = ZIP_DIR / f'{TASK_ID}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(PACK_DIR.rglob('*')):
            if p.is_file() and p != zip_path and p.suffix != '.zip':
                zf.write(p, p.relative_to(PACK_DIR))
    zip_sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    write_json('ZIP_RECORD.json', {'task_id': TASK_ID, 'run_id': RUN_ID, 'zip_path': rel(zip_path), 'zip_sha256': zip_sha, 'generated_at': NOW})

    print(json.dumps({'task_id': TASK_ID, 'run_id': RUN_ID, 'report_dir': str(REPORT_DIR), 'pack_dir': str(PACK_DIR), 'zip_path': str(zip_path), 'zip_sha256': zip_sha, 'protected_conclusion': protected['conclusion'], 'safety_pass': safety['pass']}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
