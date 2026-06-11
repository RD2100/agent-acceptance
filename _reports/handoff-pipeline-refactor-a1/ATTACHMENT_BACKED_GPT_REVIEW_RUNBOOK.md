# 附件版 GPT 审查流程手册

> 任务：HANDOFF-PIPELINE-REFACTOR-A1  
> 状态：2026-06-08 修正后生效  
> 目标：确保 GPT 审查是真正基于新对话 + 可见附件 + 可验证回复，而不是旧回复或未发送草稿。

## 为什么需要这套流程

之前的自动化用了 `Control+Enter` 作为提交动作，但 ChatGPT 网页没有真正发送消息：prompt 仍停留在输入框里。因此以后不能把“按了快捷键”当作“已提交”。

新的硬规则是：

1. 必须点击网页里可见的提交按钮。
2. 必须确认消息真的发出。
3. 必须确认附件在页面中可见。
4. 必须用 `run_id` 绑定本次审查，避免捕获旧回复。

## 必须通过的前置门槛

### 1. fresh shell

每次执行前先运行：

```bash
cd "D:/agent-acceptance" && pwd && date && echo FRESH_SHELL_OK && git rev-parse --is-inside-work-tree
```

要求：

- `pwd` 是 `/d/agent-acceptance`
- 出现 `FRESH_SHELL_OK`
- git 返回 `true`
- 命令同步返回，不进入后台卡住

### 2. 新建唯一 run_id

每次审查必须生成新的 run_id，例如：

```text
HANDOFF_A1_ATTACHCHAT_YYYYMMDD_HHMMSS_RANDOM6
```

本次成功 run_id：

```text
HANDOFF_A1_ATTACHCHAT_20260608_220428_CHL0ZX
```

### 3. 新开 GPT 对话

必须打开新 ChatGPT 对话，不复用旧 URL。  
旧对话容易返回 stale reply 或让 capture 读到旧 assistant message。

### 4. 清空输入框

新对话打开后，先清空 composer，防止残留上一轮未发送 prompt。

### 5. 上传附件并确认可见

上传：

```text
evidence_packs/handoff-pipeline-refactor-a1/closure-pack.zip
```

上传后必须确认页面文本中能看到：

```text
closure-pack.zip
```

或至少：

```text
closure-pack
```

同时保存截图。

本次成功截图：

```text
_reports/handoff-pipeline-refactor-a1/ATTACH_UPLOAD_CONFIRMATION.png
```

### 6. 粘贴 prompt

prompt 必须包含本次 run_id，并要求 GPT 输出：

- run_id
- task_id
- overall_judgment
- evidence_pack_reviewed
- attachment_reviewed
- next_task_authorization
- END_OF_GPT_RESPONSE

### 7. 点击提交按钮

禁止只用 `Control+Enter`。

必须点击可见提交按钮。本次成功命中的按钮：

```text
button[data-testid="send-button"]
```

备用选择器：

```text
button.composer-submit-button-color
```

### 8. 确认消息真的发出

点击后必须确认至少一项成立：

- user message bubble 出现
- assistant response 开始生成
- 输入框清空

本次成功确认：

```json
"send_confirm": {
  "ok": true,
  "reason": "user_message_bubble_appeared"
}
```

### 9. 捕获 GPT 回复

只接受同时包含以下内容的回复：

- 本次 run_id
- `overall_judgment:`
- `END_OF_GPT_RESPONSE`

否则不得报告 verdict。

### 10. 本地验证

必须运行：

```bash
cd "D:/agent-acceptance" && python scripts/verify_gpt_reply.py evidence_packs/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_ATTACHCHAT.txt HANDOFF-PIPELINE-REFACTOR-A1
```

只有 verifier 通过，才能生成 approved handoff。

## 本次成功证据

| 项目 | 路径 / 值 |
|---|---|
| run_id | `HANDOFF_A1_ATTACHCHAT_20260608_220428_CHL0ZX` |
| 新 GPT 对话 URL | `_reports/handoff-pipeline-refactor-a1/ATTACH_GPT_CHAT_URL.txt` |
| 上传截图 | `_reports/handoff-pipeline-refactor-a1/ATTACH_UPLOAD_CONFIRMATION.png` |
| 提交状态 | `_reports/handoff-pipeline-refactor-a1/ATTACH_SUBMISSION_STATUS.json` |
| GPT 回复 | `evidence_packs/handoff-pipeline-refactor-a1/GPT_REVIEW_RESULT_ATTACHCHAT.txt` |
| verify 输出 | `_reports/handoff-pipeline-refactor-a1/VERIFY_GPT_REPLY_OUTPUT_ATTACHCHAT.txt` |
| run_id 校验 | `_reports/handoff-pipeline-refactor-a1/ATTACH_RUN_ID_CHECK.json` |
| 最终 verdict | `accepted_with_limitation` |
| attachment_reviewed | `true` |

## 失败处理规则

遇到以下情况必须停止，不得继续假装成功：

| 情况 | 处理 |
|---|---|
| 附件不可见 | `manual_required` |
| 找不到提交按钮 | `manual_required` |
| 点击提交后没有 user bubble / assistant response | `manual_required` |
| 捕获回复不含 run_id | 判定 stale/wrong reply |
| 捕获回复不含 END_OF_GPT_RESPONSE | 不得报告 verdict |
| 捕获回复不含 overall_judgment | 不得报告 verdict |
| verify_gpt_reply 不通过 | 不得生成 approved handoff |

## 固化脚本

入口脚本：

```text
scripts/gpt_new_chat_attachment_submit.py
```

当前已验证实现：

```text
_reports/handoff-pipeline-refactor-a1/_submit_new_chat_with_attachment_strict.py
```

后续如要复用到其他任务，应先参数化 task_id、pack path、run_id path、输出路径和 prompt 模板。
