# 项目规范操作手册 — agent-acceptance

> 最后更新: 2026-06-10 (R13)
> 维护人: QoderWork Agent (executor)
> 审核人: ChatGPT independent_reviewer (conversation 6a26cc03)
> 保护级别: SADP protected (docs/agent-runtime/ 路径，纳入 governancePatterns)

---

## 0. 为什么需要这份手册

本项目在 R1-R13 开发过程中暴露了重复造轮子的问题：`_utc_now()` 在 9 个文件中各写一遍，`load_registry()` 重复 5 次，GPT 提交流程的 workspace 临时脚本多达 27 个。每次新 session 都在重新发明同样的工具。

本手册是项目唯一的操作参考来源。任何新 session 开始工作前，必须先读本手册，检查是否已有现成工具和流程可以复用。

**核心原则：reuse > create, configure > implement, compose > abstract.**

---

## 1. 项目架构概览

```
agent-acceptance/
├── .sadp/                      # SADP 策略文件 (受保护)
│   ├── SADP_POLICY.json        # 统一策略源
│   └── TRIGGER_RULES.json      # 触发规则
├── .agent/                     # 项目注册 (治理相邻)
│   └── PROJECT_REGISTRY.json   # 10 项目注册表
├── _projects/                  # 子项目目录
│   └── {project-id}/
│       └── .agent/CONVERSATION_BINDING.json
├── _evidence/                  # 审核证据包
├── docs/agent-runtime/         # 运行时文档 (受保护)
├── scripts/                    # 正式脚本 (本手册重点)
├── tests/                      # 测试套件 (1038 tests)
├── tasks/                      # TaskSpec 定义
├── rules/core.md               # 核心规则 (受保护)
├── AGENTS.md                   # 治理入口 (受保护)
└── CLAUDE.md                   # 全局指令 (受保护)
```

**Shared CDP v2 架构**: 10 个项目共享一个 Chrome 实例 (localhost:9222)，通过 conversation_id + tab target_id 实现隔离。

---

## 2. 正式工具清单

> 以下脚本位于 `D:\agent-acceptance\scripts\`，是经过审核的正式版本。
> workspace 中的临时脚本 (如 `paste_to_chatgpt.py`, `capture_gpt_reply_v2.py`) 是原型，应逐步迁移到正式版本。

### 2.1 CDP / 浏览器自动化

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| `tab_target_resolver.py` | 将 chat_url 解析为 CDP page target_id | 所有需要查找标签页的操作 |
| `multi_project_router.py` | 多项目任务路由，解析 dispatch 目标 | 确定消息发往哪里 |
| `gate0_preflight_10.py` | 10 项目预检，分类 active/pending/blocked | 任务开始前检查就绪状态 |
| `dry_run_dispatch_10.py` | dry-run 全 10 项目，构造 dispatch packet 但不发送 | 验证 dispatch 逻辑 |
| `multi_cdp_launcher.py` | 启动共享 Chrome 实例 (单 CDP) | 首次启动或重启 Chrome |
| `lazy_launch_manager.py` | 按需管理 Chrome CDP 生命周期 | 资源受限时的延迟启动 |
| `onboard_project.py` | 一键 onboarding: Chrome + CDP + binding + registry | 新项目接入 |
| `smoke_test_two_projects.py` | 双项目隔离验证 (9222+9223) | 隔离性 smoke test |

**关键 API:**
```python
from scripts.tab_target_resolver import list_cdp_pages, resolve_tab_target, validate_cdp_endpoint
# list_cdp_pages(endpoint) -> list[dict]  # 列出 CDP 所有页面
# resolve_tab_target(endpoint, chat_url) -> TabTarget  # 解析精确标签
# validate_cdp_endpoint(endpoint) -> (bool, str)  # 验证 CDP 端点安全
```

### 2.2 SADP 治理

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| `sadp_pre_task_enforcer.py` | 3 边界强制 (pre_task, pre_edit, post_task) | 所有任务执行入口 |
| `qoderwork_task_runner.py` | P0/P1 任务执行 wrapper | `python scripts/qoderwork_task_runner.py start <taskspec>` |
| `state_machine_runtime.py` | 状态机转换守卫 | draft -> gate_passing 等状态转换 |
| `validate_taskspec.py` | TaskSpec YAML 结构验证 | 编写 TaskSpec 后验证 |
| `human_decision_record.py` | human_required 决策记录 | 人工决策后记录证据 |

**Task Runner 标准用法:**
```bash
# 1. 开始任务 (验证 TaskSpec + Gate 0)
python scripts/qoderwork_task_runner.py start tasks/task-xxx.md

