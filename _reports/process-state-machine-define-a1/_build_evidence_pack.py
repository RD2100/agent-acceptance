#!/usr/bin/env python3
"""Build evidence pack for PROCESS-STATE-MACHINE-DEFINE-A1 and generate GPT review prompt."""

import hashlib
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/agent-acceptance')
REPORT_DIR = ROOT / '_reports/process-state-machine-define-a1'
PACK_DIR = ROOT / 'evidence_packs/process-state-machine-define-a1'
TIMESTAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
RUN_ID = f'PROCESS_STATE_MACHINE_DEFINE_A1_REVIEW_{TIMESTAMP}_RD'
TASK_ID = 'PROCESS-STATE-MACHINE-DEFINE-A1'
ZIP_NAME = f'PROCESS_STATE_MACHINE_DEFINE_A1_{TIMESTAMP}.zip'

# Files to include in evidence pack (relative to REPORT_DIR)
DELIVERABLES = [
    'PROCESS_STATE_MACHINE.md',
    'PROCESS_STATE_MACHINE.json',
    'CHANGED_FILES_SCHEMA.json',
    'changed_files_utils.py',
    'EXECUTION_REPORT.md',
    '_validate_deliverables.py',
]

# Also include reference files from hardening plan
REFERENCES = [
    (ROOT / '_reports/handoff-workflow-hardening-plan-a1/HANDOFF_WORKFLOW_HARDENING_PLAN.md', 'HANDOFF_WORKFLOW_HARDENING_PLAN.md'),
    (ROOT / '_reports/handoff-workflow-hardening-plan-a1/GPT_REVIEW_RECORD_R2.json', 'AUTHORIZATION_SOURCE_GPT_REVIEW_RECORD_R2.json'),
    (ROOT / '_reports/handoff-workflow-hardening-plan-a1/GPT_REVIEW_RESULT_R2.txt', 'AUTHORIZATION_SOURCE_GPT_REVIEW_RESULT_R2.txt'),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def build_pack():
    # Clean and recreate pack dir
    if PACK_DIR.exists():
        shutil.rmtree(PACK_DIR)
    PACK_DIR.mkdir(parents=True)

    manifest_entries = []

    # Copy deliverables
    for filename in DELIVERABLES:
        src = REPORT_DIR / filename
        dst = PACK_DIR / filename
        if not src.exists():
            print(f'WARNING: {filename} not found at {src}')
            continue
        shutil.copy2(src, dst)
        sha = sha256_file(dst)
        size = dst.stat().st_size
        manifest_entries.append({
            'file': filename,
            'sha256': sha,
            'size': size,
            'source': 'deliverable',
        })
        print(f'  Packed: {filename} ({size} bytes, sha256={sha[:16]}...)')

    # Copy references
    for src, dest_name in REFERENCES:
        dst = PACK_DIR / dest_name
        if not src.exists():
            print(f'WARNING: Reference file not found: {src}')
            continue
        shutil.copy2(src, dst)
        sha = sha256_file(dst)
        size = dst.stat().st_size
        manifest_entries.append({
            'file': dest_name,
            'sha256': sha,
            'size': size,
            'source': 'reference',
        })
        print(f'  Packed ref: {dest_name} ({size} bytes, sha256={sha[:16]}...)')

    # Generate PACK_MANIFEST.md
    manifest_lines = [
        '# PACK MANIFEST — PROCESS-STATE-MACHINE-DEFINE-A1',
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
    REPORT_DIR_COPY = REPORT_DIR / 'GPT_REVIEW_PROMPT.md'
    REPORT_DIR_COPY.write_text(prompt, encoding='utf-8')
    print(f'  Prompt written: GPT_REVIEW_PROMPT.md')

    return zip_path, RUN_ID


def generate_prompt(zip_size, zip_sha, manifest_entries):
    file_list = '\n'.join(f'- `{e["file"]}` ({e["size"]} bytes)' for e in manifest_entries)

    return f"""# GPT 审查请求 — PROCESS-STATE-MACHINE-DEFINE-A1

## 审查基本信息

- **task_id**: `PROCESS-STATE-MACHINE-DEFINE-A1`
- **run_id**: `{RUN_ID}`
- **提交时间**: `{datetime.now(timezone.utc).isoformat()}`
- **evidence pack**: `{ZIP_NAME}` ({zip_size} bytes, SHA-256: `{zip_sha}`)
- **授权来源**: `HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2` verdict `accepted_with_limitation`, GPT 指示 `execute_immediately: 是`

## 审查目标

本任务实现了硬化计划（HANDOFF_WORKFLOW_HARDENING_PLAN.md）中两个 P0 级并行项：
1. **P0-1: PROCESS_STATE_MACHINE** — GPT-Agent 交接流程的正式状态机定义
2. **P0-2: CHANGED_FILES_SCHEMA** — 标准化 pre/post 文件变更证明格式

## Evidence Pack 内容

{file_list}

## 审查要求（7 项）

请逐项审查并给出评价：

### 1. 状态机完整性
PROCESS_STATE_MACHINE.md/json 是否完整定义了 8 个状态（draft, gate_passing, gpt_reviewing, accepted, accepted_with_limitation, blocked, human_required, closed）和 10 个转换（T01-T10）？

### 2. 不变式正确性
8 个不变式（INV-01 至 INV-08）是否覆盖了所有关键约束？特别是：closed 终态、verify_gpt_reply.py 强制验证、blocked 唯一回退路径、审查轮次限制。

### 3. 禁止转换覆盖
forbidden_transitions 列表是否完整覆盖了所有非法转换路径？是否有遗漏？

### 4. CHANGED_FILES_SCHEMA 合规性
CHANGED_FILES_SCHEMA.json 是否符合 JSON Schema draft 2020-12？条件验证（allOf + if/then）是否正确处理了 added/deleted/renamed 类型的 null 约束？

### 5. 工具函数实用性
changed_files_utils.py 是否提供了完整的生成/验证/摘要功能？CLI 接口是否合理？

### 6. 与硬化计划的一致性
产出物是否与 HANDOFF_WORKFLOW_HARDENING_PLAN.md 第五章 5.1/5.2 节的规格保持一致？是否遗漏了任何要求？

### 7. next_task_authorization 机制
状态机中的 authorization_mechanism 定义是否完整？是否解决了硬化计划 Q7 提出的授权链断裂问题？

## 输出格式要求

请严格按以下格式输出审查结果：

```
run_id: {RUN_ID}
task_id: PROCESS-STATE-MACHINE-DEFINE-A1
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
- 如果判定为 accepted 或 accepted_with_limitation，必须在 next_task_authorization 中指定下一个任务
- END_OF_GPT_RESPONSE 标记必须出现在回复末尾
"""


if __name__ == '__main__':
    zip_path, run_id = build_pack()
    print(f'\nDone. Run ID: {run_id}')
    print(f'ZIP: {zip_path}')
    print(f'Next: submit via Playwright CDP to continuation conversation')
