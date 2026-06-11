当前进展可以重新定性为：

YAML
overall_status: v2_shared_cdp_architecture_ready
architecture_mode: single_chrome_shared_cdp
cdp_port: 9222
login_strategy: shared_profile_one_time_login
current_active_projects: 1
pending_slots: 9
test_status: 852 passed
live_multi_project_dispatch: not_yet_authorized
next_priority: redefine_isolation_model_then_bind_real_projects

你们现在已经从原来的 “10 个 Chrome / 10 个 CDP port / 10 个 profile” 路线，转向了更现实的 “单 Chrome 共享 CDP + 多 GPT conversation 逻辑隔离” 路线。这个调整是合理的，因为它解决了之前最大的现实阻塞：每个独立 profile 都要单独登录，并且容易遇到 Cloudflare challenge。

一、当前进度评估

现在基础设施已经比较成熟，可以认为 v2 架构基础可用。

已经就绪的能力包括：

1. 单 Chrome 共享 CDP 已验证可用；
2. 共享 profile 可以复用登录态，避免 10 个 profile 逐个登录；
3. /bindChrome skill 已就绪，可以把真实 Chrome 会话绑定到 AWSP；
4. /rdinit skill 已就绪，可以快速为项目初始化治理框架；
5. PROJECT_REGISTRY 已具备 1 active + 9 pending 的结构；
6. 全量测试 852 passed，说明原有 registry、router、Gate0、dry-run、workflow scaffolding 没有明显回归。

但要注意：架构性质已经变了。

之前追求的是：

项目级物理隔离：
project → independent Chrome profile → independent CDP port → independent GPT conversation

现在变成：

项目级逻辑隔离：
project → shared Chrome/CDP/profile → dedicated GPT conversation/tab → run_id/task_id/capture binding

所以，后续不能再用“profile_collision”作为阻断 live dispatch 的核心标准。否则 v2 架构会天然一直被判定为 collision。现在应该把验收重点转到：

conversation_id 唯一
chat_url 唯一
tab target 可精确定位
run_id/task_id 精确匹配
禁止 last-message-only capture
项目 evidence pack 互不串联
dispatch packet 绑定正确 conversation

一句话：v2 不再追求 profile 隔离，而要强化 conversation/tab/run_id 层面的隔离。

二、当前最大风险

v2 共享 CDP 的最大风险不是 profile 冲突，而是 捕获串话。

主要风险有：

1. 多个项目共用同一个 Chrome，如果 capture 只拿最后一个 assistant message，极易串项目；
2. 一个 Chrome 里多个 ChatGPT tab，如果没有 target/page 精确绑定，可能向 A 项目对话提交 B 项目任务；
3. 共享登录态意味着账号层面无隔离，不能用 profile 隔离作为安全边界；
4. 10 个项目如果同时触发 GPT review，页面加载、响应等待、capture 都可能互相影响；
5. 单 Chrome 崩溃会影响所有项目；
6. ChatGPT 侧频率限制、页面状态、会话刷新都会成为共享瓶颈。

所以，v2 的核心不是再开 10 个 Chrome，而是要建立：

conversation-level isolation
tab-level target resolution
capture-level anti-cross-talk guard
bounded concurrency
三、下一步最高优先级
P0：先冻结 v2 架构标准

下一步第一件事应该是：

AWSP-SHARED-CDP-ARCHITECTURE-V2-BASELINE-A1

目标：把架构标准从“multi CDP physical isolation”正式切换为“single Chrome shared CDP logical isolation”。

这个任务必须明确：

1. shared profile 是设计选择，不再视为 profile_collision blocker；
2. profile_collision 在 v2 中降级为 known_architecture_tradeoff；
3. v2 的强隔离边界改为 conversation_id / chat_url / page_target_id / run_id / task_id；
4. live dispatch 的前置条件不再是 unique profile，而是 unique conversation + exact tab target + capture verification；
5. 单 Chrome 共享 CDP 的并发上限需要受 resource policy 控制。

