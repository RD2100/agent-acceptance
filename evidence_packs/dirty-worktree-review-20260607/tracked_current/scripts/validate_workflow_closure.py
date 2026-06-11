"""Enhanced Workflow Closure Validator — SD-01/02/03 R2 hardening.

- SD-01: SHA256 verification, actual_deliverable_patterns, manifest consistency
- SD-02: closed requires GPT_REVIEW_RESULT + workflow ledger entry
- SD-03: governance task self-close detection
"""
import sys
import hashlib
import zipfile
from pathlib import Path

SUMMARY_ONLY_FILES = {
    "GPT_REVIEW_PROMPT.md", "CLOSURE_REPORT.md", "CLOSURE_REPORT.yaml",
    "SAFETY_ATTESTATION.md", "PACK_MANIFEST.md",
    "WORKFLOW_CLOSURE_VALIDATION.yaml",
}
VERIFICATION_FILES = {
    "TEST_OUTPUT.txt", "BYPASS_CHECK_OUTPUT.txt", "BYPASS_CHECK_OUTPUT.yaml",
    "GATE_OUTPUT.txt", "DOCTOR_OUTPUT.txt",
}

ACTUAL_DELIVERABLE_PATTERNS = [
    "contracts/", "schemas/", "docs/", "templates/", "scripts/",
    "tests/", "pipelines/", "examples/", "review/", "input/",
    "control_plane/",
    "closure/FLOW_OUTCOME.json", "submission/SUBMISSION_RESULT.json",
    "diff.patch",
]

GOVERNANCE_PATTERNS = [
    "contracts/", "policies/", "schemas/",
    "templates/GPT_REVIEW_PROMPT_TEMPLATE.md",
    "scripts/validate_", "scripts/check_",
    "docs/workflow-state", "docs/framework-usage",
    "docs/workflow-memory", "docs/memory-",
]


def is_governance_file(path: str) -> bool:
    return any(p in path for p in GOVERNANCE_PATTERNS)


def is_actual_deliverable(path: str) -> bool:
    """Check if file matches actual deliverable patterns."""
    if path in SUMMARY_ONLY_FILES or path in VERIFICATION_FILES:
        return False
    for p in ACTUAL_DELIVERABLE_PATTERNS:
        if path.startswith(p.rstrip("/")) or p.rstrip("/") in path:
            return True
    return False


