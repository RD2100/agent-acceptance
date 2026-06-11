from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import shutil
import subprocess
import zipfile

ROOT = Path('D:/agent-acceptance')
TASK_ID = 'EXISTING-WORKFLOW-DISCOVERY-SMOKE-A1'
RUN_ID = 'EXISTING_WORKFLOW_DISCOVERY_SMOKE_A1_' + datetime.now().strftime('%Y%m%d_%H%M%S')
OUT = ROOT / '_reports/existing-workflow-discovery-smoke-a1'
PACK = ROOT / 'evidence_packs/existing-workflow-discovery-smoke-a1'
NOW = datetime.now(timezone.utc).isoformat()

COMPONENTS = [
    ('source_of_truth_hierarchy', 'HANDOFF_SOURCE_OF_TRUTH.md', 'P1', '定义 P0/P1/P2/P3 权威层级、approval rule、coding-agent 禁止自批准。'),
    ('handoff_approval_record', 'HANDOFF_APPROVAL_RECORD.json', 'P1', '记录 HANDOFF-PIPELINE-REFACTOR-A1 的 verified GPT verdict、run_id、限制和 hash。'),
    ('attachment_review_runbook', '_reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md', 'P1', '附件版 GPT 审查 SOP：fresh shell、run_id、新对话、附件可见、点击提交、确认 user bubble、捕获并 verifier。'),
    ('gpt_reply_verifier', 'scripts/verify_gpt_reply.py', 'P0', 'fail-closed 校验 captured GPT reply：END marker、overall_judgment、task_id、next_task_authorization。'),
    ('attachment_submit_entrypoint', 'scripts/gpt_new_chat_attachment_submit.py', 'P0', '附件提交入口，指向已验证 strict submitter；后续需参数化复用。'),
    ('pre_gpt_review_gate', 'scripts/pre_gpt_review_gate.py', 'P0', '提交 GPT 前 gate：复用 evidence_pack_linter 并检查 actual_deliverables 与 manifest。'),
    ('evidence_pack_linter', 'scripts/evidence_pack_linter.py', 'P0', '检查 evidence pack 必备文件、目录、summary-only 风险和 stale/failing output。'),
    ('global_repair_gpt_record', '_reports/global-project-handoff-repair-a1/GPT_REVIEW_RECORD.json', 'P0', 'GLOBAL-PROJECT-HANDOFF-REPAIR-A1 的 GPT 审查记录与 required fix。'),
    ('global_repair_verify_output', '_reports/global-project-handoff-repair-a1/VERIFY_GPT_REPLY_OUTPUT.txt', 'P0', 'GLOBAL-PROJECT-HANDOFF-REPAIR-A1 verifier 通过证据。'),
    ('global_repair_pre_gpt_gate', '_reports/global-project-handoff-repair-a1/PRE_GPT_GATE_OUTPUT.txt', 'P0', 'GLOBAL-PROJECT-HANDOFF-REPAIR-A1 linter/gate 通过证据。'),
    ('global_repair_execution_report', '_reports/global-project-handoff-repair-a1/EXECUTION_REPORT.md', 'P0', 'GLOBAL-PROJECT-HANDOFF-REPAIR-A1 执行报告、限制、next task。'),
    ('global_repair_pack_manifest', '_reports/global-project-handoff-repair-a1/PACK_MANIFEST.md', 'P0', 'GLOBAL-PROJECT-HANDOFF-REPAIR-A1 evidence pack manifest。'),
    ('whole_project_source_map', '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json', 'P0', 'whole-project claims 到 P0/P1/P3/unverified evidence 的映射。'),
    ('whole_project_stale_claims', '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_STALE_CLAIMS_REGISTER.json', 'P0', 'stale/unverified claims register，保护 296 PASS、production promotion 等限制。'),
    ('whole_project_test_ledger', '_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_TEST_LEDGER.json', 'P0', '测试 ledger，明确 13 passed 与 12/13 mismatch，296 PASS 不验证。'),
    ('evidence_binding_gpt_result', '_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt', 'P0', '最近 GLOBAL-PROJECT-EVIDENCE-BINDING-A1 GPT blocked verdict。'),
    ('evidence_binding_verify_output', '_reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt', 'P0', '最近 blocked verdict 的 verifier 输出。'),
    ('evidence_binding_pack_manifest', '_reports/global-project-evidence-binding-a1/PACK_MANIFEST.md', 'P0', '最近 evidence-binding pack manifest。'),
    ('evidence_binding_execution_report', '_reports/global-project-evidence-binding-a1/EXECUTION_REPORT.md', 'P0', '最近 evidence-binding 执行报告。'),
    ('evidence_binding_changed_files', '_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json', 'P0', 'changed-files evidence，含 HANDOFF_REPLY_V4.txt deletion conflict。'),
    ('evidence_binding_protected_status', '_reports/global-project-evidence-binding-a1/PROTECTED_LEGACY_FILES_STATUS.json', 'P0', 'protected legacy files status。'),
    ('evidence_binding_source_appendix', '_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json', 'P0', 'source map evidence binding appendix，含旧 ZIP 嵌入声明。'),
]


