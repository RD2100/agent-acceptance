# docs/agent-runtime/ 的 Schema 引用完整性验证

> 验证日期: 2026-05-28
> 方法: 提取 docs/agent-runtime/ 下所有 .md 文件中的 .schema.json 引用 → 逐一验证在 schemas/ 目录中的存在性

## 验证结果：全部通过

**所有被引用的 schema 文件均真实存在。未发现断链。**

## 引用清单（19 个 schema，全部验证通过）

### schemas/agent-runtime/ (9 个)

| # | Schema 文件名 | 在 docs 中被引用 | 存在 | 路径 |
|---|-------------|:---:|:---:|------|
| 1 | source-lock-record.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 2 | task-spec.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 3 | run-spec.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 4 | evidence-index.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 5 | gate-result.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 6 | execution-report.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 7 | skill-intake-record.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 8 | tool-risk-record.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |
| 9 | memory-update-record.schema.json | ✅ | ✅ | `schemas/agent-runtime/` |

### schemas/resource-integration/ (10 个)

| # | Schema 文件名 | 在 docs 中被引用 | 存在 | 路径 |
|---|-------------|:---:|:---:|------|
| 10 | resource-registry-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 11 | capability-promotion-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 12 | capability-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 13 | capability-routing-audit-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 14 | evidence-provider-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 15 | dev-frame-adapter-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 16 | codegraph-index-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 17 | local-skill-intake-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 18 | memory-context-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |
| 19 | script-safety-record.schema.json | ✅ | ✅ | `schemas/resource-integration/` |

## 引用分布（按文档）

| 文档 | 引用 schema 数 |
|------|:--:|
| resource-integration-final-audit.md | 18 |
| resource-integration-status-index.md | 18 |
| resource-integration-reviewer-playbook.md | 10 |
| r0-negative-tests.md | 2 |
| r0-reviewer-checklist.md | 2 |
| reviewer-playbook.md | 2 |
| runtime-v2-final-status.md | 9 |
| r5-local-skill-reviewer-checklist.md | 1 |
| r6-memory-reviewer-checklist.md | 1 |
| r7-acceptance-native-reviewer-checklist.md | 1 |
| phase-6-source-lock-quarantine.md | 2 |
| phase-6b-handoff.md | 2 |
| phase-6b-source-lock-plan.md | 1 |
| capability-routing-handoff.md | 2 |
| test-frame-evidence-provider.md | 1 |
| resource-registry.md | 1 |
| cr0-capability-inventory-reviewer-checklist.md | 1 |
| capability-routing-final-audit.md | 2 |

## 结论

- **引用总数**: 19 个唯一 schema 名称
- **断链数**: 0
- **路径不匹配**: 0（所有引用路径与实际文件路径一致）
- **验证状态**: ALL PASS
