"""Minimal Memory Compiler — extracts lessons from GPT_REVIEW_RESULT and WORKFLOW_AUDIT_LEDGER.

No raw transcript, no real paper, no external API.
Generates: memory/daily/YYYY-MM-DD.md, memory/knowledge/index.md
"""
import sys
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = ROOT / "memory"
DAILY_DIR = MEMORY_DIR / "daily"
KNOWLEDGE_DIR = MEMORY_DIR / "knowledge"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_audit_ledger() -> Optional[Path]:
    p = ROOT / "docs" / "WORKFLOW_AUDIT_LEDGER.yaml"
    return p if p.exists() else None


def find_gpt_review_results() -> list[Path]:
    results = []
    for d in (ROOT / "evidence_packs").iterdir():
        if d.is_dir():
            for name in ["GPT_REPLY.txt", "GPT_REPLY_R2.txt", "GPT_REPLY_R3.txt"]:
                p = d / name
                if p.exists():
                    results.append(p)
    return results


def extract_lessons_from_review(text: str, review_id: str, task_id: str) -> list[dict]:
    """Extract lessons from a GPT review text. Simple keyword-based extraction."""
    lessons = []
    text_lower = text.lower()

    # Pattern: summary-only pack
    if "summary-only" in text_lower or "summary only" in text_lower:
        lessons.append({
            "memory_type": "教训",
            "lesson": "summary-only evidence pack 被 GPT 驳回；必须包含实际产物文件，不得只有 closure report/attestation/manifest",
            "source_review_run_id": review_id,
            "source_task_id": task_id,
        })

    # Pattern: ready_for_review as closed
    if "ready_for_review" in text_lower and ("closed" in text_lower or "accepted" in text_lower):
        lessons.append({
            "memory_type": "教训",
            "lesson": "ready_for_review 不等于 closed；closed 必须有 GPT accepted + ledger 记录",
            "source_review_run_id": review_id,
            "source_task_id": task_id,
        })

    # Pattern: manifest mismatch
    if "manifest" in text_lower and ("不匹配" in text_lower or "mismatch" in text_lower or "不一致" in text_lower):
        lessons.append({
            "memory_type": "踩坑记录",
            "lesson": "manifest 与 ZIP 双向一致性是 Evidence-First 的基础要求；不一致会导致 GPT 判 blocked",
            "source_review_run_id": review_id,
            "source_task_id": task_id,
        })

    # Pattern: blocked after multiple rounds
    if "blocked" in text_lower and ("round" in text_lower or "轮" in text_lower or "iteration" in text_lower):
        lessons.append({
            "memory_type": "失败模式",
            "lesson": "多轮迭代后仍被 GPT 判 blocked，说明 pre-submission self-verify 未生效",
            "source_review_run_id": review_id,
            "source_task_id": task_id,
        })

    # Pattern: accepted
    if "overall_judgment: accepted" in text_lower:
        lessons.append({
            "memory_type": "工作流规则",
            "lesson": f"任务 {task_id} 经 GPT 审查 accepted，验收流程完整闭合",
            "source_review_run_id": review_id,
            "source_task_id": task_id,
        })

    return lessons


def extract_lessons_from_ledger(ledger_path: Path) -> list[dict]:
    """Extract lessons from WORKFLOW_AUDIT_LEDGER.yaml."""
    lessons = []
    if not ledger_path or not ledger_path.exists():
        return lessons

    text = ledger_path.read_text(encoding="utf-8")
    text_lower = text.lower()

    # Systemic defects
    if "sd-01" in text_lower or "summary_only" in text_lower.replace("-", ""):
        if "open" in text_lower:
            lessons.append({
                "memory_type": "失败模式",
                "lesson": "系统性缺陷 SD-01（summary-only evidence pack）仍处于 open 状态，需通过 gate 自动化阻断",
                "source_task_id": "WORKFLOW-HARDENING-A1",
            })

    if "sd-02" in text_lower:
        if "open" in text_lower:
            lessons.append({
                "memory_type": "失败模式",
                "lesson": "系统性缺陷 SD-02（ready_for_review 被当作 closed）仍处于 open 状态，需固化状态转移规则",
                "source_task_id": "WORKFLOW-HARDENING-A1",
            })

    # Closed tasks
    for line in text.split("\n"):
        if "status: closed" in line.lower():
            lessons.append({
                "memory_type": "工作流规则",
                "lesson": "识别到已闭合任务，可作为后续 memory 编译的数据来源",
                "source_task_id": "WORKFLOW_AUDIT_LEDGER",
            })

    return lessons


def compile_daily_log(date_str: str, lessons: list[dict]) -> str:
    """Generate daily memory log using the template."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    log = f"""# 每日记忆日志 — {date_str}

> 记忆类型: 每日日志
> 隐私分类: 默认私有
> 合成数据标记: 是
> 生成时间: {now}
> 生成方式: memory_compiler.py（自动化编译）

## 来源审查记录

