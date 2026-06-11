#!/usr/bin/env python3
"""cross_repo_verify.py — Verify all three DevFrame repos are healthy and consistent."""
import json, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

REPOS = {
    "agent-acceptance": {"path": "D:/agent-acceptance", "cmd": [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"]},
    "devframe-control-plane": {"path": "D:/devframe-control-plane", "cmd": [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"]},
    "dev-frame-opencode": {"path": "D:/dev-frame-opencode", "cmd": [sys.executable, "smoke_test.py"]},
}

def main():
    results = {}
    for name, cfg in REPOS.items():
        r = subprocess.run(cfg["cmd"], capture_output=True, text=True, cwd=cfg["path"], timeout=300)
        results[name] = {"exit": r.returncode, "tail": (r.stdout or r.stderr).strip().split("\n")[-1]}

    all_ok = all(v["exit"] == 0 for v in results.values())
    report = {"timestamp": datetime.now(timezone.utc).isoformat(), "overall": "PASS" if all_ok else "FAIL", "repos": results}
    print(json.dumps(report, indent=2, ensure_ascii=False))
    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
