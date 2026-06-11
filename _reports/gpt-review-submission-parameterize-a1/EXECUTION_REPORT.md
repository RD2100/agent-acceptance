# GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1 执行报告

---

## 任务信息

| 字段 | 值 |
|------|-----|
| **task_id** | `GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1` |
| **run_id** | `GPT_REVIEW_SUBMISSION_PARAMETERIZE_A1_20260609T110000_RD` |
| **generated_at** | `2026-06-09T11:00:00+08:00` |
| **authorization_source** | `PROCESS-STATE-MACHINE-DEFINE-A1` verdict: `accepted_with_limitation`, next_task: `GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1` |
| **hardening_plan_ref** | `HANDOFF_WORKFLOW_HARDENING_PLAN.md` section 5.3, section 7 task 2 |

---

## 执行概要

本任务实现了硬化计划 P0-3：将 `gpt_new_chat_attachment_submit.py` 从硬编码委托脚本改造为完全参数化的 GPT 审查提交器。

### 变更内容

**原脚本（已替换）**：5 行 wrapper，通过 `runpy.run_path` 委托到 `_reports/handoff-pipeline-refactor-a1/_submit_new_chat_with_attachment_strict.py`，所有参数（RUN_ID、PACK 路径、输出路径、PROMPT）均硬编码。

**新脚本（参数化版本）**：~400 行，支持完整 CLI 参数、双场景（Scenario A/B）、hardened capture 逻辑、模板变量替换、dry-run 模式。

---

## 产出物清单

| # | 文件 | 描述 |
|---|------|------|
| 1 | `scripts/gpt_new_chat_attachment_submit.py` | 参数化提交器（~400 行） |
| 2 | `_reports/gpt-review-submission-parameterize-a1/gpt_submit_usage.md` | 使用说明文档 |
| 3 | `_reports/gpt-review-submission-parameterize-a1/EXECUTION_REPORT.md` | 本文件 |
| 4 | `_reports/gpt-review-submission-parameterize-a1/_validate_parameterize.py` | 验证脚本 |

---

## 参数化特性对照

### 命令行参数（硬化计划 section 5.3 规格 vs 实现）

| 规格要求 | 实现状态 | 说明 |
|----------|----------|------|
| `--task-id` (required) | ✅ | 用于 prompt 注入和输出文件命名 |
| `--pack-path` (required) | ✅ | evidence pack ZIP 路径 |
| `--run-id-path` (required) | ✅ | run_id 文件路径 |
| `--output-path` (required) | ✅ | GPT 回复保存路径 |
| `--prompt-template` (optional) | ✅ | 自定义 prompt 模板（默认使用内置通用模板） |
| `--dry-run` (optional) | ✅ | 仅生成 prompt 和配置，不提交 |
| `--timeout` (optional) | ✅ | 捕获超时（秒），默认 300 |

### 超出规格的增强

| 增强项 | 说明 |
|--------|------|
| `--chat-url` | 支持 Scenario A（延续性对话）和 Scenario B（新对话）双场景 |
| `--report-dir` | 可自定义状态/截图/对账文件存放目录 |
| `--cdp-url` | 可自定义 CDP 连接地址 |
| Hardened capture | 集成 before_assistant_count baseline + run_id matching（来自 GAP-010） |
| Capture reconciliation | 每次提交自动生成对账报告 JSON |
| 模板变量 `{{TIMESTAMP}}` | 额外支持时间戳注入 |
| Pack manifest 自动加载 | `{{PACK_MANIFEST}}` 自动查找 pack 同级目录 |

---

## 验证结果

### Dry-run 测试

| 测试 | 结果 | 说明 |
|------|------|------|
| CLI `--help` 输出 | PASS | 所有参数和示例正确显示 |
| Scenario A dry-run | PASS | 正确识别延续对话 URL，模板变量替换正确 |
| Scenario B dry-run | PASS | 无 chat-url 时默认为 Scenario B |
| 缺失 pack 错误处理 | PASS | 正确报错并退出（exit code 1） |
| 状态 JSON 输出 | PASS | dry_run 状态文件结构完整 |
| Prompt 模板加载 | PASS | 外部模板文件正确加载，变量替换正常 |

---

## 与硬化计划其他部分的集成

### 与 PROCESS_STATE_MACHINE 的关系

参数化脚本支持硬化计划中定义的状态转换 T02 (gate_passing → gpt_reviewing)：当所有门禁通过后可调用此脚本提交 GPT 审查。

### 与 CHANGED_FILES_SCHEMA 的关系

脚本产出的状态文件（`GPT_REVIEW_SUBMISSION_STATUS.json`、`GPT_CAPTURE_RECONCILIATION.json`）可作为 evidence 记录，在状态转换 T02 时由 `changed_files_utils.py` 标准化记录。

### 与 ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md 的关系

脚本自动化实现了 10 步 SOP 中的以下步骤：
- Step 3: 清空 composer → `clear_composer()`
- Step 4: 上传附件并确认可见 → `try_upload()` + `attachment_check`
- Step 5: 粘贴 prompt → `pyperclip.copy()` + `Control+v`
- Step 6: 点击可见提交按钮 → `click_visible_send_button()`（多选择器 + JS fallback）
- Step 7: 确认 user bubble → 消息计数检查
- Step 8: 捕获回复 → `capture_with_baseline()`（hardened 版本）

---

## 已知限制

1. 脚本依赖 `playwright` 和 `pyperclip`，需要 `pip install` 安装
2. Chrome CDP 实例需要预先启动并登录 ChatGPT
3. `{{PACK_MANIFEST}}` 仅查找 pack 文件同级目录，不支持自定义 manifest 路径
4. 内置默认模板较为通用，具体任务建议使用 `--prompt-template` 指定专用模板
5. Scenario B（新对话）模式下无法预设对话上下文，适用于独立审查任务

---

*报告生成时间: 2026-06-09T11:00:00+08:00*
*Task ID: GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1*
*Run ID: GPT_REVIEW_SUBMISSION_PARAMETERIZE_A1_20260609T110000_RD*
