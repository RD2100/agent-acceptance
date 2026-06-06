"""Check if conversation handoff is needed based on thresholds.

Thresholds per GPT analysis:
- assistant_message_count >= 60: force handoff
- response_time_seconds >= 60: force handoff
- review_round_count >= 3: force handoff
- last_gpt_reply_bytes < 2000: force handoff

Output: HANDOFF_NEEDED.yaml
"""
import sys
import json
from pathlib import Path


def check_handoff(
    assistant_message_count: int = 0,
    response_time_seconds: int = 0,
    review_round_count: int = 0,
    last_gpt_reply_bytes: int = 0,
) -> dict:
    force_reasons = []
    suggest_reasons = []

    if assistant_message_count >= 60:
        force_reasons.append(f"assistant_message_count={assistant_message_count} >= 60")
    elif assistant_message_count >= 45:
        suggest_reasons.append(f"assistant_message_count={assistant_message_count} >= 45 (suggested)")
    if response_time_seconds >= 60:
        force_reasons.append(f"response_time_seconds={response_time_seconds}s >= 60")
    elif response_time_seconds >= 40:
        suggest_reasons.append(f"response_time_seconds={response_time_seconds}s >= 40 (suggested)")
    if review_round_count >= 3:
        force_reasons.append(f"review_round_count={review_round_count} >= 3")
    if 0 < last_gpt_reply_bytes < 2000:
        force_reasons.append(f"last_gpt_reply_bytes={last_gpt_reply_bytes} < 2000")

    all_reasons = force_reasons + suggest_reasons
    return {
        "handoff_needed": len(force_reasons) > 0,
        "force_handoff": len(force_reasons) > 0,
        "suggested_only": len(all_reasons) > 0 and len(force_reasons) == 0,
        "reasons": all_reasons,
        "recommended_action": "generate_handoff" if len(force_reasons) > 0 else ("suggest_handoff" if suggest_reasons else "continue"),
    }


def main():
    stats = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            stats[k] = int(v)

    result = check_handoff(
        assistant_message_count=stats.get("messages", 0),
        response_time_seconds=stats.get("response_time", 0),
        review_round_count=stats.get("rounds", 0),
        last_gpt_reply_bytes=stats.get("reply_bytes", 0),
    )

    print(f"HANDOFF_NEEDED:")
    print(f"  handoff_needed: {result['handoff_needed']}")
    print(f"  force_handoff: {result['force_handoff']}")
    print(f"  reasons:")
    for r in result["reasons"]:
        print(f"    - {r}")
    if not result["reasons"]:
        print(f"    []")
    print(f"  recommended_action: {result['recommended_action']}")

    return 0 if not result["force_handoff"] else 1


if __name__ == "__main__":
    sys.exit(main())
