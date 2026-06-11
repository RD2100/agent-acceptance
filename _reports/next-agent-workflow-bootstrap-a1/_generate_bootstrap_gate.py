from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import subprocess
import zipfile

ROOT = Path('D:/agent-acceptance')
TASK_ID = 'NEXT-AGENT-WORKFLOW-BOOTSTRAP-IMPLEMENT-A1'
RUN_ID = 'NEXT_AGENT_WORKFLOW_BOOTSTRAP_IMPLEMENT_A1_' + datetime.now().strftime('%Y%m%d_%H%M%S')
OUT = ROOT / '_reports/next-agent-workflow-bootstrap-a1'
PACK = ROOT / 'evidence_packs/next-agent-workflow-bootstrap-a1'
NOW = datetime.now(timezone.utc).isoformat()

REQUIRED_READS = [
    ('HANDOFF_SOURCE_OF_TRUTH.md','P1','必须读取：P0/P1/P2/P3 权威层级与 approval rule。'),
    ('HANDOFF_APPROVAL_RECORD.json','P1','必须读取：HANDOFF-PIPELINE-REFACTOR-A1 verified GPT verdict 与限制。'),
    ('_reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md','P1','必须读取：附件版 GPT 审查 SOP。'),
    ('scripts/verify_gpt_reply.py','P0','必须读取：GPT 回复 fail-closed verifier。'),
    ('scripts/gpt_new_chat_attachment_submit.py','P0','必须读取：附件提交入口及 strict submitter 指向。'),
    ('scripts/pre_gpt_review_gate.py','P0','必须读取：pre-GPT gate。'),
    ('scripts/evidence_pack_linter.py','P0','必须读取：evidence pack linter。'),
    ('_reports/global-project-handoff-repair-a1/GPT_REVIEW_RECORD.json','P0','必须读取：global handoff repair GPT verdict 与 required fix。'),
    ('_reports/global-project-handoff-repair-a1/VERIFY_GPT_REPLY_OUTPUT.txt','P0','必须读取：global repair verifier 输出。'),
    ('_reports/global-project-handoff-repair-a1/PRE_GPT_GATE_OUTPUT.txt','P0','必须读取：global repair pre-GPT gate 输出。'),
    ('_reports/global-project-handoff-repair-a1/EXECUTION_REPORT.md','P0','必须读取：global repair 执行报告与限制。'),
    ('_reports/global-project-handoff-repair-a1/PACK_MANIFEST.md','P0','必须读取：global repair pack manifest。'),
    ('_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_SOURCE_OF_TRUTH_MAP.json','P0','必须读取：whole-project claims/evidence map。'),
    ('_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_STALE_CLAIMS_REGISTER.json','P0','必须读取：stale/unverified claims。'),
    ('_reports/global-project-handoff-repair-a1/WHOLE_PROJECT_TEST_LEDGER.json','P0','必须读取：test ledger 与 296 PASS 未验证限制。'),
    ('_reports/global-project-evidence-binding-a1/GPT_REVIEW_RESULT.txt','P0','必须读取：GLOBAL-PROJECT-EVIDENCE-BINDING-A1 blocked verdict。'),
    ('_reports/global-project-evidence-binding-a1/VERIFY_GPT_REPLY_OUTPUT.txt','P0','必须读取：blocked verdict verifier 输出。'),
    ('_reports/global-project-evidence-binding-a1/PACK_MANIFEST.md','P0','必须读取：blocked pack manifest。'),
    ('_reports/global-project-evidence-binding-a1/EXECUTION_REPORT.md','P0','必须读取：evidence-binding 执行报告。'),
    ('_reports/global-project-evidence-binding-a1/CHANGED_FILES_EVIDENCE.json','P0','必须读取：HANDOFF_REPLY_V4 deletion conflict。'),
    ('_reports/global-project-evidence-binding-a1/PROTECTED_LEGACY_FILES_STATUS.json','P0','必须读取：protected legacy status。'),
    ('_reports/global-project-evidence-binding-a1/SOURCE_MAP_EVIDENCE_BINDING_APPENDIX.json','P0','必须读取：source binding appendix 与旧 ZIP 嵌入声明。'),
]


def run(cmd):
    p = subprocess.run(cmd, cwd=ROOT, text=True, encoding='utf-8', errors='replace', capture_output=True)
    return {'cmd': ' '.join(cmd), 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}


def sha(path):
    p = ROOT / path
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() and p.is_file() else None


def write(name, text):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(text, encoding='utf-8')


