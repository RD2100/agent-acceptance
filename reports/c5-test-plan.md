# Batch C5: Bootstrap 验收测试计划

你是编码智能体。执行以下 10 个测试，每个测试输出一行 PASS/FAIL。全部在 $env:TEMP 隔离执行，完成后清理。
不装插件、不改 config、不写 memory、不修改 D:\agent-acceptance 已有文件。

完整测试脚本位于: `reports/c5-test-plan.ps1`（如文件存在，直接运行：`powershell -EP Bypass -File reports/c5-test-plan.ps1`）

## 10 个测试场景

| # | 场景 | 验证内容 |
|---|------|---------|
| 01 | Fresh Project | 11 项检查：AGENTS.md, rules, schemas, capability-inventory, tool-policy, reviewer-playbook, fixtures |
| 02 | Dry-Run | 无文件写入 |
| 03 | Force Overwrite | -Force 覆盖已有文件 |
| 04 | Skip Without Force | 无 -Force 不覆盖，输出 SKIP |
| 05 | Auto-Detect Dir Name | 从目录名自动提取项目名 |
| 06 | Auto-Detect Git Remote | 从 git remote URL 提取项目名 |
| 07 | Platform=Claude | 平台参数正确写入 AGENTS.md |
| 08 | Placeholders | 3 个生成文件中无残留 {{ }} |
| 09 | JSON Schemas | 19 个 JSON Schema 全部可解析 |
| 10 | Inventory Structure | 8 项结构检查（Registration Procedure, Platform Key, Summary, Status Legend 等）|

## 执行方式

测试脚本在 `reports/c5-test-plan.ps1` 中。该脚本包含全部 10 个测试的完整 PowerShell 代码。
请在阅读该文件内容后，逐个执行每个测试块（TEST-01 到 TEST-10），或直接运行整个脚本：

```powershell
powershell -ExecutionPolicy Bypass -File D:\agent-acceptance\reports\c5-test-plan.ps1
```

## 报告模板

```
| 测试 | 结果 |
|------|:---:|
| TEST-01: Fresh Project | |
| TEST-02: Dry-Run | |
| TEST-03: Force Overwrite | |
| TEST-04: Skip Without Force | |
| TEST-05: Auto-Detect Dir Name | |
| TEST-06: Auto-Detect Git Remote | |
| TEST-07: Platform=Claude | |
| TEST-08: Placeholders | |
| TEST-09: JSON Schemas | |
| TEST-10: Inventory Structure | |
```

如果 reports/c5-test-plan.ps1 文件内容不完整或不可用，请通知 reviewer。
