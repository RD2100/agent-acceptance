#!/usr/bin/env python3
"""
verify_gpt_reply.py — P0 guard: No captured GPT reply, no verdict.

Enforces GPT_RESPONSE_BINDING_RULE. Blocks agent summary-based verdicts.
Usage: python scripts/verify_gpt_reply.py <reply_file> [task_id]
"""
import hashlib, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def verify(reply_path: str, expected_task_id: str = None) -> dict:
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
        valid_judgments = {"accepted", "accepted_with_limitation", "blocked", "review_unverified", "mixed_blocked", "mixed"}
        if judgment not in valid_judgments:
            errors.append(f"invalid overall_judgment: {judgment}")
        checks["overall_judgment"] = judgment

    # 3. evidence_pack_reviewed flag
    checks["evidence_pack_reviewed"] = "evidence_pack_reviewed: true" in content.lower()

    # 4. task_id matching — extract from reply, compare with expected
    tm = re.search(r"task_id:\s*(\S+)", content, re.IGNORECASE)
    reply_task_id = tm.group(1).strip() if tm else None
    checks["task_id_in_reply"] = reply_task_id
    if expected_task_id and reply_task_id:
        checks["task_id_matches"] = (expected_task_id.upper() == reply_task_id.upper())
        if not checks["task_id_matches"]:
            errors.append(f"task_id mismatch: expected {expected_task_id}, reply has {reply_task_id}")
    elif expected_task_id and not reply_task_id:
        checks["task_id_matches"] = False
        errors.append(f"task_id not found in reply (expected {expected_task_id})")

    # 5. next_task_authorization if accepted
    checks["has_next_task_auth"] = "next_task_authorization:" in content.lower()
    if judgment in ("accepted", "accepted_with_limitation") and not checks["has_next_task_auth"]:
        errors.append("accepted verdict missing next_task_authorization")

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


def closure_ready(reply_path: str, task_id: str) -> dict:
    """Check if task is ready for closure/binding based on GPT reply."""
    result = verify(reply_path, task_id)
    if not result["valid"]:
        return {"closure_ready": False, "reason": "GPT reply not valid", "verdict": result}
    judgment = result["overall_judgment"]
    if judgment in ("accepted", "accepted_with_limitation"):
        return {"closure_ready": True, "reason": f"GPT {judgment}", "verdict": result}
    if judgment == "blocked":
        return {"closure_ready": False, "reason": "GPT blocked — fix required before closure", "verdict": result}
    if judgment == "review_unverified":
        return {"closure_ready": False, "reason": "GPT review_unverified — more evidence needed", "verdict": result}
    return {"closure_ready": False, "reason": f"unknown judgment: {judgment}", "verdict": result}


def main():
    if len(sys.argv) < 2:
        print("Usage: verify_gpt_reply.py <reply_file> [task_id]")
        sys.exit(1)

    reply_path = sys.argv[1]
    task_id = sys.argv[2] if len(sys.argv) > 2 else None

    result = verify(reply_path, task_id)
    result["task_id"] = task_id
    cr = closure_ready(reply_path, task_id) if task_id else None

    print(json.dumps({"verify": result, "closure_ready": cr}, indent=2, ensure_ascii=False))

    if not result["valid"]:
        print(f"\nGUARD BLOCKED: GPT reply for {task_id or 'UNKNOWN'} is not valid.")
        print(f"Errors: {result.get('errors', [])}")
        sys.exit(1)

    print(f"\nGUARD OK: GPT reply for {task_id or 'UNKNOWN'} is valid.")
    print(f"Verdict: {result['overall_judgment']}")
    print(f"Closure ready: {cr['closure_ready'] if cr else 'N/A'}")
    sys.exit(0 if (not cr or cr["closure_ready"]) else 1)


if __name__ == "__main__":
    main()