没有这个 baseline，后续 Gate0 仍会按照旧规则把共享 profile 判为 collision，从而阻断所有 live dispatch。

四、下一步任务优先级路线
Priority 1：重写 Gate0 规则，适配 shared CDP v2

任务名建议：

SHARED-CDP-GATE0-PREFLIGHT-V2-A1

验收目标：

1. 允许多个项目共享 cdp_endpoint=http://localhost:9222；
2. 允许多个项目共享 browser_profile_id；
3. 不再因 profile 相同直接判 non_dispatchable_collision；
4. 必须检查每个 active 项目的 conversation_id 唯一；
5. 必须检查每个 active 项目的 chat_url 唯一；
6. 必须检查 CDP /json 页面列表中存在对应 conversation URL；
7. 必须生成 page_target_id / targetId 绑定；
8. 如果找不到精确 tab，项目必须 human_required；
9. 如果多个 tab 匹配同一 conversation，项目必须 blocked；
10. 如果 conversation_id 重复，必须 blocked。

这个任务是目前最关键的工程转向。

Priority 2：建立 tab target resolver

任务名建议：

SHARED-CDP-TAB-TARGET-RESOLVER-A1

目标：在单 Chrome 多 tab 下，精确找到每个项目对应的 ChatGPT tab。

核心输出：

JSON
{
  "project_id": "project-alpha",
  "agent_id": "agent-alpha",
  "conversation_id": "...",
  "chat_url": "https://chatgpt.com/c/...",
  "cdp_endpoint": "http://localhost:9222",
  "target_id": "...",
  "target_url": "...",
  "match_status": "exact_match"
}

通过标准：

1. exact conversation URL 能匹配到唯一 target；
2. 无匹配 → human_required；
3. 多匹配 → blocked；
4. 非 ChatGPT 页面不能被绑定；
5. 不能 fallback 到最后一个 tab；
6. 不能 fallback 到当前激活 tab；
7. target_id 必须进入 dispatch packet 和 capture evidence。

这是 v2 的核心安全组件。

Priority 3：升级 dispatch packet

任务名建议：

SHARED-CDP-DISPATCH-PACKET-V2-A1

之前 packet 只需要 project_id、agent_id、chat_url、run_id、task_id。现在必须加：

target_id
target_url
conversation_id
capture_policy
expected_run_id
expected_task_id
expected_end_marker
forbid_last_message_only_capture=true

并且 packet 需要明确：

dispatch_mode: dry_run | human_gated_live
cdp_mode: shared_single_chrome
isolation_model: conversation_target_bound
Priority 4：做 2 项目真实 GPT conversation 绑定

任务名建议：

SHARED-CDP-REAL-GPT-BINDING-2-A1

目标不是开 10 个，而是在同一个 Chrome 里先绑定 2 个真实 GPT conversation：

agent-acceptance → conversation A → target A
project-alpha → conversation B → target B

通过标准：

1. 两个项目都 active；
2. 两个 conversation_id 不同；
3. 两个 chat_url 不同；
4. 两个 target_id 不同；
5. 两个 target_url 精确匹配；
6. Gate0 v2 PASS；
7. dry-run dispatchable=true；
8. packets_sent=0。

完成这一步以后，才算 v2 架构真正进入可试运行状态。

Priority 5：live dispatch 仍然只允许 2 项目小规模试验

任务名建议：

SHARED-CDP-GPT-REVIEW-LIVE-2-A1

必须 human-gated。

通过标准：

1. 只允许 2 个项目；
2. 每个项目一个真实 GPT conversation；
3. 每个项目一个唯一 target_id；
4. 每次发送前重新 resolve target；
5. 发送后只从该 target 对话捕获；
6. 回复必须匹配 run_id；
7. 回复必须匹配 task_id；
8. 回复必须包含 END marker；
9. 不能读取最后一个 assistant message 作为依据；
10. evidence pack 必须绑定 project_id / agent_id / target_id / run_id。
五、10 项目扩展的推荐节奏

