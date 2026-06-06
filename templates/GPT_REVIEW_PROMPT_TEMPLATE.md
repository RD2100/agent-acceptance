# GPT Review Prompt Template

> template_version: gpt-review-template-v1
> Authority: agent-acceptance
> Consumers: all GPT review prompts for any task type
> Usage: Copy this template, fill placeholders, add task_type_specific fields.

---

## Instructions for the Prompt Author

1. Copy this template into your GPT_REVIEW_PROMPT.md.
2. Replace all `{{PLACEHOLDER}}` values.
3. Under `## Task-Specific Context`, describe what GPT must judge.
4. Under `task_type_specific`, define the review dimensions unique to this task type.
5. The `## Required Reply Format` section MUST remain unchanged — this is the canonical schema.
6. Submit the evidence pack ZIP with this prompt as the first file.

---

## Evidence Pack Context

| Field | Value |
|-------|-------|
| REVIEW_RUN_ID | `{{REVIEW_RUN_ID}}` |
| task_type | `{{TASK_TYPE}}` |
| review_stage | `{{REVIEW_STAGE}}` |
| contract_id | `{{CONTRACT_ID_OR_NULL}}` |
| contract_version | `{{CONTRACT_VERSION_OR_NULL}}` |
| evidence_pack_path | `{{PACK_PATH}}` |
| evidence_pack_sha256 | `{{PACK_SHA256_OR_NULL}}` |
| submitted_at | `{{ISO8601_TIMESTAMP}}` |

## Evidence Pack Contents

| File | Role | SHA256 |
|------|------|--------|
| `{{FILE_PATH}}` | `{{ROLE}}` | `{{SHA256_OR_NULL}}` |
<!-- Repeat for each file in pack -->

## Task-Specific Context

<!-- Describe: what was done, what GPT must judge, relevant constraints -->

{{TASK_SPECIFIC_CONTEXT}}

## The base fields below are mandatory for ALL task types.
## Fields marked `| null` are optional: use `null` (YAML null, no quotes) when not applicable.

```yaml
REVIEW_RUN_ID: "{{REVIEW_RUN_ID}}"
template_version: "gpt-review-template-v1"
task_type: "{{TASK_TYPE}}"
review_stage: "{{REVIEW_STAGE}}"
overall_judgment: "accepted | blocked | human_required | review_unverified"
reviewer_type: "gpt | human | agent"
contract_id: {{CONTRACT_ID_OR_NULL}}
contract_version: {{CONTRACT_VERSION_OR_NULL}}
# evidence_pack:  (optional — use null when no pack, or fill nested fields when present)
evidence_pack: null
#
# When present, replace null above with:
# evidence_pack:
#   path: "path/to/pack.zip"
#   sha256: "abc123..."
#   manifest_valid: true
evidence_inspected:
  - path: "{{FILE_PATH}}"
    sha256: {{SHA256_OR_NULL}}
    inspected: true | false
    role: "{{ROLE}}"
blocking_reasons: []
missing_evidence: []
scope_violation: true | false
fake_green_risk: true | false
safety_boundaries_respected: true | false
required_next_action: "{{CONCRETE_STEP}}"
allow_proceed: true | false
review_unverified_reason: {{REASON_OR_NULL}}
created_at: "{{ISO8601_TIMESTAMP}}"
rationale: "{{EXPLANATION}}"
task_type_specific:
  "{{TASK_TYPE}}":
    # The key above MUST match the task_type field value.
    # Schema enforces key is a valid task_type; application code
    # enforces key equals task_type field (JSON Schema limitation).
    # Task-specific fields defined by the prompt author below.
```

## Rules

- `overall_judgment: accepted` → `allow_proceed` MUST be `true`
- `overall_judgment: blocked` → `allow_proceed` MUST be `false`
- `overall_judgment: human_required` → `allow_proceed` MUST be `false` (unless explicitly authorized)
- `overall_judgment: review_unverified` → `allow_proceed` MUST be `false` AND `review_unverified_reason` MUST be non-null
- `blocking_reasons` MUST be `[]` (empty list), never the string `"none"`
- `missing_evidence` MUST be `[]` (empty list), never the string `"none"`
- `evidence_inspected` MUST list every evidence file GPT actually read
- If SHA256 is unavailable, use `null` — never invent a hash
- Agent summary is not evidence — GPT must inspect the actual files
- Do NOT suggest guard removal, evidence cleanup, or enabling live CDP by default
