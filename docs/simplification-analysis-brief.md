# 跨项目兼容层精简化分析

> 提交网页版深度分析 | 2026-05-30

## 一、背景

刚完成了一个 4 阶段跨项目兼容层设计（11 文件 ~800 行），现质疑是否过度工程化。

## 二、两个 frame 的真实状态

- dev-frame：休眠，R3 适配器候选，无数据流，不是 git repo
- test-frame：休眠，R2 证据源候选，无执行，无数据流向 agent-acceptance

两个项目的共同特点：被登记但从未活跃。

## 三、自我质疑：一半有用，一半画蛇添足

### 确实有用的（4 项）

1. EvidenceIndex freshness 扩展 — 修复了 status=collected 和历史数据语义混乱
2. Authority Matrix — 把外部 frame 不得生产 GateResult 从隐性变显式
3. 契约演进策略 — 改 TaskSpec 时有据可查
4. boundary-envelope.schema.json — 轻量跨项目数据契约

### 画蛇添足的（5 项）

1. 两个 frame-manifest.yaml — 给休眠项目写声明文件
2. path drift scanner — 68 个自引用警告，零实际价值
3. --strict 模式 — 把噪声升级为 BLOCKED
4. 整个准入层的紧迫性 — 等 frame 活跃时才需要
5. accepted_frames — 描述的是不发生的数据流

## 四、提议的精简方案

- 删除 3：两个 frame-manifest.yaml + path drift scanner
- 简化 2：checker 精简（去 path drift + --strict）+ lock 中 accepted_frames 改 registered_frames/inactive
- 保留 7：schema 模板 + freshness + authority-matrix + 演进策略 + 文档引用

## 五、核心问题

1. 这个精简方案是否合理？有没有该删没删的？
2. 预先设计但暂不激活的机制，什么条件下算技术债、什么条件下算合理前瞻？
3. 休眠集成场景下，为未来设计的合理边界在哪？留 schema 模板就够，还是 checker 也不该写？
