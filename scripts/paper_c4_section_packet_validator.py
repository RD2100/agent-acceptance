#!/usr/bin/env python3
"""
paper_c4_section_packet_validator.py — Validate section review input packets.
Fail-closed on forbidden content. No real paper ingestion.
"""
import json, sys, yaml
from pathlib import Path

FORBIDDEN_FIELDS = {
    "real_paper_full_text","raw_paper_text","full_chapter_text",
    "paper_excerpt_unbounded","private_user_text","raw_transcript",
    "external_upload","memory_write_with_paper_content","live_cdp"
}
ALLOWED_PRIVACY_MODES = {"synthetic_only","metadata_only","sanitized_section"}

def validate(data: dict) -> dict:
    errors = []
    warnings = []

    # Required fields
    for field in ["task_id","paper_project_type","target_section_name","privacy_mode"]:
        if field not in data:
            errors.append(f"missing required field: {field}")

    # Forbidden fields
    for field in FORBIDDEN_FIELDS:
        if data.get(field):
            errors.append(f"forbidden field present: {field}")

    # Privacy mode
    mode = data.get("privacy_mode","")
    if mode not in ALLOWED_PRIVACY_MODES:
        errors.append(f"invalid privacy_mode: {mode}")

    # sanitized_section requires authorization_ref
    if mode == "sanitized_section" and not data.get("authorization_ref"):
        errors.append("sanitized_section requires authorization_ref")

    valid = len(errors) == 0
    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "privacy_mode": mode,
        "task_id": data.get("task_id","unknown"),
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: paper_c4_section_packet_validator.py <input.yaml>")
        sys.exit(1)
    fp = Path(sys.argv[1])
    if not fp.exists():
        print(json.dumps({"valid":False,"errors":[f"file not found: {fp}"]}))
        sys.exit(1)
    try:
        data = yaml.safe_load(fp.read_text(encoding="utf-8"))
    except Exception as e:
        print(json.dumps({"valid":False,"errors":[str(e)]}))
        sys.exit(1)
    result = validate(data)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["valid"] else 1)

if __name__ == "__main__":
    main()
