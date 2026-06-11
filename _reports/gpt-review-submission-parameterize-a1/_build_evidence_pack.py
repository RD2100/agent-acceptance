#!/usr/bin/env python3
"""Build evidence pack for GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1 and generate GPT review prompt."""

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/agent-acceptance')
TASK_ID = 'GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1'
TIMESTAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
RUN_ID = f'GPT_REVIEW_SUBMISSION_PARAMETERIZE_A1_REVIEW_{TIMESTAMP}_RD'

REPORT_DIR = ROOT / '_reports/gpt-review-submission-parameterize-a1'
PACK_DIR = ROOT / 'evidence_packs/gpt-review-submission-parameterize-a1'
ZIP_NAME = f'GPT_REVIEW_SUBMISSION_PARAMETERIZE_A1_{TIMESTAMP}.zip'

# Deliverables from report dir
DELIVERABLES = [
    ('EXECUTION_REPORT.md', REPORT_DIR / 'EXECUTION_REPORT.md'),
    ('gpt_submit_usage.md', REPORT_DIR / 'gpt_submit_usage.md'),
    ('_validate_parameterize.py', REPORT_DIR / '_validate_parameterize.py'),
    ('GPT_REVIEW_SUBMISSION_STATUS.json', REPORT_DIR / 'GPT_REVIEW_SUBMISSION_STATUS.json'),
]

# The parameterized script itself
SCRIPT_FILE = ROOT / 'scripts/gpt_new_chat_attachment_submit.py'