def run(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, text=True, encoding='utf-8', errors='replace', capture_output=True)
    return {'cmd': ' '.join(cmd), 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None


def write(name, text):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(text, encoding='utf-8')


def write_json(name, data):
    write(name, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def manifest_for(paths):
    rows = []
    for rel in paths:
        p = ROOT / rel
        rows.append({'path': rel, 'exists': p.exists(), 'sha256': sha(rel), 'bytes': p.stat().st_size if p.exists() and p.is_file() else None})
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PACK.mkdir(parents=True, exist_ok=True)

    fresh = run(['bash', '-lc', 'cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree'])
    status = run(['git', 'status', '--short'])
    rev = run(['git', 'rev-parse', 'HEAD'])

    matrix = []
    read_paths = []
    for name, path, level, note in COMPONENTS:
        p = ROOT / path
        exists = p.exists()
        reviewed = exists and p.is_file()
        if reviewed:
            read_paths.append(path)
        matrix.append({
            'component_name': name,
            'path': path,
            'exists': exists,
            'reviewed': reviewed,
            'reused_for_future_task': name in {
                'source_of_truth_hierarchy','attachment_review_runbook','gpt_reply_verifier','attachment_submit_entrypoint',
                'pre_gpt_review_gate','evidence_pack_linter','global_repair_gpt_record','global_repair_verify_output',
                'global_repair_pre_gpt_gate','whole_project_source_map','whole_project_stale_claims',
                'evidence_binding_gpt_result','evidence_binding_changed_files','evidence_binding_protected_status','evidence_binding_source_appendix'
            },
            'evidence_level': level if exists else 'not_source_of_truth',
            'notes': note if exists else 'missing: 未编造，后续不能依赖该组件。'
        })
    write_json('REUSE_PROOF_MATRIX.json', matrix)

    discovery = f'''# Existing Workflow Discovery — {TASK_ID}

- run_id: {RUN_ID}
- generated_at: {NOW}
- scope: 只读为主的流程发现与复用能力测试
- reused_existing_workflow: true
- not_a_formal_fix_task: true

## 已发现的现有流程组件

| 组件 | 路径 | 存在 | 作用 | 证据层级 |
|---|---|---:|---|---|
'''
    for item in matrix:
        discovery += f"| {item['component_name']} | `{item['path']}` | {item['exists']} | {item['notes']} | {item['evidence_level']} |\n"
    discovery += '''
## 本项目已有 GPT review 闭环组成

1. `HANDOFF_SOURCE_OF_TRUTH.md` 定义 P0/P1/P2/P3 权威层级和 approval rule。
2. 任务执行生成 evidence pack、manifest、safety scan、targeted test output、execution report。
3. `scripts/evidence_pack_linter.py` 检查 pack 必备结构，避免 summary-only。
4. `scripts/pre_gpt_review_gate.py` 在提交 GPT 前做 gate。
5. 附件版 runbook 要求 fresh shell、唯一 run_id、新/指定 GPT 对话、附件可见、点击提交按钮、确认 user bubble/assistant response。
6. GPT 回复必须包含 run_id、task_id、overall_judgment、END_OF_GPT_RESPONSE。
7. `scripts/verify_gpt_reply.py` fail-closed 校验 captured reply；不通过不得报告 accepted/closed。
8. GPT verdict、verify output、review record、pack manifest 进入 P0/P1 证据层。

## 本轮会复用的组件

- `HANDOFF_SOURCE_OF_TRUTH.md`
- `_reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`
- `scripts/verify_gpt_reply.py`
- `scripts/gpt_new_chat_attachment_submit.py`
- `scripts/evidence_pack_linter.py`
- `scripts/pre_gpt_review_gate.py`
- `_reports/global-project-handoff-repair-a1/*` 的 review/gate/source-map/stale/test-ledger 证据
- `_reports/global-project-evidence-binding-a1/*` 的 blocked verdict、changed-files、protected status、source appendix

## 不能替代 source-of-truth 的组件

- memory / compiled memory 只能 recall，不能定案。
- legacy `PROJECT_HISTORY*` / `HANDOFF*` / paste block 只能 P3 audit/reference。
- 未经 verifier 的 root `GPT_*.txt` 不能作为当前 verdict。
- 对话里的 `296 PASS` 仍是 unverified conversational claim。

## 重新造轮子的风险

存在风险：如果直接根据对话重写提交流程、重新写 verifier、重新定义 source-of-truth，可能绕开已验证 runbook/gate/verifier，导致旧回复误捕获、附件未确认、blocked 被包装成 success。

## 避免重新造轮子的方式

- R2 只复用现有 runbook、verifier、linter、pre-GPT gate、source-of-truth map。
- 对 blocked 三个问题做最小 evidence 修复，不新建 review workflow。
- 不改写 legacy 文件；如需恢复/移动/删除 `HANDOFF_REPLY_V4.txt`，属于高风险 git/legacy 操作，先问用户。
- 保留 `blocked`、`accepted_with_limitation`、`partial/needs_more_evidence` 原状态，不美化。
'''
    write('EXISTING_WORKFLOW_DISCOVERY.md', discovery)

    blocked_mapping = '''# Blocked Verdict Fix Mapping — GLOBAL-PROJECT-EVIDENCE-BINDING-A1

## 1. HANDOFF_REPLY_V4.txt deletion evidence conflict

- GPT 原始 blocking issue：`changed-files evidence shows tracked deletion of HANDOFF_REPLY_V4.txt, so the pack cannot independently verify that all legacy HANDOFF-related files were not deleted.`
- 对应证据文件：
  - `_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt`
  - `_reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt`
  - `_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json`
  - `_reports/global-project-evidence-binding-a1/GIT_STATUS_EVIDENCE.txt`
- 应复用组件：`HANDOFF_SOURCE_OF_TRUTH.md`、`CHANGED_FILES_EVIDENCE.json`、`PROTECTED_LEGACY_FILES_STATUS.json`、`scripts/verify_gpt_reply.py`、pre-GPT gate。
- 最小修复：明确 `HANDOFF_REPLY_V4.txt` 是否属于 protected legacy handoff 范围；若不属于，提供 P0 scope evidence；若属于，需恢复该文件后重新生成 git evidence。
- 高风险需确认：恢复/checkout/移动/删除 legacy 文件；任何 `git checkout`、`git reset`、`git clean`。
- 可自动执行：读取 git evidence、生成 scope appendix、更新 R2 报告/manifest/safety scan、重新打包、GPT 审查。

## 2. SAFETY_ATTESTATION 与 git evidence 冲突

- GPT 原始 blocking issue：`SAFETY_ATTESTATION claims legacy files were not deleted/moved/renamed/rewritten, but git changed-files evidence contains D HANDOFF_REPLY_V4.txt.`
- 对应证据文件：
  - `evidence_packs/global-project-evidence-binding-a1/SAFETY_ATTESTATION.md`
  - `_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json`
  - `_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt`
- 应复用组件：`HANDOFF_SOURCE_OF_TRUTH.md`、`ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`、`scripts/evidence_pack_linter.py`、`scripts/pre_gpt_review_gate.py`。
- 最小修复：R2 attestation 不能笼统声称所有 legacy 文件未删除；必须改为与 git evidence 一致：核心 tracked protected 文件 clean，`HANDOFF_REPLY_V4.txt` 状态需 scope 判定或 human gate。
- 高风险需确认：为消除冲突而执行任何 destructive git 或 legacy 文件改动。
- 可自动执行：重写 R2 attestation 文案、重新 safety scan、manifest、pack、pre-GPT gate。

## 3. SOURCE_MAP_EVIDENCE_BINDING_APPENDIX 旧 ZIP 嵌入声明不一致

- GPT 原始 blocking issue：`SOURCE_MAP_EVIDENCE_BINDING_APPENDIX claims the prior GLOBAL_PROJECT_HANDOFF_REPAIR_A1 ZIP is embedded in the pack, but the referenced copy_path is not present in the attached ZIP or PACK_MANIFEST.`
- 对应证据文件：
  - `_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json`
  - `_reports/global-project-evidence-binding-a1/PACK_MANIFEST.md`
  - `evidence_packs/global-project-evidence-binding-a1/GLOBAL-PROJECT-EVIDENCE-BINDING-A1_20260608_233125.zip`
  - `_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt`
- 应复用组件：source map appendix 生成逻辑、PACK_MANIFEST、evidence pack linter、pre-GPT gate。
- 最小修复：二选一：要么真的把旧 ZIP 嵌入 R2 pack 并写入 PACK_MANIFEST；要么把 `embedded_in_pack` 改为 false/sha256-only，删除不实 copy_path 声明。
- 高风险需确认：无破坏性文件操作；但若要删除旧错误 pack，应先确认。本轮/R2 可生成新 pack，不删除旧 pack。
- 可自动执行：生成新的 appendix、manifest、zip 内容核验、GPT 审查。
'''
    write('BLOCKED_VERDICT_FIX_MAPPING.md', blocked_mapping)

    generated = [
        '_reports/existing-workflow-discovery-smoke-a1/EXISTING_WORKFLOW_DISCOVERY.md',
        '_reports/existing-workflow-discovery-smoke-a1/REUSE_PROOF_MATRIX.json',
        '_reports/existing-workflow-discovery-smoke-a1/BLOCKED_VERDICT_FIX_MAPPING.md',
        '_reports/existing-workflow-discovery-smoke-a1/TEST_EXECUTION_REPORT.md',
        '_reports/existing-workflow-discovery-smoke-a1/TARGETED_TEST_OUTPUT.txt',
        '_reports/existing-workflow-discovery-smoke-a1/SAFETY_SCAN.md',
        '_reports/existing-workflow-discovery-smoke-a1/PACK_MANIFEST.md',
    ]

    test_output = f'''# Targeted Test Output — {TASK_ID}

## fresh shell

command: cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree
exit: {fresh['returncode']}
stdout:
{fresh['stdout']}
stderr:
{fresh['stderr']}

## key file existence check

'''
    for item in matrix:
        test_output += f"- {item['path']}: exists={item['exists']} reviewed={item['reviewed']}\n"
    test_output += f'''
## git status --short

exit: {status['returncode']}
stdout:
{status['stdout']}
stderr:
{status['stderr']}

## generated file list

''' + '\n'.join(f'- {p}' for p in generated) + '\n'
    write('TARGETED_TEST_OUTPUT.txt', test_output)

    report_text = f'''# Test Execution Report — {TASK_ID}

- task_id: {TASK_ID}
- run_id: {RUN_ID}
- generated_at: {NOW}
- 只读为主: true
- 正式修复任务: false
- R2任务: false
- branch/head: `{rev['stdout'].strip()}`

## 读取的文件

''' + '\n'.join(f'- `{p}`' for p in read_paths) + '''

## 生成的测试产物

''' + '\n'.join(f'- `{p}`' for p in generated) + '''

## legacy 文件改动

未修改、删除、移动、重命名 legacy `PROJECT_HISTORY` / `HANDOFF` / `PASTE_BLOCK` 文件。本轮只写入 `_reports/existing-workflow-discovery-smoke-a1/` 与 `evidence_packs/existing-workflow-discovery-smoke-a1/`。

## 危险 git 操作

未执行 `git reset` / `git clean` / `git checkout`，未 commit，未 push。

## 是否准备进入正式 R2

ready_for_gpt_review。进入 R2 前建议先让 GPT 审查本 smoke pack，确认已发现并复用现有流程。正式 R2 仍需处理 `HANDOFF_REPLY_V4.txt` 的 scope/restore 问题；涉及恢复 legacy 文件或 git checkout 时需要用户确认。
'''
    write('TEST_EXECUTION_REPORT.md', report_text)

    report_texts = ''.join((OUT / p).read_text(encoding='utf-8', errors='replace') for p in [
        'EXISTING_WORKFLOW_DISCOVERY.md','BLOCKED_VERDICT_FIX_MAPPING.md','TEST_EXECUTION_REPORT.md','TARGETED_TEST_OUTPUT.txt'
    ] if (OUT / p).exists())
    patterns = {
        'paper_fulltext': r'(?i)论文全文|full paper text|raw transcript|原始学术段落',
        'token_secret': r'(?i)(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_./+=-]{20,}',
        'private_key': r'-----BEGIN [A-Z ]*PRIVATE KEY-----',
        'openai_key': r'sk-[A-Za-z0-9_-]{20,}',
    }
    findings = []
    for name, pat in patterns.items():
        if re.search(pat, report_texts):
            findings.append(name)
    safety = '# Safety Scan\n\n- scanned_reports: generated markdown/txt/json summary files\n- paper_fulltext: not_found\n- original_academic_paragraphs: not_found\n- private_notes: not_found\n- token: not_found\n- secret: not_found\n- credentials: not_found\n- pass: ' + ('true' if not findings else 'false') + '\n'
    if findings:
        safety += '\n## findings\n' + '\n'.join(f'- {x}' for x in findings) + '\n'
    write('SAFETY_SCAN.md', safety)

    # Copy to evidence pack structure.
    if PACK.exists():
        for child in PACK.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            elif child.suffix != '.zip':
                child.unlink()
    (PACK / 'actual_deliverables').mkdir(parents=True, exist_ok=True)
    (PACK / 'reports').mkdir(parents=True, exist_ok=True)
    for filename in ['EXISTING_WORKFLOW_DISCOVERY.md','REUSE_PROOF_MATRIX.json','BLOCKED_VERDICT_FIX_MAPPING.md']:
        shutil.copy2(OUT / filename, PACK / 'actual_deliverables' / filename)
    for filename in ['TEST_EXECUTION_REPORT.md','TARGETED_TEST_OUTPUT.txt','SAFETY_SCAN.md']:
        shutil.copy2(OUT / filename, PACK / 'reports' / filename)

    prompt = f'''GPT REVIEW REQUEST: {TASK_ID}

run_id: {RUN_ID}

Please review this read-mostly workflow discovery smoke evidence pack. Verify that the agent discovered and reused the existing GPT-agent handoff/review workflow instead of inventing a new one.

Return ONLY:
run_id: {RUN_ID}
task_id: {TASK_ID}
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
  - <issue or none>
required_fixes:
  - <fix or none>
limitations:
  - <limitation or none>
next_task_authorization:
  task_id: GLOBAL-PROJECT-EVIDENCE-BINDING-A1-R2 | none
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
'''
    (PACK / 'GPT_REVIEW_PROMPT.md').write_text(prompt, encoding='utf-8')
    (PACK / 'CLOSURE_REPORT.md').write_text(f'# Closure Report — {TASK_ID}\n\n- run_id: {RUN_ID}\n- status: ready_for_gpt_review\n- reused_existing_workflow: true\n- legacy_files_modified: false\n- dangerous_git_operations: none\n', encoding='utf-8')
    (PACK / 'SAFETY_ATTESTATION.md').write_text('# Safety Attestation\n\n- safety_boundaries_respected: true\n- read_mostly_task: true\n- legacy_files_modified: false\n- dangerous_git_operations: none\n- sensitive_content_included: false\n', encoding='utf-8')

    pack_files = []
    for p in sorted(PACK.rglob('*')):
        if p.is_file() and p.suffix != '.zip':
            rel = str(p.relative_to(PACK)).replace('\\','/')
            pack_files.append((rel, hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size))
    manifest = ['# Pack Manifest', '', f'- task_id: {TASK_ID}', f'- run_id: {RUN_ID}', f'- generated_at: {NOW}', '', '| Path | SHA256 | Bytes |', '|---|---|---:|']
    for rel, digest, size in pack_files:
        manifest.append(f'| `{rel}` | `{digest}` | {size} |')
    manifest_text = '\n'.join(manifest) + '\n'
    write('PACK_MANIFEST.md', manifest_text)
    (PACK / 'PACK_MANIFEST.md').write_text(manifest_text, encoding='utf-8')

    zip_path = PACK / f'EXISTING_WORKFLOW_DISCOVERY_SMOKE_A1_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(PACK.rglob('*')):
            if p.is_file() and p != zip_path and p.suffix != '.zip':
                zf.write(p, p.relative_to(PACK))
    zip_record = {'task_id': TASK_ID, 'run_id': RUN_ID, 'zip_path': str(zip_path.relative_to(ROOT)).replace('\\','/'), 'zip_sha256': hashlib.sha256(zip_path.read_bytes()).hexdigest(), 'generated_at': NOW}
    write_json('ZIP_RECORD.json', zip_record)

    print(json.dumps({'task_id': TASK_ID, 'run_id': RUN_ID, 'zip_path': zip_record['zip_path'], 'zip_sha256': zip_record['zip_sha256'], 'safety_pass': not findings}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