# 2. 编辑前检查 (文件是否在 write_set)
python scripts/qoderwork_task_runner.py edit-check path/to/file.py

# 3. 完成任务 (生成 ExecutionReport)
python scripts/qoderwork_task_runner.py finish
```

### 2.3 GPT Review 工作流

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| `gpt_new_chat_attachment_submit.py` | 参数化 GPT 提交 (Scenario A/B) | 向 ChatGPT 发送审核材料 |
| `capture_gpt_reply.py` | 捕获 GPT 回复 (等待 END marker) | 提交后等待并抓取回复 |
| `validate_gpt_reply_completeness.py` | 验证回复完整性 | 捕获后验证质量 |
| `verify_gpt_reply.py` | P0 守卫: 无回复则无 verdict | 阻止基于摘要的判定 |
| `review_queue.py` | Review 队列生命周期管理 | 跟踪 submitted -> replied -> closed |
| `pre_gpt_review_gate.py` | 提交前证据质量门控 | 发送前检查证据包 |
| `gpt_review_transaction.py` | 完整 GPT review 事务 | 端到端 review 流程 |
| `generate_reconciliation_report.py` | 提交->捕获->verdict 链审计 | 对账异常检测 |

**标准 Review 提交流程:**
```bash
# 1. 复制提交文本到剪贴板 (PowerShell)
Set-Clipboard -Value (Get-Content submission.txt -Raw)

# 2. 通过 CDP 粘贴到 ChatGPT
python scripts/gpt_new_chat_attachment_submit.py --scenario A --conversation-url "..."

# 3. 等待 45s 后捕获回复
sleep 45 && python scripts/capture_gpt_reply.py --conversation-url "..."

# 4. 验证回复完整性
python scripts/validate_gpt_reply_completeness.py --reply gpt_reply_latest.txt

