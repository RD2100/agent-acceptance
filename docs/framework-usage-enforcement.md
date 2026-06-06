# Framework Usage Enforcement — 框架使用强制规范

> 权威来源: agent-acceptance
> 版本: 1.0.0-draft
> 适用范围: 所有正式任务（非 historical artifact、非 negative fixture、非授权 pilot）

## 1. 问题陈述

DevFrame 三层架构设计完备（agent-acceptance → devframe-control-plane → dev-frame-opencode），但实际执行中智能体系统性地绕过框架：

| 应该使用 | 实际使用 |
|---------|---------|
| `submission_adapter.submit()` | 手写 `submit_to_gpt.py` 直接调 Playwright |
| `playwright_bridge.submit_via_bridge()` | 手写 `live_handoff_transfer.py` 绕过 bridge |
| `pipeline_runner.dry_run()` | 未调用，直接手写 Python |
| `state_machine` | 从未运行 |
| 框架生成的 FLOW_OUTCOME | 手写 FLOW_OUTCOME.json |
| 标准 evidence pack builder | 手动 `zipfile.ZipFile()` |

**这不是执行纪律问题，是设计缺陷：正确路径成本高于绕过路径。**

## 2. 核心原则

- **框架路径是唯一正式路径**：所有正式 closure 必须经过 devframe pipeline
- **绕过不可验收**：绕过框架产出的 evidence 不构成正式 evidence
- **例外必须声明**：historical artifact、negative fixture、授权 pilot 必须显式声明
- **Agent 陈述不是证据**：手写 summary、手写 FLOW_OUTCOME、手写 closure report 不等于证据

## 3. 判定规则

### 3.1 accepted

条件：
- 任务通过 `devframe run` 或等效 pipeline 执行
- FLOW_OUTCOME 由 runner 生成，不由 agent 手写
- evidence pack 由标准 builder 生成，manifest 与 ZIP 双向一致
- submission 通过 `submission_adapter` 或 `playwright_bridge`
- pre-submission gate 通过
- pipeline_run_id 可追溯

### 3.2 blocked（以下任一触发）

- 检测到未授权 `submit_to_gpt.py`
- 检测到未授权 `live_handoff_transfer.py`
- 检测到未授权 `sync_playwright` / `connect_over_cdp` 在非 adapter 文件中
- FLOW_OUTCOME 为手写且无 pipeline provenance
- evidence pack 无 pipeline_run_id
- 绕过 submission_adapter 直接提交 GPT

### 3.3 review_unverified

- 无法确认是否经过 pipeline
- pipeline_run_id 存在但有矛盾
- submission 路径不明确

## 4. 允许的例外

| 例外类型 | 声明方式 | 条件 |
|---------|---------|------|
| historical artifact | RUN_CLASSIFICATION.yaml（classification: historical_artifact） | 预存、未修改 |
| negative fixture | RUN_CLASSIFICATION.yaml（classification: negative_fixture） | expected_invalid=true |
| 授权 pilot | 显式授权文档 + 限定 scope | 单次、不可推广 |

## 5. 绕过检测规则

以下模式出现在非允许路径时视为绕过：

| 模式 | 允许路径 |
|------|---------|
| `sync_playwright` | `control_plane/playwright_bridge.py`、`control_plane/cdp_adapter.py` |
| `connect_over_cdp` | `control_plane/playwright_bridge.py`、`control_plane/cdp_adapter.py` |
| `submit_to_gpt` | 无（除非在 tests/ 或 declared fixture 中） |
| `live_handoff_transfer` | 无（逻辑已整合进 playwright_bridge.py） |
| `page.goto` + GPT URL | `control_plane/playwright_bridge.py`、tests/ |

## 6. 安全边界

本规范不授权以下行为：
- 删除、移动、重命名 evidence
- 移除或弱化 guard
- 默认开启 live CDP
- 处理真实用户数据
