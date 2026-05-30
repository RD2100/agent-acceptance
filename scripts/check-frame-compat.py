#!/usr/bin/env python3
"""
check-frame-compat.py — Cross-Project Compatibility Preflight Checker
=====================================================================
Part of RD2100 Agent Runtime v2.
Runs as part of Gate 0 preflight.
Checks frame manifests against the runtime compatibility lock.

Usage:
  python check-frame-compat.py [--strict] [--json]

Exit codes:
  0 = PASS (all frames compatible)
  1 = BLOCKED (hard incompatibility)
  2 = WARNING (non-blocking issues)
"""

import sys
import json
import os
import hashlib
import re
from pathlib import Path
from datetime import datetime

# === Config ===
RUNTIME_ROOT = Path(r"D:\agent-acceptance")
LOCK_PATH = RUNTIME_ROOT / "docs" / "agent-runtime" / "runtime-compatibility-lock.yaml"

# Minimal inline YAML parser (avoids external dependency)
def parse_simple_yaml(text):
    """Parse a simple subset of YAML (no anchors, no multi-line strings, no flow style)."""
    lines = text.strip().split("\n")
    result = {}
    stack = [(result, -1)]
    current_list = None
    current_list_key = None

    for line in lines:
        stripped = line.rstrip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        value_part = stripped.lstrip()

        # Pop stack if indent decreased
        while stack[-1][1] >= indent and len(stack) > 1:
            stack.pop()

        parent, parent_indent = stack[-1]

        if ": " in value_part or value_part.endswith(":"):
            if value_part.endswith(":"):
                key = value_part[:-1].strip().strip('"').strip("'")
                val = {}
                parent[key] = val
                stack.append((val, indent))
            else:
                key, raw_val = value_part.split(": ", 1)
                key = key.strip().strip('"').strip("'")
                raw_val = raw_val.strip()

                if raw_val == "[]":
                    val = []
                elif raw_val.startswith("[") and raw_val.endswith("]"):
                    val = [v.strip().strip('"').strip("'") for v in raw_val[1:-1].split(",") if v.strip()]
                elif raw_val in ("true", "false"):
                    val = raw_val == "true"
                else:
                    val = raw_val.strip('"').strip("'")

                if key == "-":
                    if current_list is not None:
                        current_list.append(val)
                else:
                    parent[key] = val
        elif value_part.startswith("- "):
            val = value_part[2:].strip().strip('"').strip("'")
            if current_list_key is None:
                for k, v in parent.items():
                    if isinstance(v, list):
                        current_list_key = k
                        current_list = v
                        break
                if current_list is None:
                    current_list = []
                    parent["_list"] = current_list
            current_list.append(val)
        else:
            val = value_part.strip().strip('"').strip("'")
            if current_list is not None:
                current_list.append(val)

    return result