def sha256_content(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_evidence_pack(zip_path: str) -> dict:
    result = {
        "result": "pending",
        "manifest_valid": False,
        "hashes_verified": False,
        "summary_only_pack": True,
        "actual_deliverables_count": 0,
        "sd01_checks": {},
        "sd02_checks": {},
        "sd03_checks": {},
        "blocking_issues": [],
    }
    errors = []

    zp = Path(zip_path)
    if not zp.exists():
        result["result"] = "fail"
        result["blocking_issues"].append("ZIP 文件不存在")
        return result

    try:
        with zipfile.ZipFile(str(zp), "r") as zf:
            namelist = set(zf.namelist())
            # Read all file contents for hash verification
            file_contents = {n: zf.read(n) for n in namelist}

            # === SD-01: Manifest + SHA256 + actual deliverables ===

            if "PACK_MANIFEST.md" not in namelist:
                errors.append("SD-01: PACK_MANIFEST.md 不在 ZIP 中")
                result["sd01_checks"]["manifest_present"] = False
            else:
                result["sd01_checks"]["manifest_present"] = True
                manifest_text = file_contents["PACK_MANIFEST.md"].decode("utf-8")

                manifest_entries = {}  # path -> sha256 from manifest
                for line in manifest_text.split("\n"):
                    if line.startswith("|") and not line.startswith("|---") and "|" in line[1:]:
                        parts = [p.strip() for p in line.split("|")[1:-1]]
                        if parts and parts[0] and parts[0] != "path":
                            manifest_entries[parts[0]] = parts[2] if len(parts) > 2 else ""

                manifest_files = set(manifest_entries.keys())
                zip_set = {n.replace("\\", "/") for n in namelist}
                extra_zip = zip_set - manifest_files
                extra_man = manifest_files - zip_set
                result["sd01_checks"]["manifest_bidirectional"] = not extra_zip and not extra_man
                result["manifest_valid"] = result["sd01_checks"]["manifest_bidirectional"]
                if extra_zip:
                    errors.append(f"SD-01: ZIP 有文件不在 manifest: {extra_zip}")
                if extra_man:
                    errors.append(f"SD-01: manifest 有文件不在 ZIP: {extra_man}")

                # SHA256 verification
                hash_errors = []
                for fname, content in file_contents.items():
                    fname_norm = fname.replace("\\", "/")
                    if fname_norm == "PACK_MANIFEST.md":
                        continue  # self-excluded
                    if fname_norm in manifest_entries:
                        expected = manifest_entries[fname_norm]
                        if expected == "self_excluded":
                            continue
                        actual = sha256_content(content)
                        if expected and expected != actual:
                            hash_errors.append(f"{fname_norm}: manifest={expected[:16]}... actual={actual[:16]}...")
                result["sd01_checks"]["hash_errors"] = hash_errors
                result["hashes_verified"] = len(hash_errors) == 0
                if hash_errors:
                    errors.append(f"SD-01: SHA256 不匹配 ({len(hash_errors)} files)")

            # SD-01: actual deliverables check
            actual_deliverables = {f for f in namelist if is_actual_deliverable(f)}
            result["actual_deliverables_count"] = len(actual_deliverables)
            result["summary_only_pack"] = len(actual_deliverables) == 0
            result["sd01_checks"]["actual_deliverables_found"] = sorted(actual_deliverables)
            result["sd01_checks"]["summary_only"] = result["summary_only_pack"]
            if result["summary_only_pack"]:
                errors.append("SD-01: summary-only evidence pack — 无 actual deliverables")

            # SD-01: claimed output check
            if "CLOSURE_REPORT.md" in namelist:
                closure_text = file_contents["CLOSURE_REPORT.md"].decode("utf-8")
                if "test" in closure_text.lower() and "TEST_OUTPUT.txt" not in namelist:
                    errors.append("SD-01: closure 提及测试但缺 TEST_OUTPUT.txt")
                if "bypass" in closure_text.lower() and "BYPASS_CHECK_OUTPUT.txt" not in namelist:
                    errors.append("SD-01: closure 提及 bypass 但缺 BYPASS_CHECK_OUTPUT.txt")

            # === SD-02: closure state + GPT review + ledger (R4: content-validated) ===
            result["sd02_checks"]["can_detect"] = True
            has_closed = False
            gpt_review_valid = False
            ledger_valid = False

            # Find GPT review files
            gpt_review_files = [f for f in namelist if f in (
                "GPT_REVIEW_RESULT.yaml", "GPT_REVIEW_RESULT.json",
                "GPT_REPLY.txt", "GPT_REPLY.yaml",
            ) or (f.startswith("evidence/") and ("GPT_REVIEW_RESULT" in f or "GPT_REPLY" in f))]
            result["sd02_checks"]["gpt_review_files_found"] = gpt_review_files

            # Find ledger files
            ledger_files = [f for f in namelist if "WORKFLOW_AUDIT_LEDGER" in f or "workflow_ledger" in f.lower()]
            result["sd02_checks"]["ledger_files_found"] = ledger_files

            # R5: Extract expected REVIEW_RUN_ID from CLOSURE_REPORT
            expected_rid = ""
            expected_task_id = ""
            if "CLOSURE_REPORT.md" in namelist:
                cr_text = file_contents["CLOSURE_REPORT.md"].decode("utf-8")
                for line in cr_text.split("\n"):
                    l = line.strip()
                    if l.startswith("REVIEW_RUN_ID:") or l.startswith("review_run_id:"):
                        v = l.split(":", 1)[1].strip().strip('"')
                        if v and "{{" not in v:
                            expected_rid = v.lower()
                    if l.startswith("task_id:") or l.startswith("TASK_ID:"):
                        v = l.split(":", 1)[1].strip().strip('"')
                        if v and "{{" not in v:
                            expected_task_id = v.lower()

            # R5: deep validate GPT review content (bound to expected_rid)
            if gpt_review_files and expected_rid:
                for grf in gpt_review_files:
                    try:
                        grf_text = file_contents[grf].decode("utf-8").lower()
                        has_accepted_v = "overall_judgment: accepted" in grf_text or "overall_judgment:accepted" in grf_text
                        has_gpt_reviewer = "reviewer_type: gpt" in grf_text or "reviewer_type:gpt" in grf_text
                        grf_rid = ""
                        for line in grf_text.split("\n"):
                            if "review_run_id:" in line:
                                grf_rid = line.split(":", 1)[1].strip().strip('"')
                                break
                        rid_match = not expected_rid or grf_rid == expected_rid
                        if has_accepted_v and has_gpt_reviewer and rid_match:
                            gpt_review_valid = True
                    except:
                        pass
            elif not expected_rid:
                gpt_review_valid = any(  # fallback: check without binding
                    "overall_judgment: accepted" in file_contents[f].decode("utf-8").lower()
                    and "reviewer_type: gpt" in file_contents[f].decode("utf-8").lower()
                    for f in gpt_review_files) if gpt_review_files else False
            result["sd02_checks"]["gpt_review_valid"] = gpt_review_valid
            result["sd02_checks"]["expected_rid"] = expected_rid

            # R5: deep validate ledger content (bound to expected_rid/expected_task_id)
            if ledger_files:
                for lf in ledger_files:
                    try:
                        lf_text = file_contents[lf].decode("utf-8").lower()
                        has_closed_entry = "final_status: closed" in lf_text or "status: closed" in lf_text
                        has_task_rid = (expected_rid and expected_rid in lf_text) or (expected_task_id and expected_task_id in lf_text)
                        if has_closed_entry and has_task_rid:
                            ledger_valid = True
                    except:
                        pass
            result["sd02_checks"]["ledger_valid"] = ledger_valid

            if "CLOSURE_REPORT.md" in namelist:
                closure_text = file_contents["CLOSURE_REPORT.md"].decode("utf-8").lower()
                has_closed = "final_status: closed" in closure_text or "final_status:closed" in closure_text
                has_ready = "task_status: ready_for_review" in closure_text

                if has_closed:
                    if not gpt_review_valid:
                        if not gpt_review_files:
                            errors.append("SD-02: final_status=closed 但证据包中无 GPT_REVIEW_RESULT 文件")
                        else:
                            errors.append("SD-02: final_status=closed 但 GPT_REVIEW_RESULT 内容无效（需 overall_judgment=accepted + reviewer_type=gpt + REVIEW_RUN_ID）")
                        result["sd02_checks"]["closed_without_gpt_accepted"] = True

                    if not ledger_valid:
                        if not ledger_files:
                            errors.append("SD-02: final_status=closed 但证据包中无 WORKFLOW_AUDIT_LEDGER 文件")
                        else:
                            errors.append("SD-02: final_status=closed 但 WORKFLOW_AUDIT_LEDGER 内容无效（需 final_status=closed + REVIEW_RUN_ID）")
                        result["sd02_checks"]["closed_without_ledger"] = True

                if has_ready and has_closed:
                    errors.append("SD-02: task_status=ready_for_review 与 final_status=closed 矛盾")
                    result["sd02_checks"]["ready_for_review_as_closed"] = True

                has_accepted = "final_status: accepted" in closure_text or "final_status:accepted" in closure_text
                if has_accepted and not gpt_review_valid:
                    errors.append("SD-02: accepted_without_valid_gpt_review — closure 声称 accepted 但无有效 GPT_REVIEW_RESULT")
                    result["sd02_checks"]["accepted_without_review_result"] = True

            # === SD-03: governance self-close (R4: uses SD-02 gpt_review_valid check) ===
            has_governance_files = any(is_governance_file(f) for f in namelist)
            result["sd03_checks"]["governance_files_present"] = has_governance_files

            if has_governance_files and has_closed and not gpt_review_valid:
                errors.append("SD-03: governance task self-closed — 治理文件存在且 final_status=closed 但无有效 GPT_REVIEW_RESULT（需 reviewer_type=gpt + accepted）")
                result["sd03_checks"]["governance_self_close"] = True

            if "CLOSURE_REPORT.md" in namelist:
                closure_text_r4 = file_contents["CLOSURE_REPORT.md"].decode("utf-8").lower()
                has_retroactive = "retroactive_review" in closure_text_r4
                has_prior = "prior_status" in closure_text_r4
                has_corrected = "corrected_status" in closure_text_r4
                has_reason = "reason_for_retroactive" in closure_text_r4

                if has_retroactive:
                    if not has_prior:
                        errors.append("SD-03: retroactive_review 但缺 prior_status")
                    if not has_corrected:
                        errors.append("SD-03: retroactive_review 但缺 corrected_status")
                    if not has_reason:
                        errors.append("SD-03: retroactive_review 但缺 reason_for_retroactive_review")

    except zipfile.BadZipFile:
        result["result"] = "fail"
        result["blocking_issues"].append("不是有效的 ZIP 文件")
        return result

    result["blocking_issues"].extend(errors)
    result["result"] = "fail" if errors else "pass"
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_workflow_closure.py <evidence_pack.zip>")
        return 2

    zip_path = sys.argv[1]
    result = validate_evidence_pack(zip_path)

    print(f"WORKFLOW_CLOSURE_VALIDATION:")
    print(f"  result: {result['result']}")
    print(f"  manifest_valid: {result['manifest_valid']}")
    print(f"  hashes_verified: {result['hashes_verified']}")
    print(f"  summary_only_pack: {result['summary_only_pack']}")
    print(f"  actual_deliverables_count: {result['actual_deliverables_count']}")
    print(f"  blocking_issues:")
    for issue in result["blocking_issues"]:
        print(f"    - {issue}")
    if not result["blocking_issues"]:
        print(f"    []")

    return {"pass": 0, "fail": 1}.get(result["result"], 2)


if __name__ == "__main__":
    sys.exit(main())
