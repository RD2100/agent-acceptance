"""ECS-A2 Gate 0 Review — Round 1: Submit research findings + TaskSpec draft to GPT."""
import asyncio, os, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
CDP_URL = "http://localhost:9222"

MSG = """EVIDENCE-CAPTURE-STANDARD-A2 — Gate 0 研究成果 + TaskSpec 草案复核请求（第1轮）

1. 背景

EVIDENCE-CAPTURE-STANDARD-A1 已完成（commit 20a4aa2, ACCEPTED_WITH_LIMITATION），交付了：
- scripts/build_evidence_pack.py（1264行，8阶段 reusable parameterized builder）
- hooks/pre-commit.governance.ps1 v2.1.0（hook output persistence）
- schemas/agent-runtime/evidence-capture.schema.json
- docs/agent-runtime/evidence-capture-workflow.md

A1 的 limitation：仍是 registered closure 不是 clean workspace；builder 用 git diff base..HEAD 不支持显式 --head；sadp-audit-raw.txt 不含完整原始 stage output。

后续 CONVERSATION-HEALTH-GATE-A3 和 A4 反复暴露 evidence pack 层问题：
- review.yaml / final-report.md / full regression log 缺失
- runtime behavior 仅靠测试模拟，无独立 runtime artifact
- 声称 full regression 但日志不在包里，无法独立验证
- accepted_with_limitation 决策无一致表示

2. Gate 0 三路并行研究发现

**路线A：Builder 分析（build_evidence_pack.py, 1264行）**

10个关键缺口：
G1. 零功能测试覆盖（仅3条静态文本断言于 TestEvidencePackIntegration）
G2. 无 evidence-manifest.json 或机器可读清单
G3. verdict_eligibility 仅嵌套在 conversation_health 块（3个值），无顶层聚合
G4. 顶层 verdict 仅反映 pytest pass/fail（EVIDENCE_COMPLETE/EVIDENCE_COMPLETE_TESTS_FAILED），不反映 evidence 完整性
G5. 无 required/optional/missing 文件分类（evidence_files 列表是扁平字符串列表）
G6. 无 full_regression vs targeted_tests 区分（单一 pytest 调用，-x 模式）
G7. evidence-index.schema.json 存在但 builder 未使用
G8. evidence_pack_linter.py 针对不同 pack 格式（closure-report based）
G9. runtime evidence .txt 文件无标准化 schema（自由格式 # 注释头）
G10. consistency_check.all_files_agree 硬编码为 true（line 685）

builder 8阶段结构：
Phase 1: Gather git data → Phase 2: Run tests → Phase 3: Security checks → Phase 4: Hook log → Phase 5: Generate evidence files (16+ files) → Phase 6: Consistency check → Phase 7: Build ZIP → Phase 8: Summary

review.yaml 当前结构：
- 顶层: verdict, task_id, generated, version, commits, base_commit, head_commit
- evidence_files: 14个硬编码基础文件 + 条件追加
- post_commit_state: modified_tracked, untracked_total, neg_009, secret_scan, session_artifacts
- consistency_check: all_files_agree (hardcoded true), sum_check
- conversation_health: checked, decision, status, verdict_eligibility (eligible|needs_more_evidence)
- startup_read: conversation_health_checked, decision, severity, verdict_impact (none|limitation)

**路线B：现有文档分析**

- evidence-capture-standard.md：不存在
- evidence-pack-review-rules.md：不存在
- evidence-pack-standard.md：存在（9个最低必备文件，9条验证规则，反模式，提交清单）
- evidence-capture-workflow.md：存在（A1交付，Phase A/B 描述）
- universal-agent-workflow-standard.md：Section 3 evidence requirements（10个必备项）
- pre-gpt-review-gate.md：11个必备项（加 ZIP 要求）
- SADP 0.R.2：7个必备文件 + review.yaml 强制 schema（reviewer_id, executor_id, reviewed_inputs, findings[]）

关键发现：4份文档的"必备文件"数量不一致（7/9/10/11）。review.yaml 实际结构与 SADP 0.R.2 强制 schema 严重偏离（缺少 reviewer_id, executor_id, reviewed_inputs, findings[]）。

17个历史 review.yaml 均不符合 SADP 0.R.2 schema，全部使用自定义 verdict 类型（EVIDENCE_COMPLETE 等）而非规定的 pass|blocked|fail|escalate。

**路线C：测试覆盖分析**

- test_build_evidence_pack.py：不存在
- TestEvidencePackIntegration（3个测试）：仅静态文本断言
- 全库 1204 个测试中，evidence-pack-related 约 70 个（跨8个文件）
- 关键测试空白：
  - 无 review.yaml 输出验证
  - 无 verdict_eligibility 测试
  - 无 evidence-manifest 生成测试
  - 无 runtime evidence 格式验证
  - 无 consistency verification 测试
  - 无 ZIP 完整性测试
  - 无 full regression claim 验证

3. 拟定 TaskSpec（ECS-A2）

task_id: EVIDENCE-CAPTURE-STANDARD-A2
title: Evidence Capture Standard — canonical evidence pack contract & builder enforcement
priority: P0

goal:
  创建并强制执行一套规范化的 Evidence Capture Standard，使所有未来 evidence pack
  完整、可审核、schema-aware、抗缺失/过期证据接受。

核心工作范围：
1. 创建 docs/agent-runtime/evidence-capture-standard.md
   - 统一"必备文件"列表（解决 7/9/10/11 不一致）
   - 定义 verdict eligibility 规则（ACCEPTED / ACCEPTED_WITH_LIMITATION / NEEDS_REVISION / REJECTED）
   - 标准化 runtime/negative-path evidence 格式
   - 标准化 full regression 声明要求

2. 创建 docs/agent-runtime/evidence-pack-review-rules.md
   - 整合分散在4份文档中的 review 规则

3. 在 build_evidence_pack.py 中添加 evidence-manifest.json 生成
   - task_id, run_id, base_commit, head_commit, commit_chain
   - required_files_present, optional_files_present
   - runtime_evidence_files, negative_path_scenarios
   - test_summary, git_status_summary
   - verdict_eligibility, limitations

4. 在 gen_review_yaml() 中添加顶层 verdict_eligibility 聚合
   - 跨所有 evidence 类别的综合 eligibility
   - evidence_completeness 块（required/optional/missing 分类）
   - 区分 full_regression vs targeted_tests

5. 标准化 runtime evidence scenario 文件格式
   - scenario name, expected result, actual result, status, source, timestamp
   - 向后兼容现有 .txt 文件

6. 添加正向+负向验证测试
   - complete pack passes validation
   - missing review.yaml → needs_more_evidence
   - missing final-report.md → needs_more_evidence
   - runtime claim without artifact → limitation
   - modified_tracked > 0 → blocks clean acceptance
   - full regression claim without log → downgrade

验收标准：
- modified_tracked = 0
- A1-A4 无回归
- 1204+ 现有测试全通过
- evidence-manifest.json 有效 JSON
- verdict_eligibility 规则确定性（无 AI 判断）

不在范围内：
- 不改旧 evidence pack
- 不改 A1-A4 语义
- 不做 live dispatch enforcement
- 不改 SADP 协议文本
- 不改 evidence_pack_linter.py

4. 请复核以下问题

Q1: ECS-A2 的范围是否合适？是否需要增减？
Q2: verdict_eligibility 应该聚合哪些信号？目前计划：test_pass, conversation_health, startup_read, required_files_present, modified_tracked
Q3: evidence-manifest.json 是否需要与现有 evidence-index.schema.json 对齐？还是创建新 schema？
Q4: "必备文件"统一列表应该以哪个文档为准？evidence-pack-standard.md 的9文件列表？
Q5: 是否需要修正 review.yaml 与 SADP 0.R.2 schema 的偏离？还是留作后续任务？
Q6: runtime evidence scenario 格式标准化是否需要 JSON schema？还是保持 .txt + 规范化 header？"""


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0]

        target_page = None
        for page in ctx.pages:
            if "6a2a8cb1-b228-83aa-addb-79bda9aba043" in page.url:
                target_page = page
                break

        if not target_page:
            target_page = ctx.pages[0]
            print(f"Navigating from {target_page.url} to target...")
            await target_page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)

        print(f"Page: {target_page.url}")
        await target_page.wait_for_timeout(3000)

        ub = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs before: {ub}")

        editor = target_page.locator('#prompt-textarea')
        if await editor.count() == 0:
            editor = target_page.locator('div[contenteditable="true"]').last
        await editor.click()
        await target_page.wait_for_timeout(500)

        await target_page.evaluate(f"""
            async () => {{
                await navigator.clipboard.writeText({json.dumps(MSG, ensure_ascii=False)});
            }}
        """)
        await target_page.wait_for_timeout(500)
        await editor.press("Control+v")
        await target_page.wait_for_timeout(2000)

        send_btn = target_page.locator('button[data-testid="send-button"]')
        disabled = await send_btn.first.get_attribute("disabled")
        print(f"Send disabled: {disabled}")
        if disabled is None:
            await send_btn.first.click()
        else:
            await editor.press("Enter")
            await target_page.wait_for_timeout(2000)
            d2 = await send_btn.first.get_attribute("disabled")
            if d2 is not None:
                await send_btn.first.click(force=True)

        await target_page.wait_for_timeout(5000)
        ua = await target_page.locator('div[data-message-author-role="user"]').count()
        print(f"User msgs after: {ua}")
        if ua <= ub:
            print("WARNING: Message may not have been sent")
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\debug_r1.png")
            return
        print(f"SUCCESS: {ub} -> {ua}")

        print("Waiting for GPT response (180s)...")
        await target_page.wait_for_timeout(180000)

        stop_btn = target_page.locator('button[data-testid="stop-button"]')
        if await stop_btn.count() > 0 and await stop_btn.first.is_visible():
            print("GPT still generating, waiting more (60s)...")
            await target_page.wait_for_timeout(60000)

        ams = target_page.locator('div[data-message-author-role="assistant"]')
        cnt = await ams.count()
        if cnt > 0:
            reply = await ams.last.inner_text()
            print(f"\n=== GPT REPLY R1 ({len(reply)} chars) ===")
            print(reply[:20000])
            op = r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\gpt_review_r1.txt"
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")
        else:
            print("No assistant messages found")
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\debug_r1.png")


asyncio.run(main())