不要立刻 10 个项目全部 active。建议：

1 active → 2 active → 4 active → 6 active → 10 active

每一档都做 Gate0 v2 + dry-run，不直接 live dispatch。

2 active

目标：证明 v2 的 conversation/tab 隔离可行。

4 active

目标：证明多 tab 下 target resolver 不串。

6 active

目标：观察 Chrome 资源压力和 ChatGPT 页面稳定性。

10 active

目标：做全量 dry-run，不建议立刻全量 live。

六、当前 9 个 pending 虚拟项目如何处理

现在 9 个 pending 是虚拟项目，等待真实项目替换。这个状态是可以接受的，但下一步应做一个 registry 清理任务：

PROJECT-REGISTRY-REAL-PROJECT-REPLACEMENT-A1

目标：

1. 保留 10 个槽位；
2. 把虚拟 project-beta ~ project-iota 替换为真实项目 ID；
3. 每个真实项目运行 /rdinit；
4. 每个项目生成自己的 .agent 配置；
5. 每个项目先保持 pending_manual_binding；
6. 不创建假的 conversation_id；
7. 不标记 active。

优先级上，它排在 Gate0 v2 和 Target Resolver 之后，或者并行做也可以。

七、自动化与 human-gated 边界
可以自动化
/rdinit 初始化项目治理框架
PROJECT_REGISTRY 更新
pending project scaffold 创建
conversation binding schema validation
CDP /json 页面列表读取
target resolver 匹配
Gate0 v2 分类
dry-run packet 构建
capture policy 检查
测试与 evidence pack 打包
必须 human-gated
创建新的 ChatGPT conversation
确认某个 conversation 属于哪个 project
把 pending_manual_binding 改为 active
首次 live dispatch
多项目并发 live dispatch
删除或重置 Chrome profile
关闭共享 Chrome 会话
严禁自动化
伪造 conversation_id
伪造 chat_url
把未验证 tab 的项目标为 active
用当前 tab 代替绑定 tab
用最后一条 assistant message 作为 verdict
多个项目共享同一个 conversation
绕过 Gate0 v2 直接发送 GPT review
八、建议 acceptance 路线图

按优先级排序：

P0  SHARED-CDP-ARCHITECTURE-V2-BASELINE-A1
P0  SHARED-CDP-GATE0-PREFLIGHT-V2-A1
P0  SHARED-CDP-TAB-TARGET-RESOLVER-A1
P0  SHARED-CDP-DISPATCH-PACKET-V2-A1
P1  SHARED-CDP-REAL-GPT-BINDING-2-A1
P1  SHARED-CDP-GPT-REVIEW-DRY-RUN-2-A1
P1  SHARED-CDP-GPT-REVIEW-LIVE-2-A1
P2  PROJECT-REGISTRY-REAL-PROJECT-REPLACEMENT-A1
P2  SHARED-CDP-REAL-GPT-BINDING-4-A1
P2  SHARED-CDP-GPT-REVIEW-DRY-RUN-10-A1
P3  SHARED-CDP-GPT-REVIEW-LIVE-4-A1
P3  SHARED-CDP-GPT-REVIEW-LIVE-10-A1
九、最终判断

你们现在的进度不是“倒退”，而是做了一个更现实的架构收敛：

从 10 Chrome 物理隔离
收敛到 1 Chrome 共享登录态 + 多 conversation 逻辑隔离

这个方向更适合快速进入多 agent / 多 GPT 工作模式。

当前最优先的不是继续开端口，也不是继续做 10 profile 登录，而是立刻把验收体系改成 v2：

共享 CDP 允许
共享 profile 允许
conversation 必须唯一
tab target 必须唯一
capture 必须绑定 run_id/task_id

一句话：基础设施已就绪，下一步要做 v2 Gate0 和 Tab Target Resolver。只要这两个通过，就可以安全进入 2 项目 shared-CDP live pilot。