# References
REFERENCES = [
    (ROOT / '_reports/handoff-workflow-hardening-plan-a1/HANDOFF_WORKFLOW_HARDENING_PLAN.md',
     'HANDOFF_WORKFLOW_HARDENING_PLAN.md'),
    (ROOT / '_reports/process-state-machine-define-a1/GPT_REVIEW_RECORD_R1.json',
     'AUTHORIZATION_SOURCE_PSM_DEFINE_A1_R1.json'),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def build_pack():
    if PACK_DIR.exists():
        shutil.rmtree(PACK_DIR)
    PACK_DIR.mkdir(parents=True)

    manifest_entries = []

    # Copy the parameterized script
    dst = PACK_DIR / 'gpt_new_chat_attachment_submit.py'
    shutil.copy2(SCRIPT_FILE, dst)
    sha = sha256_file(dst)
    size = dst.stat().st_size
    manifest_entries.append({'file': 'gpt_new_chat_attachment_submit.py', 'sha256': sha, 'size': size, 'source': 'deliverable'})
    print(f'  Packed: gpt_new_chat_attachment_submit.py ({size} bytes)')

    # Copy deliverables
    for name, src in DELIVERABLES:
        if not src.exists():
            print(f'  WARNING: {name} not found at {src}')
            continue
        dst = PACK_DIR / name
        shutil.copy2(src, dst)
        sha = sha256_file(dst)
        size = dst.stat().st_size
        manifest_entries.append({'file': name, 'sha256': sha, 'size': size, 'source': 'deliverable'})
        print(f'  Packed: {name} ({size} bytes)')

    # Copy references
    for src, dest_name in REFERENCES:
        if not src.exists():
            print(f'  WARNING: Reference not found: {src}')
            continue
        dst = PACK_DIR / dest_name
        shutil.copy2(src, dst)
        sha = sha256_file(dst)
        size = dst.stat().st_size
        manifest_entries.append({'file': dest_name, 'sha256': sha, 'size': size, 'source': 'reference'})
        print(f'  Packed ref: {dest_name} ({size} bytes)')

    # Generate PACK_MANIFEST.md
    manifest_lines = [
        f'# PACK MANIFEST — {TASK_ID}',
        '',
        f'- **task_id**: `{TASK_ID}`',
        f'- **run_id**: `{RUN_ID}`',
        f'- **generated_at**: `{datetime.now(timezone.utc).isoformat()}`',
        f'- **total_files**: {len(manifest_entries)}',
        f'- **total_size**: {sum(e["size"] for e in manifest_entries)} bytes',
        '',
        '## File Listing',
        '',
        '| File | SHA-256 | Size | Source |',
        '|------|---------|------|--------|',
    ]
    for entry in manifest_entries:
        manifest_lines.append(f'| `{entry["file"]}` | `{entry["sha256"]}` | {entry["size"]} | {entry["source"]} |')
    manifest_text = '\n'.join(manifest_lines) + '\n'
    (PACK_DIR / 'PACK_MANIFEST.md').write_text(manifest_text, encoding='utf-8')
    print(f'  Manifest written: PACK_MANIFEST.md')

    # Create ZIP
    zip_path = PACK_DIR / ZIP_NAME
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for entry in manifest_entries:
            fp = PACK_DIR / entry['file']
            if fp.exists():
                zf.write(fp, entry['file'])
        zf.write(PACK_DIR / 'PACK_MANIFEST.md', 'PACK_MANIFEST.md')

    zip_size = zip_path.stat().st_size
    zip_sha = sha256_file(zip_path)
    print(f'\n  ZIP created: {ZIP_NAME}')
    print(f'  Size: {zip_size} bytes')
    print(f'  SHA-256: {zip_sha}')

    # Save run_id
    run_id_path = REPORT_DIR / 'R1_RUN_ID.txt'
    run_id_path.write_text(RUN_ID + '\n', encoding='utf-8')

    # Generate GPT review prompt
    prompt = generate_prompt(zip_size, zip_sha, manifest_entries)
    prompt_path = PACK_DIR / 'GPT_REVIEW_PROMPT.md'
    prompt_path.write_text(prompt, encoding='utf-8')
    (REPORT_DIR / 'GPT_REVIEW_PROMPT.md').write_text(prompt, encoding='utf-8')
    print(f'  Prompt written: GPT_REVIEW_PROMPT.md')

    return zip_path, RUN_ID, zip_sha


def generate_prompt(zip_size, zip_sha, manifest_entries):
    file_list = '\n'.join(f'- `{e["file"]}` ({e["size"]} bytes)' for e in manifest_entries)

    return f"""# GPT 审查请求 — GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1

## 审查基本信息

- **task_id**: `{TASK_ID}`
- **run_id**: `{RUN_ID}`
- **提交时间**: `{datetime.now(timezone.utc).isoformat()}`
- **evidence pack**: `{ZIP_NAME}` ({zip_size} bytes, SHA-256: `{zip_sha}`)
- **授权来源**: `PROCESS-STATE-MACHINE-DEFINE-A1` verdict `accepted_with_limitation`, next_task: `GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1`, execute_immediately: 是

## 审查目标

本任务实现了硬化计划（HANDOFF_WORKFLOW_HARDENING_PLAN.md）中的 P0-3 项：
- **将 `gpt_new_chat_attachment_submit.py` 从硬编码委托脚本改造为完全参数化的 GPT 审查提交器**

## Evidence Pack 内容

{file_list}

## 审查要求（7 项）

请逐项审查并给出评价：

### 1. 参数化完整性
`gpt_new_chat_attachment_submit.py` 是否支持硬化计划 section 5.3 定义的所有 CLI 参数（--task-id, --pack-path, --run-id-path, --output-path, --prompt-template, --dry-run, --timeout）？

### 2. 模板变量替换
是否支持 {{TASK_ID}}、{{RUN_ID}}、{{PACK_MANIFEST}}、{{TIMESTAMP}} 四个模板变量的正确替换？

### 3. 双场景支持
是否正确区分 Scenario A（延续性对话，指定 --chat-url）和 Scenario B（新对话）？页面查找/打开逻辑是否正确？

### 4. Hardened capture 逻辑
是否集成了 before_assistant_count baseline + run_id authoritative matching？capture reconciliation 是否每次提交自动生成？

### 5. Dry-run 模式
--dry-run 模式是否正确工作（仅生成 prompt 和配置信息，不实际提交）？

### 6. 错误处理
缺失必需参数、文件不存在、模板不存在等边界情况是否有适当处理？

### 7. 使用说明文档
`gpt_submit_usage.md` 是否清晰描述了所有参数、场景和使用示例？

## 输出格式要求

请严格按以下格式输出审查结果：

```
run_id: {RUN_ID}
task_id: GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1
evidence_pack_reviewed: true
attachment_reviewed: true

overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified

blocking_issues:
- (如有 blocking 问题，列出；如无，写 "none")

required_fixes:
- (如有必须修复项，列出；如无，写 "none")

limitations:
- (如有已知限制，列出；如无，写 "none")

next_task_authorization:
  task_id: (下一个任务的 ID)
  authorized: 已授权 | 未授权
  execute_immediately: 是 | 否
  ask_before_starting: 是 | 否

END_OF_GPT_RESPONSE
```

注意：
- 请使用中文回答审查内容部分，但输出格式字段名保持英文
- overall_judgment 必须使用以下四个合法值之一：accepted, accepted_with_limitation, blocked, review_unverified
- END_OF_GPT_RESPONSE 标记必须出现在回复末尾
"""


if __name__ == '__main__':
    zip_path, run_id, zip_sha = build_pack()
    print(f'\nDone. Run ID: {run_id}')
    print(f'ZIP: {zip_path}')
