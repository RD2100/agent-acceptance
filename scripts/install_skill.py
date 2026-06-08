#!/usr/bin/env python3
"""
install_skill.py — Generic third-party skill installer for agent-acceptance.
Usage: python scripts/install_skill.py --url <github_url> --name <skill_name>
Clones repo into .claude/skills/<name>, merges hooks, registers in registry.json
"""
import argparse, json, subprocess, sys, hashlib
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO / ".claude" / "skills"
REGISTRY_PATH = SKILLS_DIR / "registry.json"
LOCK_DIR = SKILLS_DIR


def load_registry() -> dict:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {"skills": {}, "updated_at": None}


def save_registry(reg: dict):
    reg["updated_at"] = datetime.now(timezone.utc).isoformat()
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")


def install(url: str, name: str, mode: str = "project") -> dict:
    """Install a third-party skill."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    target = SKILLS_DIR / name
    result = {"name": name, "url": url, "mode": mode, "status": "installed_pending_review", "steps": {}}

    # Step 1: Clone
    if target.exists():
        result["steps"]["clone"] = f"already exists at {target}"
    else:
        r = subprocess.run(["git", "clone", "--depth", "1", url, str(target)],
                          capture_output=True, text=True, timeout=60)
        result["steps"]["clone"] = "ok" if r.returncode == 0 else f"failed: {r.stderr[:200]}"
        if r.returncode != 0:
            result["status"] = "clone_failed"
            return result

    # Step 2: Get commit SHA
    r = subprocess.run(["git", "-C", str(target), "rev-parse", "HEAD"],
                      capture_output=True, text=True, timeout=10)
    commit_sha = r.stdout.strip()[:8] if r.returncode == 0 else "unknown"
    result["commit"] = commit_sha

    # Step 3: Write lock file
    lock = {"name": name, "url": url, "commit": commit_sha,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "installer_version": "1.0.0"}
    (LOCK_DIR / f"{name}.lock.json").write_text(json.dumps(lock, indent=2, ensure_ascii=False), encoding="utf-8")

    # Step 4: Merge hooks (if skill has .claude/settings.json)
    skill_settings = target / ".claude" / "settings.json"
    if skill_settings.exists():
        _merge_hooks(skill_settings)
        result["steps"]["hooks_merged"] = True

    # Step 5: Register
    reg = load_registry()
    reg["skills"][name] = {"url": url, "commit": commit_sha, "status": "installed_pending_review",
                           "installed_at": datetime.now(timezone.utc).isoformat()}
    save_registry(reg)
    result["steps"]["registered"] = True
    result["status"] = "installed_pending_review"

    return result


def _merge_hooks(skill_settings: Path):
    """Merge skill hooks into project settings without overwriting."""
    import json
    skill_cfg = json.loads(skill_settings.read_text(encoding="utf-8"))
    project_cfg_path = REPO / ".claude" / "settings.json"

    if project_cfg_path.exists():
        project_cfg = json.loads(project_cfg_path.read_text(encoding="utf-8"))
    else:
        project_cfg = {}

    # Merge hooks (append, don't replace)
    for hook_type in ["PostToolUse", "Stop", "SessionStart", "PreCompact"]:
        skill_hooks = skill_cfg.get("hooks", {}).get(hook_type, [])
        if skill_hooks:
            existing = project_cfg.get("hooks", {}).get(hook_type, [])
            # Add skill hooks that don't already exist
            for h in skill_hooks:
                if h not in existing:
                    existing.append(h)
            project_cfg.setdefault("hooks", {})[hook_type] = existing

    project_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    project_cfg_path.write_text(json.dumps(project_cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Install third-party skill")
    parser.add_argument("--url", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--mode", default="project", choices=["project", "user"])
    args = parser.parse_args()

    result = install(args.url, args.name, args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result["status"] != "clone_failed" else 1)


if __name__ == "__main__":
    main()
