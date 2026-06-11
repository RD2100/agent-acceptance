#!/usr/bin/env python3
"""validate_run_id_consistency.py — Validates run_id consistency across pack artifacts.

Checks:
1. run_id.txt exists
2. R1_RUN_ID.txt matches run_id.txt
3. Evidence pack zip exists and filename contains run_id
4. GPT_REVIEW_PROMPT.md uses {{RUN_ID}} template variable (not hardcoded)
5. GPT_REVIEW_PROMPT.md uses {{TASK_ID}} template variable
6. PACK_MANIFEST.md run_id field matches run_id.txt
7. GPT review result run_id matches (if result exists)

Per AWSP v1.0.0 (docs/AGENT_WORKFLOW_STANDARD.md).

Usage:
    python scripts/validate_run_id_consistency.py --report-dir _reports/task-a1/
"""

import argparse
import re
import sys
from pathlib import Path


def validate_run_id_consistency(report_dir: str) -> dict:
    """Validate run_id consistency across all pack artifacts.

    Returns:
        dict with consistent, errors, details.
    """
    errors = []
    details = {}
    rdir = Path(report_dir)

    # 1. Read run_id from run_id.txt
    run_id_file = rdir / "run_id.txt"
    if not run_id_file.exists():
        return {"consistent": False, "errors": ["run_id.txt not found"], "details": {}}
    run_id = run_id_file.read_text(encoding="utf-8").strip()
    if not run_id:
        return {"consistent": False, "errors": ["run_id.txt is empty"], "details": {}}
    details["run_id_from_file"] = run_id

    # 2. Check R1_RUN_ID.txt matches
    r1_run_id_file = rdir / "R1_RUN_ID.txt"
    if r1_run_id_file.exists():
        r1_run_id = r1_run_id_file.read_text(encoding="utf-8").strip()
        details["r1_run_id"] = r1_run_id
        if r1_run_id != run_id:
            errors.append(f"R1_RUN_ID.txt ({r1_run_id}) != run_id.txt ({run_id})")

    # 3. Check evidence pack zip exists and filename contains run_id
    # Search for evidence_packs directory at multiple levels
    task_dir_name = rdir.name
    matching_pack_dir = None
    pack_dirs_root = None

    # Try rdir.parent.parent / "evidence_packs" (standard: _reports/task/../../evidence_packs/)
    # and rdir.parent / "evidence_packs" (test: tmp_path/task/../evidence_packs/)
    for candidate_root in [rdir.parent.parent, rdir.parent]:
        ep_root = candidate_root / "evidence_packs"
        if ep_root.exists():
            pack_dirs_root = ep_root
            for pd in ep_root.glob("*"):
                if pd.name.lower() == task_dir_name.lower() or pd.name == task_dir_name:
                    matching_pack_dir = pd
                    break
            if matching_pack_dir:
                break

    if not matching_pack_dir:
        errors.append(f"evidence_packs/{task_dir_name}/ directory not found — pack required per AWSP")
    else:
        zips = sorted(matching_pack_dir.glob("*.zip"))
        if not zips:
            errors.append(f"No evidence pack zip found in {matching_pack_dir} — pack zip required per AWSP")
        else:
            pack_name = zips[-1].stem
            details["pack_filename"] = pack_name
            if run_id not in pack_name:
                errors.append(f"Pack filename ({pack_name}) does not contain run_id ({run_id})")

    # 4. Check GPT_REVIEW_PROMPT.md uses {{RUN_ID}}
    prompt_file = rdir / "GPT_REVIEW_PROMPT.md"
    if prompt_file.exists():
        prompt_content = prompt_file.read_text(encoding="utf-8")
        has_run_id_var = "{{RUN_ID}}" in prompt_content
        details["prompt_has_run_id_var"] = has_run_id_var

        if not has_run_id_var:
            errors.append("GPT_REVIEW_PROMPT.md missing {{RUN_ID}} template variable — required per AWSP")

        # Check for hardcoded run_ids
        hardcoded_pattern = re.findall(r'run_id:\s*\w+_\d{8}T\d{6}_\w+', prompt_content)
        if hardcoded_pattern:
            details["hardcoded_run_ids"] = hardcoded_pattern
            errors.append(
                f"GPT_REVIEW_PROMPT.md has {len(hardcoded_pattern)} hardcoded run_id(s) "
                f"instead of {{{{RUN_ID}}}} template variable"
            )

        # 5. Check GPT_REVIEW_PROMPT.md uses {{TASK_ID}}
        has_task_id_var = "{{TASK_ID}}" in prompt_content
        details["prompt_has_task_id_var"] = has_task_id_var
        if not has_task_id_var:
            errors.append("GPT_REVIEW_PROMPT.md missing {{TASK_ID}} template variable — required per AWSP")
    else:
        errors.append("GPT_REVIEW_PROMPT.md not found — required per AWSP")

    # 6. Check PACK_MANIFEST.md run_id field matches
    if matching_pack_dir and matching_pack_dir.exists():
        manifest_file = matching_pack_dir / "PACK_MANIFEST.md"
        if not manifest_file.exists():
            errors.append("PACK_MANIFEST.md not found in evidence pack directory — required per AWSP")
        else:
            manifest_content = manifest_file.read_text(encoding="utf-8")
            # Extract run_id from manifest table: | run_id | VALUE |
            m = re.search(r'\|\s*run_id\s*\|\s*(\S+)\s*\|', manifest_content)
            if m:
                manifest_run_id = m.group(1).strip()
                details["manifest_run_id"] = manifest_run_id
                if manifest_run_id != run_id:
                    errors.append(
                        f"PACK_MANIFEST.md run_id ({manifest_run_id}) != run_id.txt ({run_id})"
                    )
            else:
                details["manifest_run_id_found"] = False
                errors.append("PACK_MANIFEST.md exists but run_id field not found — required per AWSP")

    # 7. Check GPT review result run_id matches (if available)
    for result_file in ["GPT_REVIEW_RESULT.txt", "GPT_REVIEW_RESULT_R1.txt", "GPT_REVIEW_RESULT_R2.txt"]:
        rf = rdir / result_file
        if rf.exists():
            content = rf.read_text(encoding="utf-8")
            m = re.search(r'run_id:\s*(\S+)', content)
            if m:
                gpt_run_id = m.group(1).strip()
                details[f"gpt_run_id_in_{result_file}"] = gpt_run_id
                if gpt_run_id != run_id:
                    errors.append(
                        f"GPT reply run_id ({gpt_run_id}) != submitted run_id ({run_id}) "
                        f"in {result_file}"
                    )

    return {
        "consistent": len(errors) == 0,
        "errors": errors,
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser(description="Validate run_id consistency across pack artifacts")
    parser.add_argument("--report-dir", required=True, help="Path to task report directory")
    args = parser.parse_args()

    result = validate_run_id_consistency(args.report_dir)
    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if result["consistent"]:
        print("\nRUN-ID CONSISTENT: All artifacts use the same run_id")
        sys.exit(0)
    else:
        print("\nRUN-ID INCONSISTENT:")
        for e in result["errors"]:
            print(f"  ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
