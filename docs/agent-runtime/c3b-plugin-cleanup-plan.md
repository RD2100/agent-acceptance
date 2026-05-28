# C3B — Plugin 清理执行计划

> **批次**: C3B  
> **日期**: 2026-05-28  
> **前置**: C3A 批量安装了 15 个插件（报告: `reports/plugin-install-report-2026-05-28.md`）  
> **目标**: 18 → 9 个插件，精简到项目真正需要的集合  
> **执行方式**: 直接执行 `codex plugin disable`，无需二次审核

---

## 审核决策（已在本批次完成，无需重审）

| 插件 | 推荐等级 | 决策 | 理由 |
|------|----------|------|------|
| coderabbit | 强烈 | ✅ 保留 | 直接补强 `rules/review.md`，AI 代码审查自动化 |
| codex-security | 强烈 | ✅ 保留 | 对应 `rules/security.md` 硬停规则 |
| sentry | 强烈 | ✅ 保留 | Runtime 异常追踪，补强 `diagnose` |
| supabase | 强烈 | ✅ 保留 | 后续数据层需求 |
| linear | 有条件 | ✅ 保留 | 项目管理，选 linear（不要 clickup/asana） |
| notion | 有条件 | ✅ 保留 | 文档协作，Phase 1+ 可重新评估 |
| clickup | 有条件 | ❌ 禁用 | 与 linear 功能冗余（三选一） |
| asana | 有条件 | ❌ 禁用 | 与 linear 功能冗余（三选一） |
| slack | 有条件 | ❌ 禁用 | 缺少凭证，Phase 1+ 按需启用 |
| teams | 有条件 | ❌ 禁用 | 缺少凭证，且非 Microsoft 生态 |
| datadog | 有条件 | ❌ 禁用 | 缺少凭证，Phase 2+ 再评估 |
| temporal | 有条件 | ❌ 禁用 | Phase 2+ 复杂流水线时再启用 |
| circleci | 有条件 | ❌ 禁用 | Phase 2+ CI/CD 部署时再启用 |
| cloudflare | 有条件 | ❌ 禁用 | Phase 2+ 部署时再启用 |
| render | 有条件 | ❌ 禁用 | Phase 2+ 部署时再启用 |

---

## 执行命令（共 9 条，直接复制运行）

```powershell
codex plugin disable clickup@openai-curated
codex plugin disable asana@openai-curated
codex plugin disable slack@openai-curated
codex plugin disable teams@openai-curated
codex plugin disable datadog@openai-curated
codex plugin disable temporal@openai-curated
codex plugin disable circleci@openai-curated
codex plugin disable cloudflare@openai-curated
codex plugin disable render@openai-curated
```

---

## 预授权声明

以下操作已被本计划预授权，执行智能体 **无需再次请求批准**：

1. **`C:\Users\RD\.codex\config.toml` 的 disable-only 修改** — `codex plugin disable` 会自动更新 `disabled_plugins` 列表，这是预期行为
2. **插件缓存目录** — disable 不会删除 `C:\Users\RD\.codex\plugins\cache\` 下的文件，仅标记禁用

---

## 硬停规则（执行智能体必须遵守）

| # | 规则 | 说明 |
|---|------|------|
| 1 | ❌ 不安装新插件 | 仅执行 disable，不 `plugin add` |
| 2 | ❌ 不修改 MCP 配置 | 不碰 `mcp.json` 或 settings |
| 3 | ❌ 不修改 settings.json | 禁写 Codex settings |
| 4 | ❌ 不写 memory | Phase 0-5 memory 只读 |
| 5 | ❌ 不执行 git 操作 | 不 commit/stash/reset/push |
| 6 | ❌ 不删除任何文件 | disable ≠ delete |

---

## 最终状态

```
启用: 9 个
  原有: browser, superpowers, github
  强推: coderabbit, codex-security, sentry, supabase
  保留: linear, notion

禁用: 9 个
  clickup, asana, slack, teams, datadog, temporal, circleci, cloudflare, render
```

---

## 验证指令

执行完成后，运行以下命令验证：

```powershell
codex plugin list 2>$null | Select-String -Pattern "installed, enabled" | Measure-Object | ForEach-Object { Write-Output "Enabled: $($_.Count)" }
codex plugin list 2>$null | Select-String -Pattern "installed, disabled" | Measure-Object | ForEach-Object { Write-Output "Disabled: $($_.Count)" }
```

期望输出：`Enabled: 9` / `Disabled: 9`（共 18 个已安装）。

---

## 执行报告模板（执行智能体填写后回传）

```
### C3B 执行报告

- 日期: 
- 执行人: [agent name]
- 命令: 9 条 disable
- 成功: /9
- 失败: /9
- 最终启用数: 
- 最终禁用数: 
- 异常:
  - [如有，逐条列出]
- config.toml 变更确认:
  - [ ] disabled_plugins 列表已更新
  - [ ] 无其他意外变更
- 判定: PASS / FAILED / BLOCKED
```
