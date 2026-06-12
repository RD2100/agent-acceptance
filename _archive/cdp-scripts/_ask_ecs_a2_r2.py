"""ECS-A2 Gate 0 Review — Round 2: Revised TaskSpec based on R1 feedback."""
import asyncio, os, json, sys
from pathlib import Path
from playwright.async_api import async_playwright

TARGET_URL = "https://chatgpt.com/c/6a2a8cb1-b228-83aa-addb-79bda9aba043"
CDP_URL = "http://localhost:9222"

MSG = """EVIDENCE-CAPTURE-STANDARD-A2 — Gate 0 第2轮：修订后 TaskSpec 确认

感谢 R1 的详细反馈。我已吸收全部6个问题的回答，将 A2 范围收敛。以下是修订后的 TaskSpec，请确认是否可以启动执行。

---

TaskSpec: EVIDENCE-CAPTURE-STANDARD-A2

task_id: EVIDENCE-CAPTURE-STANDARD-A2
title: Evidence Capture Standard — canonical evidence pack contract & builder enforcement
priority: P0
status: draft

Goal:
Define and enforce a canonical evidence pack contract by adding evidence-manifest generation,
top-level verdict eligibility, evidence completeness classification, runtime evidence indexing,
and deterministic builder validation.

---

7项核心工作（按 R1 建议固定）：

1. 新建 docs/agent-runtime/evidence-capture-standard.md
   - 分层必备文件定义：
     Tier 0（所有 pack 必备，10项）：
       review.yaml, final-report.md, git-status-before.txt, git-status-after.txt,
       diff.patch 或 git-show.txt, test-output.txt 或 no-test-rationale.md,
       safety-report.json, secret-scan output, task spec / current-task snapshot,
       evidence-manifest.json
     Tier 1（条件必备，声称相关能力时必须有）：
       runtime evidence index, negative-path evidence, hook-output/latest.json,
       conversation-health/latest.json, startup-read-latest.json,
       full-regression log, migration record, schema validation output
     Tier 2（可选）：
       raw command logs, screenshots, debug output, coverage output
   - verdict_eligibility 规则（三类信号分类）：
     硬阻断信号 → eligible → needs_more_evidence / not_eligible
       required_files_missing, modified_tracked > 0 without deferred record,
       tests_failed_without_explanation, claimed_full_regression_but_log_missing,
       runtime_behavior_claimed_but_no_runtime_artifact,
       schema_invalid_manifest_or_review_yaml
     降级信号 → eligible_with_limitations
       startup_read_missing, conversation_health_suggest, advisory_stage_warning,
       only_targeted_tests_run, runtime_proved_by_tests_only,
       missing_optional_files, ai_guard_warning_explained
     记录信号 → 不影响 eligibility
       untracked_total, session_artifacts, neg_009_count, generated_at,
       pack_size, zip_sha256, warning_count
   - verdict_eligibility 枚举：
     eligible_clean | eligible_with_limitations | needs_more_evidence | not_eligible
   - "Relationship to SADP 0.R.2 Review YAML" 一节：
     明确 ECS review.yaml 是 evidence pack metadata，
     SADP 0.R.2 review.yaml 是 reviewer protocol artifact，
     二者当前不等价。后续另开 SADP-REVIEW-YAML-ALIGNMENT-A1。
   - review_yaml_profile: "ecs-v1"
   - runtime evidence 双轨制说明：
     .txt scenario 文件 + 标准化 header（Scenario/Expected/Actual/Status/Source/Generated/Code version）
     runtime-evidence-index.json 机器可读索引

2. 新建 docs/agent-runtime/evidence-pack-review-rules.md
   - 整合分散在 4 份文档中的 review 评估规则
   - 与 evidence-capture-standard.md 交叉引用

3. 新建 schemas/agent-runtime/evidence-manifest.schema.json
   - 最小字段：
     schema_version, task_id, run_id, base_commit, head_commit,
     commit_chain, generated_at, required_files, optional_files,
     missing_files, test_summary, runtime_evidence,
     negative_path_evidence, git_status, safety,
     verdict_eligibility, limitations
   - 支撑 builder 的 deterministic validation
   - evidence-index.schema.json 保留为 legacy，文档说明二者关系

4. 可选：新建 schemas/agent-runtime/runtime-evidence-index.schema.json
   - runtime-evidence-index.json 的 schema
   - 字段：schema_version, scenarios[] (name, file, expected, actual, status, source, generated_at, head_commit)

5. build_evidence_pack.py 改造
   - 生成 evidence-manifest.json（符合新 schema）
   - review.yaml 增加顶层 verdict_eligibility 块：
     status: eligible_clean | eligible_with_limitations | needs_more_evidence | not_eligible
     reasons: []
     blocking_signals: []
     limitation_signals: []
   - review.yaml 增加 evidence_completeness 块：
     tier_0_required: [文件列表]
     tier_0_present: [文件列表]
     tier_0_missing: [文件列表]
     tier_1_conditional: [条件文件列表]
     tier_1_present: [已存在列表]
     tier_1_missing: [缺失列表]
     tier_2_optional: [可选文件列表]
   - 区分 full_regression / targeted_tests / no_test_rationale
   - 生成 runtime-evidence-index.json（当 --extra-dir 包含 .txt scenario 文件时）
   - 支持 --head 参数（可默认 HEAD）
   - review_yaml_profile: "ecs-v1"

6. 标准化 runtime evidence scenario header
   - 保持 .txt 文件
   - 标准化 header 格式：
     # Scenario: <name>
     # Expected: <expected result>
     # Actual: <actual result>
     # Status: PASS | FAIL | SKIP
     # Source: <command or script>
     # Generated: <ISO-8601 timestamp>
     # Code version: <head_commit>
   - 向后兼容现有 .txt 文件（旧格式仍可解析）

7. 添加测试 + runtime evidence
   测试覆盖：
   - complete pack generates valid manifest
   - evidence-manifest.json conforms to schema
   - verdict_eligibility = eligible_clean when all tier 0 present
   - verdict_eligibility = needs_more_evidence when review.yaml missing
   - verdict_eligibility = needs_more_evidence when final-report.md missing
   - verdict_eligibility = eligible_with_limitations when startup_read missing
   - full_regression claim without log → limitation or downgrade
   - runtime claim without artifact → limitation
   - modified_tracked > 0 → blocks clean eligibility
   - runtime-evidence-index.json generated from .txt scenarios
   - --head parameter correctly sets head_commit in manifest

   Runtime evidence（7个场景）：
   - complete_pack_valid
   - missing_review_yaml_needs_more_evidence
   - missing_final_report_needs_more_evidence
   - missing_runtime_artifact_downgrades
   - stale_extra_evidence_detected
   - modified_tracked_blocks_clean_acceptance
   - full_regression_claim_requires_log

---

Deny paths（与 R1 一致，不碰这些文件）：
- scripts/pre_commit_*.py
- scripts/check_handoff_needed.py
- scripts/startup_conversation_health_check.py
- scripts/validate_hook_output.py
- scripts/ai_guard.py
- hooks/pre-commit.governance.ps1
- docs/agent-runtime/sub-agent-dispatch-protocol.md
- docs/agent-runtime/startup-read-gate.md
- scripts/evidence_pack_linter.py
- tests/test_hook_failure_semantics.py
- tests/test_startup_conversation_health_check.py
- tests/test_pre_gpt_review_gate.py

Acceptance criteria:
- evidence-capture-standard.md 存在且可被未来 agent 使用
- evidence-pack-review-rules.md 存在且整合了 review 规则
- evidence-manifest.schema.json 存在且 builder 生成符合 schema 的 manifest
- build_evidence_pack.py 生成 evidence-manifest.json
- review.yaml 包含顶层 verdict_eligibility 和 evidence_completeness 块
- 区分 full_regression / targeted_tests
- 缺失 Tier 0 必备文件 → needs_more_evidence
- runtime 声称无 artifact → limitation
- modified_tracked > 0 → blocks clean eligibility
- 正向+负向测试覆盖
- runtime negative-path evidence 包含在 evidence pack 中
- modified_tracked = 0 after commit
- 1204+ 现有测试无回归

---

请确认：
1. 这份修订后的 TaskSpec 是否可以启动执行？
2. 是否有需要调整的细节？
3. 授权我立即执行？还是仍需 ask_before_starting？"""


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
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\debug_r2.png")
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
            print(f"\n=== GPT REPLY R2 ({len(reply)} chars) ===")
            print(reply[:20000])
            op = r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\gpt_review_r2.txt"
            os.makedirs(os.path.dirname(op), exist_ok=True)
            with open(op, "w", encoding="utf-8") as f:
                f.write(reply)
            print(f"\nSaved: {op}")
        else:
            print("No assistant messages found")
            await target_page.screenshot(path=r"D:\agent-acceptance\_evidence\EVIDENCE-CAPTURE-STANDARD-A2\debug_r2.png")


asyncio.run(main())
