#!/usr/bin/env python3
"""Rebuild evidence pack for R2 with fixed files."""
import hashlib, os, shutil
from pathlib import Path
from datetime import datetime

ROOT = Path('D:/agent-acceptance')
REPORT_DIR = ROOT / '_reports/handoff-workflow-hardening-plan-a1'
PACK_DIR = ROOT / 'evidence_packs/handoff-workflow-hardening-plan-a1'

# 1. Copy updated files to evidence pack
copies = [
    (REPORT_DIR / 'HANDOFF_WORKFLOW_HARDENING_PLAN.md', PACK_DIR / 'actual_deliverables/HANDOFF_WORKFLOW_HARDENING_PLAN.md'),
    (REPORT_DIR / 'HARDENING_GAP_ANALYSIS.json', PACK_DIR / 'actual_deliverables/HARDENING_GAP_ANALYSIS.json'),
    (REPORT_DIR / 'GPT_CAPTURE_ADVICE.txt', PACK_DIR / 'reports/GPT_CAPTURE_ADVICE.txt'),
    (REPORT_DIR / 'GPT_REVIEW_RECORD.json', PACK_DIR / 'reports/GPT_REVIEW_RECORD_R1.json'),
    (REPORT_DIR / 'GPT_REVIEW_RESULT.txt', PACK_DIR / 'reports/GPT_REVIEW_RESULT_R1.txt'),
    (REPORT_DIR / 'VERIFY_GPT_REPLY_OUTPUT.txt', PACK_DIR / 'reports/VERIFY_GPT_REPLY_OUTPUT_R1.txt'),
]
for src, dst in copies:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src), str(dst))
        print(f'Copied: {src.name} -> {dst.relative_to(PACK_DIR)}')

# 2. Rebuild PACK_MANIFEST.md
lines = [
    '# Pack Manifest -- HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2',
    '',
    '- task_id: HANDOFF-WORKFLOW-HARDENING-PLAN-A1',
    '- round: R2',
    f'- generated_at: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S+00:00")}',
    '- note: R2 fixes 4 blocked issues from R1 GPT review. Self-hash omitted.',
    '',
    '| Path | SHA256 | Bytes |',
    '|---|---|---:|',
]

for dirpath, dirnames, filenames in sorted(os.walk(str(PACK_DIR))):
    dirnames.sort()
    for fname in sorted(filenames):
        fpath = Path(dirpath) / fname
        if fpath.name == 'PACK_MANIFEST.md' or fpath.suffix == '.zip':
            continue
        rel = str(fpath.relative_to(PACK_DIR)).replace('\\', '/')
        data = fpath.read_bytes()
        h = hashlib.sha256(data).hexdigest()
        lines.append(f'| `{rel}` | `{h}` | {len(data)} |')

manifest_text = '\n'.join(lines) + '\n'
(PACK_DIR / 'PACK_MANIFEST.md').write_text(manifest_text, encoding='utf-8')
print(f'Manifest updated: {(PACK_DIR / "PACK_MANIFEST.md").stat().st_size} bytes')

# Copy updated manifest to reports
shutil.copy2(str(PACK_DIR / 'PACK_MANIFEST.md'), str(REPORT_DIR / 'PACK_MANIFEST.md'))
print('Report manifest copied')

# 3. Create R2 ZIP
import zipfile
timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%S')
zip_name = f'HANDOFF_WORKFLOW_HARDENING_PLAN_A1_R2_{timestamp}.zip'
zip_path = PACK_DIR / zip_name

# Remove old R1 ZIP if exists
for old_zip in PACK_DIR.glob('*.zip'):
    old_zip.unlink()
    print(f'Removed old ZIP: {old_zip.name}')

with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
    for dirpath, dirnames, filenames in sorted(os.walk(str(PACK_DIR))):
        dirnames.sort()
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            if fpath.suffix == '.zip':
                continue
            arcname = str(fpath.relative_to(PACK_DIR))
            zf.write(str(fpath), arcname)

zip_size = zip_path.stat().st_size
zip_hash = hashlib.sha256(zip_path.read_bytes()).hexdigest()
print(f'R2 ZIP created: {zip_name} ({zip_size} bytes, SHA256: {zip_hash})')

# 4. Create R2 GPT review prompt
run_id_r2 = f'HANDOFF_WORKFLOW_HARDENING_PLAN_A1_R2_REVIEW_{timestamp}_RD'
prompt = f"""GPT REVIEW REQUEST: HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2

run_id: {run_id_r2}

请审查附件 R2 evidence pack。这是对 R1 blocked verdict 的修复提交。

R1 blocked 原因及本次修复：

1. source-of-truth 层级表述错误（P0/P1/P2/P3 定义不符合 HANDOFF_SOURCE_OF_TRUTH.md）
   → 已修正为与 HANDOFF_SOURCE_OF_TRUTH.md 一致的定义

2. gpt_new_chat_attachment_submit.py 能力描述与 HARDENING_GAP_ANALYSIS.json 不一致
   → 已统一描述：明确脚本当前为 pointer_only + 实际实现功能 + 参数化限制

3. startup proof 未纳入 evidence pack
   → 已将 STARTUP_READ_PROOF 和 STARTUP_READ_SUMMARY 纳入 pack 和 manifest

4. HANDOFF_REPLY_V4.txt 表述不够明确
   → 已明确其仍为 tracked_deleted_human_required，不得自动 git restore

新增内容（基于 R1 审查中发现的 capture 误取问题）：
- 新增 GAP-010（capture_mechanism_hardening）
- 新增附录 C：R1 审查经验教训
- 新增 GPT_CAPTURE_ADVICE.txt：GPT 关于 capture 固化的详细建议
- 核心原则：在延续性对话中，last assistant is not authoritative；target run_id match is authoritative

请重点判断：
1. R1 的 4 个 blocking issues 是否已全部修复
2. 新增的 capture 经验教训是否合理
3. 整体计划是否可接受（可附 limitation）

如果附件不可检查，请返回 review_unverified。

请只返回：

run_id: {run_id_r2}
task_id: HANDOFF-WORKFLOW-HARDENING-PLAN-A1-R2
overall_judgment: accepted | accepted_with_limitation | blocked | review_unverified
evidence_pack_reviewed: true | false
attachment_reviewed: true | false
blocking_issues:
- <问题或 none>
required_fixes:
- <修复或 none>
limitations:
- <限制或 none>
next_task_authorization:
task_id: <下个任务或 none>
authorized: 已授权 | 未授权
execute_immediately: 是 | 否
ask_before_starting: 是 | 否
END_OF_GPT_RESPONSE
"""

prompt_path = PACK_DIR / 'GPT_REVIEW_PROMPT_R2.md'
prompt_path.write_text(prompt, encoding='utf-8')
(REPORT_DIR / 'GPT_REVIEW_PROMPT_R2.md').write_text(prompt, encoding='utf-8')
print(f'R2 prompt created: run_id={run_id_r2}')

# Save run_id for the submit script
run_id_path = REPORT_DIR / 'R2_RUN_ID.txt'
run_id_path.write_text(run_id_r2 + '\n', encoding='utf-8')
print(f'Run ID saved: {run_id_r2}')