"""
    seen_reviews = set()
    for l in lessons:
        rid = l.get("source_review_run_id", "")
        if rid and rid not in seen_reviews:
            seen_reviews.add(rid)
            log += f"| {rid} | {l.get('source_task_id','')} | agent-acceptance | 见GPT_REPLY | 是 |\n"

    log += "\n## 观察到的教训\n\n| 教训ID | 教训内容 | 来源审查ID | 是否编译为知识 |\n|--------|---------|-----------|----------------|\n"
    for i, l in enumerate(lessons):
        lid = f"MEM-A2-{i+1:03d}"
        log += f"| {lid} | {l['lesson']} | {l.get('source_review_run_id','WORKFLOW_AUDIT_LEDGER')} | 是 |\n"

    log += "\n## 重复失败模式\n\n"
    patterns = [l for l in lessons if l["memory_type"] == "失败模式"]
    if patterns:
        log += "| 模式 | 是否重复 | 关联任务 | 是否需要 gate 更新 |\n|------|---------|---------|-------------------|\n"
        for p in patterns:
            log += f"| {p['lesson'][:50]}... | 待确认 | {p.get('source_task_id','')} | 待评估 |\n"
    else:
        log += "无\n"

    log += f"""
## 经验总结

本日编译了 {len(lessons)} 条教训，来自 {len(seen_reviews)} 个审查来源。
主要发现：{lessons[0]['lesson'][:80] if lessons else '无特别发现'}...。

## 下一步计划

基于当前编译结果，建议：
1. 对重复 failure pattern 进行 gate 自动化加固
2. 将已闭合任务的经验编译为 knowledge article

## 脱敏说明

- 是否接触私密内容: 否
- 是否存储私密内容: 否
- 脱敏处理: 所有内容来自已脱敏的 GPT review result 和 audit ledger
"""
    return log


def compile_index(lessons: list[dict]) -> str:
    """Generate memory knowledge index."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    idx = f"""# 记忆索引

> 最后更新: {now}
> 条目总数: {len(lessons)}
> 生成方式: memory_compiler.py
> 隐私分类: 默认私有

## 概念条目

| 记忆ID | 标题 | 记忆类型 | 状态 |
|--------|------|---------|------|
"""
    for i, l in enumerate(lessons):
        lid = f"MEM-A2-{i+1:03d}"
        idx += f"| {lid} | {l['lesson'][:40]}... | {l['memory_type']} | 活跃 |\n"

    idx += """

## 失败模式

| 记忆ID | 模式 | 出现次数 | 关联 gate | 状态 |
|--------|------|---------|----------|------|
"""
    patterns = [l for l in lessons if l["memory_type"] == "失败模式"]
    for p in patterns:
        idx += f"| — | {p['lesson'][:50]}... | 待统计 | 待评估 | 活跃 |\n"

    idx += """

## 踩坑记录

| 记忆ID | 坑 | 关联任务 |
|--------|-----|---------|
"""
    gotchas = [l for l in lessons if l["memory_type"] == "踩坑记录"]
    for g in gotchas:
        idx += f"| — | {g['lesson'][:50]}... | {g.get('source_task_id','')} |\n"

    idx += f"""

## 下一步总体计划

Memory Compiler 原型已运行。当前编译了 {len(lessons)} 条记录。
后续应增加：自动检测重复模式、关联 gate 更新建议、与 WORKFLOW_AUDIT_LEDGER 联动。
"""
    return idx


def main():
    print("=== Memory Compiler ===\n")

    # 1. Find sources
    ledger = find_audit_ledger()
    reviews = find_gpt_review_results()
    print(f"Sources: ledger={'found' if ledger else 'none'}, reviews={len(reviews)}")

    # 2. Extract lessons
    all_lessons = []

    if ledger:
        ledger_lessons = extract_lessons_from_ledger(ledger)
        all_lessons.extend(ledger_lessons)
        print(f"  Ledger lessons: {len(ledger_lessons)}")

    for rp in reviews:
        text = rp.read_text(encoding="utf-8")
        review_id = rp.parent.name.replace("evidence_packs/", "").replace("\\", "-")
        task_id = rp.parent.name.split("-")[0] if "-" in rp.parent.name else rp.parent.name
        review_lessons = extract_lessons_from_review(text, review_id, task_id)
        all_lessons.extend(review_lessons)
        print(f"  {rp.parent.name}: {len(review_lessons)} lessons")

    print(f"\nTotal lessons: {len(all_lessons)}")

    if not all_lessons:
        print("No lessons found. Nothing to compile.")
        return 1

    # 3. Generate daily log
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    daily_path = DAILY_DIR / f"{today}.md"
    daily_content = compile_daily_log(today, all_lessons)
    daily_path.write_text(daily_content, encoding="utf-8")
    print(f"Daily log: {daily_path} ({len(daily_content)} chars)")

    # 4. Generate index
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    index_path = KNOWLEDGE_DIR / "index.md"
    index_content = compile_index(all_lessons)
    index_path.write_text(index_content, encoding="utf-8")
    print(f"Index: {index_path} ({len(index_content)} chars)")

    # 5. Output result
    result = {
        "result": "pass",
        "sources_scanned": {"ledger": ledger is not None, "reviews_count": len(reviews)},
        "lessons_extracted": len(all_lessons),
        "daily_log": str(daily_path),
        "index": str(index_path),
        "no_raw_transcript": True,
        "no_real_paper": True,
        "no_external_api": True,
    }
    print(f"\nResult: {result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
