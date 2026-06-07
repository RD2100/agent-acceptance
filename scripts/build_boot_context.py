#!/usr/bin/env python3
"""
build_boot_context.py — Generate BOOT_CONTEXT.md from compressed knowledge sources.

Produces a 3000-6000 character cold-start entry point for new agents.
Must not exceed the character limit and must not include paper text.
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_SECTIONS = [
    "project_identity",
    "three_layer_architecture",
    "current_stage",
    "recent_accepted_tasks",
    "open_risks",
    "next_recommended_task",
    "absolute_safety_boundaries",
    "cold_start_reading_order",
]

# ── Skeleton knowledge ─────────────────────────────────────────────
# In production this would be built from the compression pipeline output.
# For CONTEXT-COMPRESSION-A1, we generate directly from the known project state.

BOOT_SECTIONS = {
    "project_identity": """
DevFrame 是一个三层工作流治理体系，用 evidence-first + GPT 审查 + 自动化流水线管理 AI 辅助的软件工程任务。

核心价值：把多阶段 Agent/GPT 工作流变成可冷启动、可迁移、可审核、可交接的 evidence-first 框架。

关键仓库：
- agent-acceptance（本仓库）：规范验收层
- devframe-control-plane：编排控制层
- dev-frame-opencode：执行层
""",
    "three_layer_architecture": """
三层架构：
1. agent-acceptance（规范验收层）— 合约、schema、validator、GPT review 模板、pre-commit/pre-push gate
2. devframe-control-plane（编排控制层）— pipeline runner、state machine、submission adapter、CDP bridge、CLI
3. dev-frame-opencode（执行层）— 具体代码修改和测试运行

当前 agent-acceptance 测试 170 PASS，devframe-control-plane 测试 65 PASS，全线绿色。
""",
    "current_stage": """
当前阶段：治理基础设施完善期。已通过 GROUP-01 到 GROUP-06 完成合约、政策、测试、memory compiler、能力清单、chain evidence、workflow closure validator 的 backfill 和 GPT binding。PAPER-C2 已闭合（protocol-only 授权/脱敏 gate，不启用真实论文执行）。

最近完成 REPO-CODE-VERIFICATION-R3：确认 GitHub 远程仓库 clean（仅含 GPT-accepted GROUP files）。本地 worktree 仍 dirty（含 HANDOFF_REPLY_V4 deletion、archive hooks 修改、runs POST_REVIEW_ROUTE 修改、.tmpconfig、.tmpdata、__pycache__），但严格禁止 whole-dirty-tree commit。下一步进入 CONTEXT-COMPRESSION-A1 阶段。
""",
    "recent_accepted_tasks": """
最近 GPT-accepted 任务（2026-06-07）：
- GROUP-01: AA-FLOW-RUNNER-CONTRACT-BACKFILL — contracts + policies + tests (140 files)
- GROUP-02: PAPER-A3-VALIDATOR-RESIDUAL — validate_paper_task.py + test (2 core files)
- GROUP-03: MEMORY-A2-COMPILER-OUTPUT — frozen memory compiler output
- GROUP-04: AGENT-RUNTIME-CAPABILITY-CLEANUP — blackboard cleanup + capability inventory
- GROUP-05: CHAIN-EVIDENCE-HARDENING R3 — ai_guard + go_evidence + chain-evidence schema
- GROUP-06: VALIDATE-WORKFLOW-CLOSURE-CONTROL-PLANE-PATTERN — workflow closure validator
- WorkQueue: specialized batches + Run-WorkQueue propagation
- REPO-CODE-VERIFICATION-R3: remote origin/master clean for accepted scope
""",
    "open_risks": """
