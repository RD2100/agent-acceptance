# GPT 审查提交脚本使用说明

---

## 概述

`scripts/gpt_new_chat_attachment_submit.py` 是参数化的 GPT 审查提交器，支持两种对话场景（Scenario A 延续性对话 / Scenario B 新对话），并集成了 hardened capture 逻辑（before_assistant_count baseline + run_id authoritative matching）。

---

## 基本用法

```bash
python scripts/gpt_new_chat_attachment_submit.py \
    --task-id "TASK-ID" \
    --pack-path "./path/to/pack.zip" \
    --run-id-path "./path/to/run_id.txt" \
    --output-path "./path/to/GPT_REVIEW_RESULT.txt" \
    --prompt-template "./path/to/GPT_REVIEW_PROMPT.md" \
    [--chat-url "https://chatgpt.com/c/xxx"] \
    [--report-dir "./path/to/report_dir"] \
    [--cdp-url "http://127.0.0.1:9222"] \
    [--timeout 300] \
    [--dry-run]
```

---

## 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--task-id` | 是 | — | 任务 ID，用于 prompt 注入和输出文件命名 |
| `--pack-path` | 是 | — | Evidence pack ZIP 文件路径 |
| `--run-id-path` | 是 | — | 包含 run_id 的文件路径 |
| `--output-path` | 是 | — | GPT 回复保存路径 |
| `--prompt-template` | 否 | 内置通用模板 | Prompt 模板文件路径 |
| `--chat-url` | 否 | `https://chatgpt.com/` | ChatGPT 对话 URL。非根 URL 时自动使用 Scenario A |
| `--report-dir` | 否 | output-path 父目录 | 状态/截图/对账文件存放目录 |
| `--cdp-url` | 否 | `http://127.0.0.1:9222` | Chrome DevTools Protocol 连接地址 |
| `--timeout` | 否 | `300` | 捕获超时时间（秒） |
| `--dry-run` | 否 | `false` | 仅生成 prompt 和配置信息，不实际提交 |

---

## 模板变量

prompt 模板文件中可使用以下变量，脚本会自动替换：

| 变量 | 替换内容 |
|------|----------|
| `{{TASK_ID}}` | `--task-id` 参数值 |
| `{{RUN_ID}}` | 从 `--run-id-path` 文件读取的内容 |
| `{{PACK_MANIFEST}}` | pack 同级目录下 `PACK_MANIFEST.md` 的内容（如不存在则提示） |
| `{{TIMESTAMP}}` | 提交时的 ISO 8601 时间戳 |

---

## 两种场景

### Scenario A — 延续性对话

当 `--chat-url` 指定了具体的对话 URL（如 `https://chatgpt.com/c/xxxx`）时使用。脚本会尝试复用已打开的对话页面，或打开新标签页导航到目标 URL。

适用于：当前延续对话已有上下文，GPT 了解项目背景。

### Scenario B — 新对话

不指定 `--chat-url` 或指定 `https://chatgpt.com/` 时使用。脚本会打开新的 ChatGPT 对话。

适用于：独立的审查任务，不需要先前对话上下文。

---

## 输出文件

脚本运行后会在 `--report-dir`（或 `--output-path` 父目录）生成以下文件：

| 文件 | 说明 |
|------|------|
| `GPT_REVIEW_CHAT_URL.txt` | 提交时使用的 ChatGPT 对话 URL |
| `GPT_REVIEW_SUBMISSION_STATUS.json` | 提交状态（上传/发送/捕获结果） |
| `GPT_REVIEW_UPLOAD_CONFIRMATION.png` | 上传附件后的页面截图 |
| `GPT_REVIEW_RESULT.txt` | 捕获的 GPT 回复全文 |
| `GPT_CAPTURE_RECONCILIATION.json` | 捕获对账报告（baseline / run_id 匹配等） |

捕获的 GPT 回复同时保存到 `--output-path` 指定的路径。

---

## 示例

### Dry Run（检查配置，不提交）

```bash
python scripts/gpt_new_chat_attachment_submit.py \
    --task-id "PROCESS-STATE-MACHINE-DEFINE-A1" \
    --pack-path "evidence_packs/process-state-machine-define-a1/PACK.zip" \
    --run-id-path "_reports/process-state-machine-define-a1/R1_RUN_ID.txt" \
    --output-path "_reports/process-state-machine-define-a1/GPT_REVIEW_RESULT.txt" \
    --prompt-template "evidence_packs/process-state-machine-define-a1/GPT_REVIEW_PROMPT.md" \
    --chat-url "https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959" \
    --dry-run
```

### 提交到延续性对话（Scenario A）

```bash
python scripts/gpt_new_chat_attachment_submit.py \
    --task-id "PROCESS-STATE-MACHINE-DEFINE-A1" \
    --pack-path "evidence_packs/process-state-machine-define-a1/PACK.zip" \
    --run-id-path "_reports/process-state-machine-define-a1/R1_RUN_ID.txt" \
    --output-path "_reports/process-state-machine-define-a1/GPT_REVIEW_RESULT.txt" \
    --prompt-template "evidence_packs/process-state-machine-define-a1/GPT_REVIEW_PROMPT.md" \
    --chat-url "https://chatgpt.com/c/6a26cc03-235c-83a2-a0fc-cd29be615959"
```

### 提交到新对话（Scenario B）

```bash
python scripts/gpt_new_chat_attachment_submit.py \
    --task-id "MY-TASK-A1" \
    --pack-path "evidence_packs/my-task-a1/pack.zip" \
    --run-id-path "evidence_packs/my-task-a1/RUN_ID.txt" \
    --output-path "_reports/my-task-a1/GPT_REVIEW_RESULT.txt"
```

---

## 前置条件

1. Chrome CDP 实例已启动并监听在 `--cdp-url` 指定的端口
2. CDP profile 已登录 ChatGPT
3. Evidence pack ZIP 文件已生成
4. Run ID 文件已创建
5. Prompt 模板文件已准备（或使用内置模板）

启动 Chrome CDP 示例：
```python
import subprocess
from pathlib import Path

chrome = Path(r'C:/Program Files/Google/Chrome/Application/chrome.exe')
profile = Path('D:/agent-acceptance/.chrome-cdp-profile')
subprocess.Popen([
    str(chrome),
    '--remote-debugging-port=9222',
    f'--user-data-dir={profile}',
    '--new-window', 'https://chatgpt.com/'
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

---

## 与硬化计划的对应关系

本脚本实现了 `HANDOFF_WORKFLOW_HARDENING_PLAN.md` 中的：
- **P0-3**: GPT 提交脚本参数化（命令行接口、模板变量、多场景支持）
- **GAP-010**: 部分——capture 逻辑已升级为 before_assistant_count baseline + run_id matching
- **ATTACHMENT_BACKED_GPT_REVIEW_RUNBOOK.md**: 10 步 SOP 的自动化实现

---

*文档生成时间: 2026-06-09*
*Task ID: GPT-REVIEW-SUBMISSION-PARAMETERIZE-A1*
