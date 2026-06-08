#!/usr/bin/env python3
"""
verify_gpt_reply.py — P0 guard: No captured GPT reply, no verdict.

Enforces GPT_RESPONSE_BINDING_RULE. Blocks agent summary-based verdicts.
Usage: python scripts/verify_gpt_reply.py <reply_file> [task_id]
"""
import hashlib, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def verify(reply_path: str) -> dict:
    """Verify a captured GPT reply. Returns verdict dict. Fail-closed."""
    fp = Path(reply_path)
    if not fp.exists():
        return {"valid": False, "overall_judgment": None, "errors": [f"reply file not found: {reply_path}"], "checks": {}, "verdict_allowed": False, "source": "captured_gpt_response"}

    content = fp.read_text(encoding="utf-8")
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()

    checks = {}
    errors = []

    # 1. END_OF_GPT_RESPONSE marker
    checks["has_end_marker"] = "END_OF_GPT_RESPONSE" in content
    if not checks["has_end_marker"]:
        errors.append("missing END_OF_GPT_RESPONSE")

    # 2. overall_judgment present and valid
    m = re.search(r"overall_judgment:\s*(\S+)", content, re.IGNORECASE)
    if not m:
        errors.append("missing overall_judgment")
        judgment = None
    else:
        judgment = m.group(1).strip().lower()
        valid = {"accepted", "accepted_with_limitation", "blocked", "review_unverified"}
        if judgment not in valid:
            errors.append(f"invalid overall_judgment: {judgment}")
        checks["overall_judgment"] = judgment

    # 3. evidence_pack_reviewed flag
    checks["evidence_pack_reviewed"] = "evidence_pack_reviewed: true" in content.lower()

    # 4. blocking_issues if blocked
    checks["has_blocking_issues"] = "blocking_issues:" in content

    # 5. next_task_authorization if accepted
    checks["has_next_task_auth"] = "next_task_authorization:" in content.lower()

    valid = len(errors) == 0 and checks["has_end_marker"] and judgment is not None

    return {
        "valid": valid,
        "overall_judgment": judgment,
        "errors": errors,
        "checks": checks,
        "sha256": sha[:32] + "...",
        "size": len(content),
        "verdict_allowed": valid,
        "source": "captured_gpt_response",
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: verify_gpt_reply.py <reply_file> [task_id]")
        sys.exit(1)

    reply_path = sys.argv[1]
    task_id = sys.argv[2] if len(sys.argv) > 2 else "UNKNOWN"

    result = verify(reply_path)
    result["task_id"] = task_id

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if not result["valid"]:
        print(f"\nGUARD BLOCKED: GPT reply for {task_id} is not valid.")
        print(f"Errors: {result.get('errors', [])}")
        print("No binding, no commit, no status report allowed.")
        sys.exit(1)

    print(f"\nGUARD OK: GPT reply for {task_id} is valid.")
    print(f"Verdict: {result['overall_judgment']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
