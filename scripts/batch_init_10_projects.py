#!/usr/bin/env python3
"""MULTI-PROJECT-REGISTRY-BATCH-INIT-A1 — Batch initialize 10 projects.

Creates:
- PROJECT_REGISTRY.json with 10 project entries (ports 9222-9231)
- Profile directories for each project
- CONVERSATION_BINDING.json scaffold for each project
- Resource policy config
- All bindings start as pending_manual_binding (except existing active ones)
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import multi_cdp_launcher

REPORT_DIR = REPO / "_reports" / "multi-project-batch-init-a1"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
PROFILES_DIR = REPO / "_cdp_profiles"

# 10 project definitions
# Project 0 is the existing agent-acceptance project (already active)
# Projects 1-9 are new scaffold entries (pending_manual_binding)
PROJECTS = [
    {"id": "agent-acceptance",   "port": 9222, "root": str(REPO), "status": "active",
     "agents": [
         {"id": "agent-local-001", "role": "reviewer", "conv": "6a26cc03-235c-83a2-a0fc-cd29be615959",
          "profile": "cdp-profile-pilot-a1", "status": "active"},
         {"id": "agent-pilot-beta", "role": "executor", "conv": "6a28d545-f918-83a5-b122-dc1503386374",
          "profile": "cdp-profile-pilot-a1", "status": "active"},
     ]},
    {"id": "project-alpha",      "port": 9223, "root": str(REPO / "_projects" / "project-alpha"),   "status": "pending_manual_binding",
     "agents": [{"id": "agent-alpha-001", "role": "executor", "conv": None, "profile": "cdp-profile-alpha", "status": "pending_manual_binding"}]},
    {"id": "project-beta",       "port": 9224, "root": str(REPO / "_projects" / "project-beta"),    "status": "pending_manual_binding",
     "agents": [{"id": "agent-beta-001", "role": "executor", "conv": None, "profile": "cdp-profile-beta", "status": "pending_manual_binding"}]},
    {"id": "project-gamma",      "port": 9225, "root": str(REPO / "_projects" / "project-gamma"),   "status": "pending_manual_binding",
     "agents": [{"id": "agent-gamma-001", "role": "executor", "conv": None, "profile": "cdp-profile-gamma", "status": "pending_manual_binding"}]},
    {"id": "project-delta",      "port": 9226, "root": str(REPO / "_projects" / "project-delta"),   "status": "pending_manual_binding",
     "agents": [{"id": "agent-delta-001", "role": "executor", "conv": None, "profile": "cdp-profile-delta", "status": "pending_manual_binding"}]},
    {"id": "project-epsilon",    "port": 9227, "root": str(REPO / "_projects" / "project-epsilon"), "status": "pending_manual_binding",
     "agents": [{"id": "agent-epsilon-001", "role": "executor", "conv": None, "profile": "cdp-profile-epsilon", "status": "pending_manual_binding"}]},
    {"id": "project-zeta",       "port": 9228, "root": str(REPO / "_projects" / "project-zeta"),    "status": "pending_manual_binding",
     "agents": [{"id": "agent-zeta-001", "role": "executor", "conv": None, "profile": "cdp-profile-zeta", "status": "pending_manual_binding"}]},
    {"id": "project-eta",        "port": 9229, "root": str(REPO / "_projects" / "project-eta"),     "status": "pending_manual_binding",
     "agents": [{"id": "agent-eta-001", "role": "executor", "conv": None, "profile": "cdp-profile-eta", "status": "pending_manual_binding"}]},
    {"id": "project-theta",      "port": 9230, "root": str(REPO / "_projects" / "project-theta"),   "status": "pending_manual_binding",
     "agents": [{"id": "agent-theta-001", "role": "executor", "conv": None, "profile": "cdp-profile-theta", "status": "pending_manual_binding"}]},
    {"id": "project-iota",       "port": 9231, "root": str(REPO / "_projects" / "project-iota"),    "status": "pending_manual_binding",
     "agents": [{"id": "agent-iota-001", "role": "executor", "conv": None, "profile": "cdp-profile-iota", "status": "pending_manual_binding"}]},
]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_registry() -> dict:
    """Build PROJECT_REGISTRY.json for all 10 projects."""
    registry = {
        "schema_version": "1.0.0",
        "awsp_version": "1.3.0",
        "generated_at": utc_now(),
        "total_projects": len(PROJECTS),
        "base_port": 9222,
        "port_range": [9222, 9231],
        "projects": {},
    }
    for proj in PROJECTS:
        registry["projects"][proj["id"]] = {
            "project_id": proj["id"],
            "cdp_port": proj["port"],
            "cdp_endpoint": f"http://localhost:{proj['port']}",
            "project_root": proj["root"],
            "profile_dir": str(PROFILES_DIR / proj["id"]),
            "binding_status": proj["status"],
            "registered_at": utc_now(),
        }
    return registry


def build_binding(proj: dict) -> dict:
    """Build CONVERSATION_BINDING.json for a project."""
    bindings = []
    for agent in proj["agents"]:
        binding = {
            "agent_id": agent["id"],
            "role": agent["role"],
            "binding_status": agent["status"],
            "conversation_id": agent["conv"] if agent["conv"] else f"pending-{proj['id']}-001",
            "chat_url": f"https://chatgpt.com/c/{agent['conv']}" if agent["conv"] else None,
            "browser_profile_id": agent["profile"],
            "cdp_endpoint": f"http://localhost:{proj['port']}",
            "allowed_task_scope": ["*"] if agent["status"] == "active" else ["pending"],
            "capture_policy": {
                "must_match_run_id": True,
                "must_match_task_id": True,
                "must_include_end_marker": True,
                "forbid_last_message_only_capture": True,
            },
        }
        bindings.append(binding)

    return {
        "schema_version": "1.0.0",
        "awsp_version": "1.3.0",
        "project_id": proj["id"],
        "project_root": proj["root"],
        "default_conversation_policy": "one_agent_one_conversation",
        "bindings": bindings,
    }


def build_resource_policy() -> dict:
    """Build MULTI_PROJECT_RESOURCE_POLICY.json."""
    return {
        "schema_version": "1.0.0",
        "max_registered_projects": 10,
        "max_warm_cdp_instances": 4,
        "max_active_gpt_reviews": 2,
        "base_port": 9222,
        "port_range": [9222, 9231],
        "lazy_launch": True,
        "auto_restart": False,
        "idle_shutdown_enabled": False,
        "require_human_for_live_dispatch": True,
        "generated_at": utc_now(),
    }


def validate_registry(registry: dict) -> list[str]:
    """Validate registry structure. Returns list of issues."""
    issues = []

    projects = registry.get("projects", {})
    if len(projects) != 10:
        issues.append(f"Expected 10 projects, got {len(projects)}")

    # Check uniqueness
    ids = list(projects.keys())
    if len(ids) != len(set(ids)):
        issues.append("Duplicate project_id found")

    ports = [p["cdp_port"] for p in projects.values()]
    if len(ports) != len(set(ports)):
        issues.append("Duplicate cdp_port found")

    endpoints = [p["cdp_endpoint"] for p in projects.values()]
    if len(endpoints) != len(set(endpoints)):
        issues.append("Duplicate cdp_endpoint found")

    profile_dirs = [p["profile_dir"] for p in projects.values()]
    if len(profile_dirs) != len(set(profile_dirs)):
        issues.append("Duplicate profile_dir found")

    # Check port range
    for pid, info in projects.items():
        port = info["cdp_port"]
        if port < 9222 or port > 9231:
            issues.append(f"Port {port} for {pid} outside range 9222-9231")

    return issues


def validate_bindings(registry: dict) -> list[str]:
    """Validate all binding files. Returns list of issues."""
    issues = []
    all_agent_ids = []
    all_conv_ids_active = []

    for pid, info in registry.get("projects", {}).items():
        root = Path(info["project_root"])
        binding_path = root / ".agent" / "CONVERSATION_BINDING.json"

        if not binding_path.exists():
            # For agent-acceptance, check the main binding
            if pid == "agent-acceptance":
                binding_path = REPO / ".agent" / "CONVERSATION_BINDING.json"
            if not binding_path.exists():
                issues.append(f"Missing binding for {pid}")
                continue

        binding = json.loads(binding_path.read_text(encoding="utf-8"))

        for agent in binding.get("bindings", []):
            aid = agent.get("agent_id")
            all_agent_ids.append(aid)

            status = agent.get("binding_status")
            conv = agent.get("conversation_id")

            if status == "active":
                if conv is None or conv.startswith("pending-"):
                    issues.append(f"Agent {aid} is active but has no real conversation_id")
                if agent.get("chat_url") is None:
                    issues.append(f"Agent {aid} is active but has no chat_url")
                all_conv_ids_active.append(conv)

            if status == "pending_manual_binding":
                if conv is not None and not conv.startswith("pending-"):
                    issues.append(f"Agent {aid} is pending but has real conversation_id {conv}")

    # Check agent_id uniqueness
    if len(all_agent_ids) != len(set(all_agent_ids)):
        issues.append("Duplicate agent_id found across projects")

    # Check active conversation uniqueness
    if len(all_conv_ids_active) != len(set(all_conv_ids_active)):
        issues.append("Duplicate active conversation_id found")

    return issues


def run_batch_init() -> dict:
    """Execute the full batch initialization."""
    report = {
        "acceptance_id": "MULTI-PROJECT-REGISTRY-BATCH-INIT-A1",
        "awsp_version": "1.3.0",
        "started_at": utc_now(),
        "steps": [],
    }

    print("=" * 60)
    print("MULTI-PROJECT-REGISTRY-BATCH-INIT-A1")
    print("=" * 60)

    # Step 1: Build registry
    print("\n[Step 1] Building PROJECT_REGISTRY.json...")
    registry = build_registry()
    reg_issues = validate_registry(registry)

    step1 = {
        "step": "build_registry",
        "total_projects": len(registry["projects"]),
        "ports": sorted([p["cdp_port"] for p in registry["projects"].values()]),
        "validation_issues": reg_issues,
        "pass": len(reg_issues) == 0,
    }
    report["steps"].append(step1)
    print(f"  Projects: {len(registry['projects'])}")
    print(f"  Ports: {step1['ports']}")
    print(f"  Validation: {'PASS' if step1['pass'] else 'FAIL: ' + str(reg_issues)}")

    # Step 2: Create profile directories
    print("\n[Step 2] Creating profile directories...")
    profiles_created = 0
    for proj in PROJECTS:
        profile_dir = PROFILES_DIR / proj["id"]
        profile_dir.mkdir(parents=True, exist_ok=True)
        profiles_created += 1

    step2 = {
        "step": "create_profiles",
        "profiles_created": profiles_created,
        "profiles_dir": str(PROFILES_DIR),
        "pass": profiles_created == 10,
    }
    report["steps"].append(step2)
    print(f"  Created {profiles_created} profile directories")

    # Step 3: Create binding scaffolds (skip agent-acceptance, keep existing)
    print("\n[Step 3] Creating binding scaffolds...")
    bindings_created = 0
    for proj in PROJECTS:
        if proj["id"] == "agent-acceptance":
            # Keep existing binding, don't overwrite
            bindings_created += 1
            continue

        root = Path(proj["root"])
        agent_dir = root / ".agent"
        agent_dir.mkdir(parents=True, exist_ok=True)

        binding = build_binding(proj)
        binding_path = agent_dir / "CONVERSATION_BINDING.json"
        binding_path.write_text(
            json.dumps(binding, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        bindings_created += 1

    step3 = {
        "step": "create_bindings",
        "bindings_created": bindings_created,
        "existing_preserved": ["agent-acceptance"],
        "pass": bindings_created == 10,
    }
    report["steps"].append(step3)
    print(f"  Bindings: {bindings_created} (1 existing preserved)")

    # Step 4: Save registry
    print("\n[Step 4] Saving PROJECT_REGISTRY.json...")
    multi_cdp_launcher.save_registry(registry)
    saved_path = multi_cdp_launcher.REGISTRY_PATH

    step4 = {
        "step": "save_registry",
        "path": str(saved_path),
        "pass": saved_path.exists(),
    }
    report["steps"].append(step4)
    print(f"  Saved to: {saved_path}")

    # Step 5: Create resource policy
    print("\n[Step 5] Creating resource policy...")
    policy = build_resource_policy()
    policy_path = REPO / ".agent" / "MULTI_PROJECT_RESOURCE_POLICY.json"
    policy_path.write_text(
        json.dumps(policy, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    step5 = {
        "step": "create_resource_policy",
        "path": str(policy_path),
        "max_warm": policy["max_warm_cdp_instances"],
        "max_active": policy["max_active_gpt_reviews"],
        "lazy_launch": policy["lazy_launch"],
        "pass": policy_path.exists(),
    }
    report["steps"].append(step5)
    print(f"  Policy: max_warm={policy['max_warm_cdp_instances']}, max_active={policy['max_active_gpt_reviews']}, lazy_launch=True")

    # Step 6: Validate all bindings
    print("\n[Step 6] Validating all bindings...")
    binding_issues = validate_bindings(registry)

    step6 = {
        "step": "validate_bindings",
        "issues": binding_issues,
        "pass": len(binding_issues) == 0,
    }
    report["steps"].append(step6)
    print(f"  Validation: {'PASS' if step6['pass'] else 'ISSUES: ' + str(binding_issues)}")

    # Step 7: Port allocation report
    print("\n[Step 7] Port allocation report...")
    port_alloc = []
    for proj in PROJECTS:
        port_alloc.append({
            "project_id": proj["id"],
            "port": proj["port"],
            "profile": str(PROFILES_DIR / proj["id"]),
            "binding_status": proj["status"],
        })
        print(f"  {proj['id']:<25} port {proj['port']}  [{proj['status']}]")

    step7 = {
        "step": "port_allocation",
        "allocations": port_alloc,
        "pass": True,
    }
    report["steps"].append(step7)

    # Save detailed reports
    port_alloc_path = REPORT_DIR / "PROJECT_PORT_ALLOCATION.json"
    port_alloc_path.write_text(
        json.dumps(port_alloc, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Summary
    all_pass = all(s.get("pass", False) for s in report["steps"])
    report["completed_at"] = utc_now()
    report["overall"] = "PASS" if all_pass else "PARTIAL"
    report["total_steps"] = len(report["steps"])
    report["passed_steps"] = sum(1 for s in report["steps"] if s.get("pass"))
    report["failed_steps"] = report["total_steps"] - report["passed_steps"]

    # Save report
    report_path = REPORT_DIR / "BATCH_INIT_REPORT.json"
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\n{'=' * 60}")
    print(f"RESULT: {report['overall']} ({report['passed_steps']}/{report['total_steps']} steps)")
    print(f"Report: {report_path}")
    print(f"{'=' * 60}")

    return report


if __name__ == "__main__":
    result = run_batch_init()
    sys.exit(0 if result["overall"] == "PASS" else 1)
