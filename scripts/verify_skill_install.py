#!/usr/bin/env python3
"""verify_skill_install.py — Verify a skill is properly installed and operational."""
import json, sys, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / ".claude" / "skills"


def verify(name: str) -> dict:
    result = {"name": name, "checks": {}, "ready": False}

    # Check 1: Directory exists
    target = SKILLS_DIR / name
    result["checks"]["dir_exists"] = target.is_dir()

    # Check 2: Registry entry
    reg_path = SKILLS_DIR / "registry.json"
    if reg_path.exists():
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        result["checks"]["registered"] = name in reg.get("skills", {})
    else:
        result["checks"]["registered"] = False

    # Check 3: Lock file
    lock = SKILLS_DIR / f"{name}.lock.json"
    result["checks"]["lock_exists"] = lock.exists()

    # Check 4: README or entry point
    result["checks"]["has_readme"] = (target / "README.md").exists() or (target / "AGENTS.md").exists()

    # Check 5: Hooks merged (check .claude/settings.json)
    settings_path = REPO / ".claude" / "settings.json"
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        hooks = settings.get("hooks", {})
        result["checks"]["hooks_present"] = any(hooks.values())
    else:
        result["checks"]["hooks_present"] = False

    # Check 6: Git repo valid
    if (target / ".git").exists():
        r = subprocess.run(["git", "-C", str(target), "log", "--oneline", "-n", "1"],
                          capture_output=True, text=True, timeout=10)
        result["checks"]["git_valid"] = r.returncode == 0

    result["ready"] = all(result["checks"].values())
    return result


def main():
    if len(sys.argv) < 2:
        # Verify all registered skills
        reg_path = SKILLS_DIR / "registry.json"
        if reg_path.exists():
            reg = json.loads(reg_path.read_text(encoding="utf-8"))
            for name in reg.get("skills", {}):
                r = verify(name)
                status = "READY" if r["ready"] else "INCOMPLETE"
                print(f"[{status}] {name}: {json.dumps(r['checks'], ensure_ascii=False)}")
        else:
            print("No registry found")
        return

    r = verify(sys.argv[1])
    print(json.dumps(r, indent=2, ensure_ascii=False))
    sys.exit(0 if r["ready"] else 1)


if __name__ == "__main__":
    main()