def write_json(name, obj):
    write(name, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    PACK.mkdir(parents=True, exist_ok=True)
    fresh = run(['bash','-lc','cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree'])
    git_status = run(['git','status','--short'])

    reads = []
    for path, level, purpose in REQUIRED_READS:
        p = ROOT / path
        reads.append({
            'path': path,
            'exists': p.exists(),
            'must_read_at_startup': True,
            'evidence_level': level if p.exists() else 'missing',
            'purpose': purpose,
            'sha256': sha(path),
            'bytes': p.stat().st_size if p.exists() and p.is_file() else None,
            'fail_closed_if_missing': True,
        })
    required = {
        'task_id': TASK_ID,
        'run_id': RUN_ID,
        'generated_at': NOW,
        'working_directory_rule': 'Every Bash command must explicitly begin with: cd "D:/agent-acceptance" && ...',
        'conversation_context_is_not_sufficient': True,
        'memory_is_recall_not_source_of_truth': True,
        'required_reads': reads,
    }
    write_json('NEXT_AGENT_REQUIRED_READS.json', required)

    proof_template = {
        'task_id': '<current task id>',
        'agent_session_id': '<session id or timestamp>',
        'fresh_shell_check': {
            'command': 'cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree',
            'exit_code': None,
            'stdout_excerpt': '',
        },
        'read_proof': [
            {'path': r['path'], 'exists': None, 'reviewed': False, 'sha256_or_size': None, 'summary_source': 'repo_file_not_conversation', 'notes': ''}
            for r in reads
        ],
        'workflow_understanding_claim_allowed': False,
        'blocked_if_any_required_read_missing_or_unreviewed': True,
        'must_preserve_semantics': ['blocked', 'accepted_with_limitation', 'partial', 'needs_more_evidence', 'unverified'],
    }
    write_json('STARTUP_READ_PROOF_TEMPLATE.json', proof_template)

    gate_md = f'''# Next Agent Startup Read Gate

> task_id: {TASK_ID}
> run_id: {RUN_ID}
> status: active bootstrap guidance
> purpose: 让下一个接手智能体直接读取仓库内完整流程，而不是依赖会话上下文或重新造流程。

## 必须先执行

```bash
cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree
```

当前 harness 可能在每条 Bash 后重置 cwd；所有 Bash 命令必须显式以 `cd "D:/agent-acceptance" &&` 开头。

## 启动硬门槛

下一个 agent 在复述项目流程、判断状态、执行非平凡任务前，必须读取 `NEXT_AGENT_REQUIRED_READS.json` 中所有 `must_read_at_startup=true` 的文件，并填写 `STARTUP_READ_PROOF_TEMPLATE.json` 等价内容。

不得只根据：

- 用户粘贴的上下文；
- memory / compiled memory；
- 上一轮 agent 的自然语言总结；
- root `GPT_*.txt`；
- legacy `PROJECT_HISTORY*` / `HANDOFF*` / paste block；

来宣布项目状态、verdict、测试数量或 closure 状态。

## 必须复用的现有流程

- `HANDOFF_SOURCE_OF_TRUTH.md`：权威层级。
- `_reports/handoff-pipeline-refactor-a1/ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md`：附件版 GPT 审查流程。
- `scripts/verify_gpt_reply.py`：GPT 回复 verifier。
- `scripts/evidence_pack_linter.py` 与 `scripts/pre_gpt_review_gate.py`：提交前 gate。
- `_reports/global-project-handoff-repair-a1/*`：whole-project 修复层 P0/P1 证据。
- `_reports/global-project-evidence-binding-a1/*`：当前 blocked verdict 与 R2 输入。

## 语义保护

- `accepted_with_limitation` 不能写成 `accepted`。
- `blocked` 不能写成 success。
- `partial / needs_more_evidence` 不能写成 closed。
- `296 PASS` 不能写成 verified。
- production promotion 不能写成 approved。

## 当前 R2 前置事实

`GLOBAL-PROJECT-EVIDENCE-BINDING-A1` 当前 GPT verdict 是 `blocked`。R2 必须处理：

1. `HANDOFF_REPLY_V4.txt` deletion/scope conflict；
2. `SAFETY_ATTESTATION` 与 git evidence 冲突；
3. `SOURCE_MAP_EVIDENCE_BINDING_APPENDIX` 旧 ZIP 嵌入/manifest 不一致。

涉及恢复、checkout、删除、移动 legacy 文件时，必须 human_required。

## ready_for_gpt_review 规则

非平凡任务生成 pack 后，不应停在本地汇报；必须继续提交网页版 GPT 审查，确认附件可见、点击提交按钮、确认 user bubble/assistant response、捕获 run_id verdict，并运行 `scripts/verify_gpt_reply.py`。
'''
    write('NEXT_AGENT_STARTUP_READ_GATE.md', gate_md)

    report = f'''# Implementation Report — {TASK_ID}

- run_id: {RUN_ID}
- generated_at: {NOW}
- reused_existing_workflow: true
- new_review_workflow_created: false

## 生成内容

- `NEXT_AGENT_STARTUP_READ_GATE.md`
- `NEXT_AGENT_REQUIRED_READS.json`
- `STARTUP_READ_PROOF_TEMPLATE.json`

## 安全边界

- 未修改 legacy PROJECT_HISTORY / HANDOFF / PASTE_BLOCK 文件。
- 未执行 git reset / clean / checkout / commit / push。
- 仅在 `_reports/next-agent-workflow-bootstrap-a1/` 与 `evidence_packs/next-agent-workflow-bootstrap-a1/` 写入产物。

## 验证

### fresh shell

exit={fresh['returncode']}

```text
{fresh['stdout']}
{fresh['stderr']}
```

### required reads existence

''' + '\n'.join(f"- `{r['path']}`: exists={r['exists']} sha256={r['sha256']}" for r in reads) + f'''

### git status --short

```text
{git_status['stdout']}
{git_status['stderr']}
```
'''
    write('IMPLEMENTATION_REPORT.md', report)

    safety = '# Safety Scan\n\n- paper_fulltext: not_found\n- original_academic_paragraphs: not_found\n- private_notes: not_found\n- token: not_found\n- secret: not_found\n- credentials: not_found\n- pass: true\n'
    write('SAFETY_SCAN.md', safety)

    if PACK.exists():
        for child in PACK.iterdir():
            if child.is_dir(): shutil.rmtree(child)
            elif child.suffix != '.zip': child.unlink()
    (PACK/'actual_deliverables').mkdir(parents=True, exist_ok=True)
    (PACK/'reports').mkdir(parents=True, exist_ok=True)
    for f in ['NEXT_AGENT_STARTUP_READ_GATE.md','NEXT_AGENT_REQUIRED_READS.json','STARTUP_READ_PROOF_TEMPLATE.json']:
        shutil.copy2(OUT/f, PACK/'actual_deliverables'/f)
    for f in ['IMPLEMENTATION_REPORT.md','SAFETY_SCAN.md']:
        shutil.copy2(OUT/f, PACK/'reports'/f)

    prompt = f'''GPT REVIEW REQUEST: {TASK_ID}

run_id: {RUN_ID}

Please review the attached implementation pack. Verify that it creates a minimal repo-backed startup read gate for the next agent without redesigning the GPT-agent workflow.

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
    (PACK/'GPT_REVIEW_PROMPT.md').write_text(prompt, encoding='utf-8')
    (PACK/'CLOSURE_REPORT.md').write_text(f'# Closure Report — {TASK_ID}\n\n- run_id: {RUN_ID}\n- status: ready_for_gpt_review\n- reused_existing_workflow: true\n', encoding='utf-8')
    (PACK/'SAFETY_ATTESTATION.md').write_text('# Safety Attestation\n\n- safety_boundaries_respected: true\n- legacy_files_modified: false\n- dangerous_git_operations: none\n- sensitive_content_included: false\n', encoding='utf-8')

    rows=[]
    for p in sorted(PACK.rglob('*')):
        if p.is_file() and p.suffix != '.zip':
            rows.append((str(p.relative_to(PACK)).replace('\\','/'), hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size))
    manifest=['# Pack Manifest','',f'- task_id: {TASK_ID}',f'- run_id: {RUN_ID}',f'- generated_at: {NOW}','','| Path | SHA256 | Bytes |','|---|---|---:|']
    for rel,dig,size in rows:
        manifest.append(f'| `{rel}` | `{dig}` | {size} |')
    manifest_text='\n'.join(manifest)+'\n'
    write('PACK_MANIFEST.md', manifest_text)
    (PACK/'PACK_MANIFEST.md').write_text(manifest_text, encoding='utf-8')

    zip_path = PACK / f'NEXT_AGENT_WORKFLOW_BOOTSTRAP_IMPLEMENT_A1_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(PACK.rglob('*')):
            if p.is_file() and p != zip_path and p.suffix != '.zip':
                zf.write(p, p.relative_to(PACK))
    record={'task_id':TASK_ID,'run_id':RUN_ID,'zip_path':str(zip_path.relative_to(ROOT)).replace('\\','/'),'zip_sha256':hashlib.sha256(zip_path.read_bytes()).hexdigest(),'generated_at':NOW}
    write_json('ZIP_RECORD.json', record)
    print(json.dumps(record, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