# 5. 归档 verdict
cp gpt_reply_latest.txt _evidence/XXX/GPT_REVIEW_RESULT_R{N}.txt
```

### 2.4 项目管理

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| `awsp_scaffold.py` | 生成 AWSP 标准项目结构 | 新项目脚手架 |
| `batch_init_10_projects.py` | 批量初始化 10 项目 | 注册表 + profile + binding |
| `update_conversation_registry.py` | 更新对话注册表 | 对话状态变更 |
| `append_to_project_history.py` | 追加任务记录到 PROJECT_HISTORY | 任务完成后记录 |
| `validate_conversation_registry.py` | 对话注册表合规验证 | 审核后验证 |

### 2.5 Memory / 上下文

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| `memory_compiler.py` | 从 GPT review 和 audit 提取 lessons | session 结束前编译记忆 |
| `memory_lint.py` | 记忆条目合规检查 | 验证记忆质量 |
| `compress_project_context.py` | 压缩历史上下文 | 上下文过长时压缩 |
| `build_boot_context.py` | 生成 BOOT_CONTEXT.md | 新 agent 冷启动 |
| `validate_context_memory.py` | 隐私守卫 (禁止论文全文等) | 输出前检查敏感内容 |

### 2.6 测试 / 验证

| 脚本 | 用途 | 使用场景 |
|------|------|----------|
| `smoke_suite.py` | 一键健康检查 | 日常开发前快速验证 |
| `evidence_pack_linter.py` | 证据包质量检查 | 提交 GPT 前检查 |
| `startup_read_gate.py` | 启动读取门控 | 确保 agent 读完必要文件 |
| `pre_push_verify.py` | 推送前验证 | git push 前检查 |
| `ci_matrix.py` | 基于影响分析的 CI 矩阵 | 智能测试选择 |

**全量测试:**
```bash
cd D:\agent-acceptance
python -m pytest tests/ -v --tb=short 2>&1 | tee test_output.txt
# 当前: 1038 passed, 0 failed, 21 warnings
```

### 2.7 Paper / 论文工具

| 脚本 | 用途 |
|------|------|
| `paper_pilot_preflight.py` | 论文工作前隐私安全检查 |
| `paper_auth_gate.py` | 人工授权门控 (fail-closed) |
| `paper_c4_section_review.py` | 章节结构化审查 |
| `paper_c5_full_section_reader.py` | 全文段落级结构分析 |
| `paper_c6_revision_suggester.py` | 修订建议生成 |
| `paper_c7_collab_iterator.py` | Claude+GPT 协作修订循环 |
| `paper_proofreading_gate.py` | 格式/排版检查 |

### 2.8 PowerShell 脚本

| 脚本 | 用途 |
|------|------|
| `sadp-audit.ps1` | SADP 治理审计 (16KB)，governancePatterns 覆盖检查 |
| `Run-Smoke.ps1` | Smoke 测试运行器 |
| `Test-Governance.ps1` | 治理测试套件 |
| `Test-GovernanceDrift.ps1` | 治理漂移检测 |
| `Test-ReviewerEvidence.ps1` | Reviewer 证据验证 |
| `Run-WorkQueue.ps1` | 工作队列执行 |
| `Run-Batch.ps1` | 批量执行 |

---

## 3. 标准操作流程 (SOP)

### SOP-1: 绑定新对话到项目

**前置条件**: Chrome 已启动 (localhost:9222)，用户在 ChatGPT 中创建了新对话。

```
步骤 1: 获取对话 URL
  用户手动创建 ChatGPT 对话，复制 URL (如 https://chatgpt.com/c/xxxx)

步骤 2: 更新 CONVERSATION_BINDING.json
  文件: _projects/{project-id}/.agent/CONVERSATION_BINDING.json
  修改:
    - binding_status: "pending_binding" → "active"
    - conversation_id: 从 URL 提取 UUID
    - chat_url: 完整 URL
    - cdp_endpoint: "http://localhost:9222"

步骤 3: 更新 PROJECT_REGISTRY.json
  文件: .agent/PROJECT_REGISTRY.json
  修改:
    - projects.{project-id}.binding_status: "pending_binding" → "active"

步骤 4: 验证
  python scripts/dry_run_dispatch_10.py
  确认: 目标项目 classification = "dispatchable"
```

### SOP-2: 提交审核给 ChatGPT

**前置条件**: 提交文本已准备好，Chrome 已打开 reviewer 对话。

```
步骤 1: 准备提交文本
  创建 r{N}_submission.txt，包含:
    - 任务 ID 和描述
    - 变更摘要 (文件 + 测试结果)
    - 证据路径
    - 结论

步骤 2: 复制到剪贴板
  PowerShell: Set-Clipboard -Value (Get-Content r{N}_submission.txt -Raw)

步骤 3: 通过 CDP 粘贴
  python scripts/gpt_new_chat_attachment_submit.py --scenario A

  或手动流程 (当正式脚本不可用时):
    a. Playwright connect_over_cdp("http://localhost:9222")
    b. 找到 reviewer 对话页面 (URL 含 6a26cc03)
    c. 点击 #prompt-textarea
    d. Ctrl+V 粘贴
    e. Enter 发送

步骤 4: 等待并捕获
  sleep 45
  python scripts/capture_gpt_reply.py

步骤 5: 归档
  cp gpt_reply_latest.txt _evidence/XXX/GPT_REVIEW_RESULT_R{N}.txt

步骤 6: 更新证据链
  - 更新 REVIEWER_INDEX.md (添加 round summary + YAML record)
  - 更新 EXECUTION_REPORT.md (review_rounds, final_verdict, test counts)
```

### SOP-3: 创建新 TaskSpec

```
步骤 1: 检查授权
  查看 REVIEWER_INDEX.md 的 next_authorized_tasks
  确认任务 ID 在授权列表中

步骤 2: 编写 TaskSpec
  文件: tasks/task-{task-id}.md
  必须包含: task_id, priority, write_set, acceptance_gates, test_plan

步骤 3: 验证
  python scripts/validate_taskspec.py tasks/task-{task-id}.md

步骤 4: Gate 0
  python scripts/gate0_preflight_10.py
  确认所有 gate 通过
```

### SOP-4: 运行完整测试

```bash
# 全量测试
cd D:\agent-acceptance
python -m pytest tests/ -v --tb=short

# 目标测试 (特定文件)
python -m pytest tests/test_sadp_pre_task_enforcer.py -v

# Smoke 快速检查
python -m pytest tests/test_smoke_suite.py -v

# PowerShell 治理测试
powershell -File scripts/Test-Governance.ps1
```

### SOP-5: 解绑项目

```
步骤 1: 更新 CONVERSATION_BINDING.json
  binding_status: "active" → "pending_binding"
  conversation_id: null
  chat_url: null

步骤 2: 更新 PROJECT_REGISTRY.json
  projects.{project-id}.binding_status: "pending_binding"

步骤 3: 验证
  python scripts/dry_run_dispatch_10.py
  确认: 目标项目 classification = "non_dispatchable_pending"
```

### SOP-6: SADP 治理审计

```powershell
# 运行完整治理审计
powershell -ExecutionPolicy Bypass -File scripts/sadp-audit.ps1

# 检查治理漂移
powershell -File scripts/Test-GovernanceDrift.ps1

# Python 侧交叉验证 (smoke tests)
python -m pytest tests/test_sadp_pre_task_enforcer.py::TestAuditPolicySmoke -v
```

---

## 4. 常见公用函数 (复用优先)

以下函数在多处重复实现，新代码必须导入正式版本，禁止重复编写。

### 4.1 _utc_now() — 重复 9 处

生成 ISO-8601 UTC 时间戳。

```python
# 正式版本位置: scripts/ 多处定义，建议统一到公共模块
# 当前分散在: dry_run_dispatch_10.py, multi_project_router.py,
#              tab_target_resolver.py, gate0_preflight_10.py 等
from datetime import datetime, timezone
def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
```

**待办 (P2)**: 提取到 `scripts/lib/common.py`，所有消费者统一导入。

### 4.2 load_registry() — 重复 5 处

加载 PROJECT_REGISTRY.json。

```python
# 正式版本: scripts/multi_project_router.py
import json
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
def load_registry() -> dict:
    return json.loads((REPO / ".agent" / "PROJECT_REGISTRY.json").read_text(encoding="utf-8"))
```

**待办 (P2)**: 提取到公共模块。

### 4.3 load_binding() — 重复 3 处

加载 CONVERSATION_BINDING.json。

```python
# 正式版本: scripts/multi_project_router.py
def load_binding(project_root: Path) -> dict:
    binding_path = project_root / ".agent" / "CONVERSATION_BINDING.json"
    if not binding_path.exists():
        return {}
    return json.loads(binding_path.read_text(encoding="utf-8"))
```

**待办 (P2)**: 提取到公共模块。

### 4.4 validate_cdp_endpoint() — 已有正式版本

```python
# 正式版本: scripts/tab_target_resolver.py
# 所有 CDP 端点验证必须使用此函数，禁止自行实现
from scripts.tab_target_resolver import validate_cdp_endpoint
valid, reason = validate_cdp_endpoint("http://localhost:9222")
```

### 4.5 _normalize_url() — 已有正式版本

```python
# 正式版本: scripts/tab_target_resolver.py
# URL 规范化 (去 query/fragment/trailing slash)
from scripts.tab_target_resolver import _normalize_url
```

---

## 5. Workspace 临时脚本对照表

> 以下 workspace 临时脚本是开发过程中产生的原型。正式脚本存在时，必须使用正式版本。

| Workspace 临时脚本 | 正式版本 | 迁移状态 |
|-------------------|---------|---------|
| paste_to_chatgpt.py | gpt_new_chat_attachment_submit.py | 待迁移 |
| capture_gpt_reply.py | capture_gpt_reply.py (scripts/) | 已存在正式版 |
| capture_gpt_reply_v2.py | capture_gpt_reply.py (scripts/) | 待迁移 (v2 增加文件输出) |
| copy_r*.ps1 (12个) | Set-Clipboard 一行命令 | 无需迁移 (临时剪贴板操作) |
| diagnose_chrome.py | multi_cdp_launcher.py | 诊断工具，保留 |
| check_chatgpt.py | onboard_project.py | 待整合 |
| batch_bootstrap.py | batch_init_10_projects.py | 待整合 |
| batch_bind.py | bind_real_conversation_alpha.py | 待整合 |
| reset_projects.py | (无正式版) | 待创建 |

**原则**: workspace 脚本用于快速原型验证。一旦功能稳定，必须迁移到 `scripts/` 目录并添加测试。

---

## 6. 复用检查清单 (core-008)

任何新代码编写前，必须走完这个清单:

```
□ 1. 检查本手册第 2 节工具清单 — 是否已有现成脚本？
□ 2. 检查第 4 节公用函数 — 是否已有可复用函数？
□ 3. 检查 capability-inventory.md — 是否已注册相关能力？
□ 4. 检查 tests/ — 是否已有类似测试可以扩展？
□ 5. 检查 lessons-learned.md — 是否有已知的坑和解决方案？
□ 6. 如果以上都无，提供 delta 理由说明为何不能复用
```

### 复用决策树

```
需要实现新功能
  ├── 已有脚本覆盖? → 直接使用
  ├── 已有函数覆盖? → 导入使用
  ├── 已有脚本可配置化? → 添加参数/选项
  ├── 已有脚本可组合? → 组合使用
  ├── 以上都不行 → 新建，但必须:
  │     ├── 提供 delta 理由
  │     ├── 添加到本手册第 2 节
  │     ├── 如果是公用函数，添加到第 4 节
  │     └── 添加对应测试
  └── 临时原型? → 放 workspace，但标记迁移目标
```

---

## 7. 已知问题和踩坑记录

### 7.1 PowerShell governancePatterns 匹配

**问题**: `\.sadp\\` 模式的转义很敏感。`"\\.sadp\\"` 要求 .sadp 前有反斜杠，但 `.sadp` 在路径开头时没有前导反斜杠。

**解法**: 使用 `"\.sadp\\"` (单一反斜杠转义点号 + 双反斜杠匹配路径分隔符)。

**验证**: `python -m pytest tests/test_sadp_pre_task_enforcer.py::TestAuditPolicySmoke -v`

### 7.2 剪贴板操作

**问题**: `System.Windows.Forms.Clipboard` 在 PowerShell 中不可用 (TypeNotFound)。

**解法**: 使用 `Set-Clipboard -Value $content` (PowerShell 5.0+ 内置)。

### 7.3 Classification 标签不一致

**问题**: Registry 用 `binding_status: "pending_binding"` 但分类器只检查 `"pending_manual_binding"`。

**解法**: R12 已修复，两处都归一化为 `non_dispatchable_pending`。见 `dry_run_dispatch_10.py` 的 `_classify_packet()`。

### 7.4 Protected file 路径

**问题**: `capability-inventory.md` 和 `sub-agent-dispatch-protocol.md` 实际路径需要 `docs/agent-runtime/` 前缀。

**解法**: R9 smoke test 发现并修复。SADP_POLICY.json 和 sadp_pre_task_enforcer.py 的 PROTECTED_FILES 必须使用完整相对路径。

### 7.5 Chrome CDP 连接

**问题**: Chrome 必须以 `--remote-debugging-port=9222` 启动，且使用共享 profile 目录。

**解法**: 使用 `scripts/multi_cdp_launcher.py` 启动，它会自动设置正确的 flags 和 profile path。

---

## 8. 测试套件概览

| 测试文件 | 测试数 | 覆盖范围 |
|----------|:------:|----------|
| test_sadp_pre_task_enforcer.py | 63 | 强制器 + 策略漂移 + 审计 smoke |
| test_dry_run_dispatch_v2.py | 18 | 分类 + 碰撞 + 归一化 |
| test_tab_target_resolver.py | 22 | CDP 验证 + URL 规范 + 边界 |
| test_cross_project_scaffold.py | ~40 | 跨项目脚手架 |
| test_conversation_registry.py | ~30 | 对话注册表 |
| test_multi_project_isolation.py | ~20 | 多项目隔离 |
| test_router_10_project_stress.py | ~15 | 10 项目路由压力 |
| test_gate0_preflight_v2.py | ~15 | Gate0 预检 v2 |
| test_dispatch_packet_v2.py | ~10 | 派遣包 fail-closed |
| test_human_decision_record.py | ~25 | 人工决策记录 |
| test_state_machine_runtime.py | ~15 | 状态机运行时 |
| 其他 50+ 文件 | ~565 | 论文、内存、handoff 等 |
| **总计** | **1038** | **0 failed, 21 warnings** |

---

## 9. Universal Agent Workflow Standard (交叉引用)

本操作手册与 Universal Agent Workflow Standard 配套使用。Standard 将 R15-R18 的治理经验提炼为项目无关的通用规范：

| 标准文档 | 用途 |
|----------|------|
| [universal-agent-workflow-standard.md](universal-agent-workflow-standard.md) | 主标准：8 大治理规范总览 |
| [startup-read-gate.md](startup-read-gate.md) | 启动读取门控：agent 开工前必读清单 |
| [pre-task-gate.md](pre-task-gate.md) | 任务前门控：write_set/TaskSpec 验证 |
| [pre-gpt-review-gate.md](pre-gpt-review-gate.md) | GPT 审核前门控：证据包最低要求 |
| [evidence-pack-standard.md](evidence-pack-standard.md) | 证据包标准：文件清单和验证规则 |
| [status-state-machine.md](status-state-machine.md) | 状态机：任务生命周期 10 态转换 |
| [human-required-decision-record.md](human-required-decision-record.md) | 人工决策记录：9 类强制授权触发器 |
| [workspace-closure-standard.md](workspace-closure-standard.md) | 工作区闭合标准：clean/registered/dirty 三态 |
| [evidence-generation-hygiene.md](evidence-generation-hygiene.md) | 证据生成卫生：防止递归 artifact 污染 |

**使用方式**：本手册是项目级操作参考（what to do），Standard 是治理规范（how to do it right）。新 session 应先读本手册了解工具，再读 Standard 了解规则。

---

## 10. 版本历史和变更日志

| 日期 | Round | 变更 | 作者 |
|------|:-----:|------|------|
| 2026-06-10 | R13 | 初始版本，基于 R1-R13 开发经验 | QoderWork |
| 2026-06-11 | R18 | 添加 §9 Universal Agent Workflow Standard 交叉引用 | UNIVERSAL-AGENT-WORKFLOW-STANDARD-A1 |

---

## 11. 下一步改进 (P2)

1. **公用函数提取**: `_utc_now()`, `load_registry()`, `load_binding()` 提取到 `scripts/lib/common.py`
2. **Workspace 脚本迁移**: 将有价值的 workspace 脚本整合到正式 scripts/
3. **操作手册自动化**: 将复用检查清单集成到 `sadp_pre_task_enforcer.py` 的 pre_task 检查中
4. **测试覆盖**: 为每个 SOP 添加集成测试