def load_yaml(path):
    """Load YAML file, returning dict or None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return parse_simple_yaml(f.read())
    except Exception as e:
        return {"_error": str(e)}

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def compute_hash(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

class CheckResult:
    def __init__(self):
        self.issues = []
        self.verdict = "PASS"

    def add(self, severity, check_name, detail):
        self.issues.append({
            "severity": severity,
            "check": check_name,
            "detail": detail,
            "timestamp": datetime.now().isoformat()
        })
        if severity == "BLOCKED":
            self.verdict = "BLOCKED"
        elif severity == "WARNING" and self.verdict == "PASS":
            self.verdict = "WARNING"

    def exit_code(self):
        return {"PASS": 0, "WARNING": 2, "BLOCKED": 1}[self.verdict]

def check_frame_compat(lock, frame_id, strict=False):
    """Check one frame against the compatibility lock."""
    result = CheckResult()
    frame_cfg = lock.get("accepted_frames", {}).get(frame_id)
    if not frame_cfg:
        result.add("BLOCKED", "frame_registered", f"Frame '{frame_id}' not found in compatibility lock")
        return result

    manifest_path = Path(frame_cfg["manifest_path"])
    
    # 1. Manifest exists
    if not manifest_path.exists():
        result.add("BLOCKED", "manifest_missing", f"Manifest not found: {manifest_path}")
        return result

    # 2. Load manifest
    manifest = load_yaml(str(manifest_path))
    if manifest.get("_error"):
        result.add("BLOCKED", "manifest_parse_error", f"Cannot parse manifest: {manifest['_error']}")
        return result

    # 3. Manifest version
    manifest_ver = manifest.get("manifest_version", "unknown")
    if manifest_ver not in ("1.0.0",):
        result.add("WARNING", "manifest_version_unknown", f"Manifest version {manifest_ver} not explicitly supported")

    # 4. Frame ID match
    frame_info = manifest.get("frame", {})
    manifest_frame_id = frame_info.get("id", "unknown")
    if manifest_frame_id != frame_id:
        result.add("BLOCKED", "frame_id_mismatch", f"Manifest claims id='{manifest_frame_id}', lock expects '{frame_id}'")

    # 5. Frame version accepted
    frame_ver = frame_info.get("version", "unknown")
    accepted_vers = frame_cfg.get("accepted_frame_versions", [])
    if accepted_vers and frame_ver not in accepted_vers:
        result.add("BLOCKED", "frame_version_rejected", f"Frame version {frame_ver} not in accepted versions: {accepted_vers}")

    # 6. Permission boundary check
    for cap_name, cap_cfg in manifest.get("capabilities", {}).items():
        cap_access = cap_cfg.get("access", "unknown")
        max_access = frame_cfg.get("max_access", "read_only")
        access_order = {"forbidden": 0, "read_only": 1}
        if access_order.get(cap_access, -1) > access_order.get(max_access, -1):
            result.add("BLOCKED", "permission_widening", f"Capability '{cap_name}': manifest access='{cap_access}' exceeds lock max_access='{max_access}'")
        
        cap_exec = cap_cfg.get("execution_policy", "unknown")
        lock_exec = frame_cfg.get("execution_policy", "forbidden")
        exec_order = {"forbidden": 0, "human_gated": 1, "dry_run_allowed": 2, "allowed": 3}
        if exec_order.get(cap_exec, -1) > exec_order.get(lock_exec, -1):
            result.add("BLOCKED", "execution_widening", f"Capability '{cap_name}': manifest execution='{cap_exec}' exceeds lock execution='{lock_exec}'")

    # 7. GateResult: always forbidden for external frames
    produces = manifest.get("contracts", {}).get("produces", {})
    gate_result = produces.get("GateResult", {})
    if gate_result.get("authority") != "forbidden":
        result.add("BLOCKED", "gate_result_authority", f"Frame '{frame_id}' claims GateResult authority='{gate_result.get('authority')}'. External frames MUST be 'forbidden'.")

    # 8. Evidence freshness check
    evidence_idx = produces.get("EvidenceIndex", {})
    allowed_freshness = evidence_idx.get("allowed_freshness", [])
    if "current" in allowed_freshness:
        result.add("BLOCKED", "evidence_freshness", f"Frame '{frame_id}' claims current evidence but has no approved_run_id capability")

    # 9. Path drift scan
    paths = manifest.get("paths", {})
    root = paths.get("root", "")
    for path_key, path_val in paths.items():
        if path_key == "root":
            continue
        if not Path(path_val).exists():
            result.add("WARNING" if not strict else "BLOCKED", "path_missing", f"Path '{path_key}={path_val}' does not exist on disk")

    # 10. Stale manifest check (git_commit vs HEAD)
    manifest_commit = frame_info.get("git_commit", "")
    if manifest_commit and manifest_commit != "not-a-git-repo":
        import subprocess
        try:
            actual = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
            if manifest_commit != actual:
                result.add("WARNING" if not strict else "BLOCKED", "manifest_stale", f"Manifest git_commit={manifest_commit[:8]} but HEAD={actual[:8]}")
        except Exception:
            pass

    return result

def scan_path_drift(lock, strict=False):
    """Scan agent-acceptance docs for absolute path references and check against manifests."""
    result = CheckResult()
    known_aliases = lock.get("path_drift_rules", {}).get("known_aliases", {})
    doc_dir = RUNTIME_ROOT / "docs"

    # Find all absolute D:\ paths in docs
    path_pattern = re.compile(r'D:\\(?:dev-?frame|test-?frame|agent-acceptance)[^\s)\]\'"`,]+', re.IGNORECASE)
    
    for md_file in doc_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            found = path_pattern.findall(content)
            for p in found:
                normalized = p.replace("\\", "\\\\")
                # Check if this path is registered in any frame manifest
                registered = False
                for frame_id, frame_cfg in lock.get("accepted_frames", {}).items():
                    manifest_path = Path(frame_cfg["manifest_path"])
                    if manifest_path.exists():
                        manifest = load_yaml(str(manifest_path))
                        for pk, pv in manifest.get("paths", {}).items():
                            if pv and pv.lower() == normalized.lower():
                                registered = True
                                break
                
                if not registered and normalized not in [v.lower() for v in known_aliases.values()]:
                    # Check alias
                    alias_resolved = False
                    for alias, target in known_aliases.items():
                        if normalized.lower().startswith(alias.lower()):
                            alias_resolved = True
                            break
                    
                    # Self-reference: paths inside agent-acceptance referencing agent-acceptance are expected
                    is_self_ref = normalized.lower().startswith(r"d:\\agent-acceptance".lower())
                    
                    if not alias_resolved and not registered and not is_self_ref:
                        result.add("WARNING" if not strict else "BLOCKED", "path_drift", f"Unregistered absolute path in {md_file.name}: {p}")
        except Exception:
            pass

    return result

def main():
    strict = "--strict" in sys.argv
    json_output = "--json" in sys.argv

    # Load lock
    lock = load_yaml(str(LOCK_PATH))
    if not lock or lock.get("_error"):
        print(json.dumps({"verdict": "BLOCKED", "issues": [{"severity": "BLOCKED", "check": "lock_load", "detail": "Cannot load runtime-compatibility-lock.yaml"}]}))
        sys.exit(1)

    all_results = {}

    # Check each registered frame
    for frame_id in lock.get("accepted_frames", {}):
        result = check_frame_compat(lock, frame_id, strict)
        all_results[frame_id] = result

    # Path drift scan
    drift_result = scan_path_drift(lock, strict)
    all_results["path_drift"] = drift_result

    # Aggregate verdict
    final_verdict = "PASS"
    all_issues = []
    for name, result in all_results.items():
        for issue in result.issues:
            issue["scope"] = name
            all_issues.append(issue)
        if result.verdict == "BLOCKED":
            final_verdict = "BLOCKED"
        elif result.verdict == "WARNING" and final_verdict == "PASS":
            final_verdict = "WARNING"

    output = {
        "check_id": f"frame-compat-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "runtime": "agent-acceptance",
        "verdict": final_verdict,
        "frames": {},
        "issues": all_issues
    }

    for name, result in all_results.items():
        output["frames"][name] = {
            "verdict": result.verdict,
            "issue_count": len(result.issues)
        }

    if json_output:
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"=== Frame Compatibility Check ===")
        print(f"Verdict: {final_verdict}")
        print(f"Issues: {len(all_issues)}")
        for issue in all_issues:
            print(f"  [{issue['severity']}] {issue['scope']}:{issue['check']} — {issue['detail']}")
        print(f"Frames: {json.dumps(output['frames'], indent=2)}")

    sys.exit({"PASS": 0, "WARNING": 2, "BLOCKED": 1}[final_verdict])

if __name__ == "__main__":
    main()