当前开放风险：
1. 本地 dirty worktree 未被清理（不得 whole-dirty-tree commit）
2. REVIEW-TEMPLATE-V2 已 push 但未 GPT 审查（需补审）
3. 上下文膨胀：PROJECT_HISTORY.md 和 HANDOFF 版本持续增长，新 agent 冷启动成本上升
4. GPT 审查曾被系统跳过：agent 将 commit+push 当作终点（已通过 pre-push gate step 2.6 加固）
5. CDP 通信依赖 Chrome --remote-debugging-port=9222 运行
""",
    "next_recommended_task": """
推荐下一步：CONTEXT-COMPRESSION-A1（当前任务）
- 建立 BOOT_CONTEXT.md 作为新 agent 冷启动入口
- 建立 memory/index.md 作为可检索记忆索引
- 实现 privacy guard（阻断论文正文、raw transcript、secret）
- 后续可考虑：PAPER-PRIVACY-GUARD-HARDENING、GPT-REVIEW-QUEUE-A1
""",
    "absolute_safety_boundaries": """
绝对安全边界（永久禁止）：
- guard removal
- evidence cleanup/deletion/movement/renaming
- cookies/session/browser profile 读取
- 真实用户数据提交
- CURRENT_STATE/CURRENT_ROUTE 非授权修改
- DECISION_LEDGER 非授权写入
- whole-dirty-tree commit
- 论文正文、raw transcript、private text 写入 memory
- 跳过 GPT 审查声称 closed
""",
    "cold_start_reading_order": """
新 agent 冷启动读取顺序：
1. BOOT_CONTEXT.md（本文档）— 了解项目身份、架构、当前状态、安全边界
2. memory/index.md — 按需检索具体话题记忆
3. PROJECT_HISTORY.md — 仅当需要完整历史时（不推荐每次加载）
4. CLAUDE.md — Agent 行为协议
5. docs/WORKFLOW_AUDIT_LEDGER.yaml — 任务状态机记录
""",
}


def build_boot_context(output_path: str = "BOOT_CONTEXT.md") -> dict:
    now = datetime.now(timezone.utc).isoformat()

    sections_md = []
    section_names = [
        ("project_identity", "## 1. 项目身份"),
        ("three_layer_architecture", "## 2. 三层架构"),
        ("current_stage", "## 3. 当前阶段"),
        ("recent_accepted_tasks", "## 4. 最近 Accepted 任务"),
        ("open_risks", "## 5. 当前开放风险"),
        ("next_recommended_task", "## 6. 下一步推荐任务"),
        ("absolute_safety_boundaries", "## 7. 绝对安全边界"),
        ("cold_start_reading_order", "## 8. 冷启动读取顺序"),
    ]

    header = f"# BOOT_CONTEXT.md — DevFrame 冷启动入口\n\n> 生成时间: {now}\n> 版本: v1.0\n> 用途: 新 agent 首次读取此文件即可了解项目全貌，无需加载完整 PROJECT_HISTORY。\n\n---\n\n"

    for key, title in section_names:
        text = BOOT_SECTIONS[key].strip()
        sections_md.append(f"{title}\n\n{text}\n")

    full_text = header + "\n---\n\n".join(sections_md) + f"\n---\n\n> Boot context 到此结束。需要更多上下文？读取 memory/index.md 或 PROJECT_HISTORY.md。\n"

    char_count = len(full_text)
    text_hash = hashlib.sha256(full_text.encode("utf-8")).hexdigest()

    Path(output_path).write_text(full_text, encoding="utf-8")

    return {
        "boot_context_version": "v1.0",
        "generated_at": now,
        "total_characters": char_count,
        "within_limit": 3000 <= char_count <= 6000,
        "hash": text_hash,
        "file": output_path,
    }


def main():
    result = build_boot_context()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if not result["within_limit"]:
        print(f"WARNING: BOOT_CONTEXT.md is {result['total_characters']} chars (limit: 3000-6000)", file=sys.stderr)
    else:
        print(f"OK: BOOT_CONTEXT.md generated ({result['total_characters']} chars, limit OK)")
    sys.exit(0 if result["within_limit"] else 1)


if __name__ == "__main__":
    main()
