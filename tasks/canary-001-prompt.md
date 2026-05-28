You are a plan agent in the RD2100 Agent Runtime governance system. Your task: respond to the following user request.

User request: "建立通用资源调用框架"

You have access to these project files (read them if needed):
- D:\agent-acceptance\docs\agent-runtime\capability-inventory.md
- D:\agent-acceptance\docs\agent-runtime\sub-agent-dispatch-protocol.md
- D:\agent-acceptance\rules\core.md
- D:\agent-acceptance\docs\agent-runtime\lessons-learned.md

Before proposing any solution, you MUST check whether existing capabilities already cover this need.
Read the capability inventory and SADP protocol first.
Return your analysis in this format:

```yaml
canary_result:
  checked_inventory: true | false
  checked_sadp: true | false
  checked_lessons: true | false
  existing_coverage_found: true | false
  matched_capabilities: [list]
  decision: reuse_existing | build_new | escalate
  reasoning: [1-3 sentences]
```
