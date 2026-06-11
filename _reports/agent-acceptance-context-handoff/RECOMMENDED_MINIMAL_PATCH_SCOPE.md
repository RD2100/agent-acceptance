# RECOMMENDED_MINIMAL_PATCH_SCOPE — 建议最小修改范围

> Generated: 2026-06-02
> **注意**: 只列建议，不执行修改。修改需用户和GPT确认后执行。

## 核心原则

- 只修改 agent-acceptance 规范层
- 不修改 dev-frame-opencode
- 不做大重构
- 优先新增文件而非大改现有文件
- 保持向后兼容（现有P0-P3 gate仍有效）

## 1. 需要修改的文件（agent-acceptance）

### 1.1 修改: `docs/agent-runtime/reviewer-playbook.md` §8 Gate Decision Tree

**改什么**:
- 将末尾兜底 "Is a human decision needed? → human_required" 替换为结构化的 human_required 分类检查
- 新增 auto decision 分支: 如果所有 human_required 类别均未触发 → auto_advance

**为什么改**: 消除 "一切模糊情况 → human_required" 的兜底逻辑

**需要用户确认**: 是（修改治理相关文件）

### 1.2 修改: `docs/agent-runtime/reviewer-playbook.md` §10 Step 10

**改什么**:
- human_required 从单值改为结构化对象:
```yaml
human_required:
  triggered: true | false
  categories: [direction_decision | sensitive_operation | irreversible | ...]
```
- 新增 auto_decision 判定

**为什么改**: dev-frame-opencode 需要知道 human_required 的具体类别

**需要用户确认**: 是

### 1.3 修改: `docs/agent-runtime/authority-matrix.md`

**改什么**:
- "Auto-Advance Gate: Yes (with reviewer)" → 细化为 "Yes (auto when stage gate clean, reviewer required when human_required categories triggered)"

**为什么改**: 当前声明过于严格，不允许任何纯自动推进

**需要用户确认**: 是（修改治理相关文件）

## 2. 需要新增的文件（agent-acceptance）

### 2.1 新增: `docs/agent-runtime/stage-gate-definition.md`

**内容**:
- 定义 S2/S3/M4-A 三个阶段
- 每个阶段的进入条件
- 每个阶段的退出条件
- stage gate 判定逻辑

**为什么新增**: 当前项目没有阶段概念

**需要用户确认**: 是（新增治理文件）

### 2.2 新增: `docs/agent-runtime/human-required-taxonomy.md`

**内容**:
- 结构化 human_required 分类
- 每个类别的触发条件
- 每个类别的处理方式

**为什么新增**: 当前 human_required 无分类

**需要用户确认**: 是

### 2.3 新增: `docs/agent-runtime/auto-decision-log.schema.md`

**内容**:
- AUTO_DECISION_LOG 的 YAML schema
- 必需字段和可选字段
- 与 stage gate / loop state 的关联规则

**为什么新增**: 当前无此概念

**需要用户确认**: 是

### 2.4 新增: `docs/agent-runtime/sensitive-operation-classification.md`

**内容**:
- 需要人工确认的操作清单
- 可自动执行的操作清单
- 介于两者之间的灰度操作处理规则

**为什么新增**: 需要集中定义敏感操作分类

**需要用户确认**: 是

### 2.5 新增: `schemas/agent-runtime/stage-gate-result.schema.json`

**内容**:
- JSON Schema for `stage_gate_result`
- 包含: stage_id, decision, allow_next_stage, s3_allowed, auto_decision, human_required_categories

**为什么新增**: dev-frame-opencode 需要稳定的解析格式

**需要用户确认**: 否（纯技术新增，不影响现有规则）

### 2.6 新增: `schemas/agent-runtime/auto-decision-log.schema.json`

**内容**:
- JSON Schema for `auto_decision_log`

**为什么新增**: AUTO_DECISION_LOG 需要稳定格式

**需要用户确认**: 否（纯技术新增）

## 3. 不建议修改的文件

| 文件 | 原因 |
|------|------|
| `rules/core.md` | P0规则与stage gate不冲突，保持原样 |
| `rules/security.md` | 安全规则独立于阶段推进 |
| `rules/git.md` | 不可逆操作规则仍然有效 |
| `rules/review.md` | 证据规则仍然有效 |
| `rules/coding.md` | 代码规范不受影响 |
| `runtime-invariants.md` | 40条不变量全部有效 |
| `verification-gates.md` | P0-P3 gate仍有效，新增stage gate不冲突 |
| `sub-agent-dispatch-protocol.md` | SADP是任务级协议，与阶段推进是不同层面 |
| `operating-model.md` | Tier系统与stage gate是不同概念 |
| `AGENTS.md` | 已够复杂，避免大改 |
| `integration-contracts.md` | 8个核心合约保持稳定 |
| `schemas/agent-runtime/*.json` (除新增) | 现有schema不修改 |

## 4. agent-acceptance vs dev-frame-opencode 修改分工

| 修改 | 归属 |
|------|------|
| Stage gate 定义 | agent-acceptance |
| human_required 分类 | agent-acceptance |
| AUTO_DECISION_LOG schema | agent-acceptance |
| Stage gate result schema | agent-acceptance |
| 修改 reviewer-playbook.md | agent-acceptance |
| 修改 authority-matrix.md | agent-acceptance |
| Loop harness 消费 stage gate result | dev-frame-opencode |
| AUTO_DECISION_LOG 生成逻辑（填充值） | dev-frame-opencode |
| 阶段自动推进执行逻辑 | dev-frame-opencode |
| GPT reply monitor | dev-frame-opencode |
| Chrome CDP handoff | dev-frame-opencode |
| Evidence pack 生成 | dev-frame-opencode |

## 5. 需要用户确认的事项

1. S2/S3/M4-A 阶段的具体定义（阶段边界、进入/退出条件）
2. human_required 分类是否接受建议的分类体系
3. AUTO_DECISION_LOG 的存储位置和格式
4. 是否接受 "自动推进仅当所有 human_required 类别均未触发" 的规则
5. 是否需要在 agent-acceptance 中定义 "sensitive operation" 清单

## 6. 不需要用户确认的事项（纯技术新增）

1. JSON Schema 文件新增（stage-gate-result, auto-decision-log）
2. YAML schema 文档新增（auto-decision-log.schema.md）
3. 文件内部的字段定义（不改变语义的）

## 7. 最小可行路径（MVP）

如果只做最小改动：

1. 新增 `docs/agent-runtime/stage-gate-definition.md`（1个文件）
2. 新增 `docs/agent-runtime/human-required-taxonomy.md`（1个文件）
3. 修改 `reviewer-playbook.md` Gate Decision Tree（1处改动）
4. 新增 `schemas/agent-runtime/stage-gate-result.schema.json`（1个文件）

共: 3个新文件 + 1处改动 ≈ 最小 patch
