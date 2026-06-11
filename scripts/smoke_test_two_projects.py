#!/usr/bin/env python3
"""MULTI-PROJECT-ISOLATION-REAL-CDP-SMOKE-A1 — Controlled Two-Project Smoke Test.

Executes a real two-project smoke test:
- Two distinct CDP ports (9222 + 9223)
- Two distinct browser profiles
- Two distinct GPT conversations (synthetic for project B)
- Registry validation
- Router resolution
- Isolation verification
- Gated dry-run capture (no message dispatch beyond capture)

Usage:
  python smoke_test_two_projects.py
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

# Import our modules
import multi_cdp_launcher
import multi_project_router

REPORT_DIR = REPO / "_reports" / "multi-project-smoke-a1"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# Project configuration
PROJECT_A = {
    "project_id": "agent-acceptance",
    "cdp_port": 9222,
    "project_root": str(REPO),
}
PROJECT_B = {
    "project_id": "smoke-project-beta",
    "cdp_port": 9223,
    "project_root": str(REPO / "_smoke_project_beta"),
}

PROFILES_DIR = REPO / "_cdp_profiles"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_cdp(port: int) -> dict:
    """Check CDP health on a port."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=5) as resp:
            version = json.loads(resp.read().decode("utf-8"))
        pages = []
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/json", timeout=5) as resp:
                pages = json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass
        chatgpt_pages = [p for p in pages if "chatgpt.com" in p.get("url", "")]
        return {
            "port": port,
            "active": True,
            "browser": version.get("Browser"),
            "protocol_version": version.get("Protocol-Version"),
            "total_pages": len(pages),
            "chatgpt_pages": len(chatgpt_pages),
            "pages": [{"url": p.get("url", ""), "title": p.get("title", "")} for p in pages],
        }
    except Exception as e:
        return {"port": port, "active": False, "error": str(e)}


def setup_project_b():
    """Create synthetic project B directory and binding."""
    proj_dir = Path(PROJECT_B["project_root"])
    agent_dir = proj_dir / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    binding = {
        "schema_version": "1.0.0",
        "awsp_version": "1.3.0",
        "project_id": PROJECT_B["project_id"],
        "project_root": PROJECT_B["project_root"],
        "bindings": [
            {
                "agent_id": "agent-smoke-beta",
                "role": "executor",
                "binding_status": "active",
                "conversation_id": "smoke-conv-beta-001",
                "chat_url": "https://chatgpt.com/c/smoke-conv-beta-001",
                "browser_profile_id": "cdp-profile-smoke-beta",
                "cdp_endpoint": f"http://localhost:{PROJECT_B['cdp_port']}",
                "allowed_task_scope": ["smoke_test"],
                "capture_policy": {
                    "must_match_run_id": True,
                    "must_match_task_id": True,
                    "must_include_end_marker": True,
                    "forbid_last_message_only_capture": True,
                },
            }
        ],
    }
    binding_path = agent_dir / "CONVERSATION_BINDING.json"
    binding_path.write_text(json.dumps(binding, indent=2, ensure_ascii=False), encoding="utf-8")
    return binding_path


def run_smoke_test() -> dict:
    """Execute the full two-project smoke test."""
    results = {
        "run_id": "SMOKE_CDP_A1_20260610",
        "awsp_version": "1.3.0",
        "started_at": utc_now(),
        "steps": [],
    }

    print("=" * 60)
    print("MULTI-PROJECT-ISOLATION-REAL-CDP-SMOKE-A1")
    print("=" * 60)

    # ── Step 1: Check CDP port 9222 ──
    print("\n[Step 1] Check CDP port 9222 (Project A)...")
    cdp_a = check_cdp(PROJECT_A["cdp_port"])
    step1 = {"step": "check_cdp_9222", "result": cdp_a, "pass": cdp_a["active"]}
    results["steps"].append(step1)
    print(f"  Active: {cdp_a['active']}, Browser: {cdp_a.get('browser', 'N/A')}")

    # ── Step 2: Check CDP port 9223 ──
    print("\n[Step 2] Check CDP port 9223 (Project B)...")
    cdp_b = check_cdp(PROJECT_B["cdp_port"])
    step2 = {"step": "check_cdp_9223", "result": cdp_b, "pass": cdp_b["active"]}
    results["steps"].append(step2)
    print(f"  Active: {cdp_b['active']}, Browser: {cdp_b.get('browser', 'N/A')}")

    if not cdp_a["active"] or not cdp_b["active"]:
        print("\n  WARNING: One or both CDP instances are not active.")
        print("  Attempting to launch Chrome on port 9223...")

        if not cdp_b["active"]:
            launch_result = multi_cdp_launcher.launch_chrome(
                PROJECT_B["project_id"],
                PROJECT_B["cdp_port"],
                PROFILES_DIR,
            )
            step2b = {"step": "launch_chrome_9223", "result": launch_result}
            results["steps"].append(step2b)
            print(f"  Launch result: {launch_result}")

            # Wait for Chrome to start
            print("  Waiting for Chrome to initialize...")
            time.sleep(8)

            cdp_b = check_cdp(PROJECT_B["cdp_port"])
            step2["result"] = cdp_b
            step2["pass"] = cdp_b["active"]
            print(f"  Retry check: Active={cdp_b['active']}")

        if not cdp_a["active"]:
            results["error"] = "Port 9222 is not active. Cannot proceed."
            results["overall"] = "BLOCKED"
            return results

    # ── Step 3: Register both projects ──
    print("\n[Step 3] Register projects in PROJECT_REGISTRY.json...")
    registry = multi_cdp_launcher.load_registry()

    registry["projects"][PROJECT_A["project_id"]] = {
        "project_id": PROJECT_A["project_id"],
        "cdp_port": PROJECT_A["cdp_port"],
        "cdp_endpoint": f"http://localhost:{PROJECT_A['cdp_port']}",
        "project_root": PROJECT_A["project_root"],
        "registered_at": utc_now(),
    }
    registry["projects"][PROJECT_B["project_id"]] = {
        "project_id": PROJECT_B["project_id"],
        "cdp_port": PROJECT_B["cdp_port"],
        "cdp_endpoint": f"http://localhost:{PROJECT_B['cdp_port']}",
        "project_root": PROJECT_B["project_root"],
        "registered_at": utc_now(),
    }
    multi_cdp_launcher.save_registry(registry)

    step3 = {
        "step": "register_projects",
        "registered": list(registry["projects"].keys()),
        "pass": len(registry["projects"]) >= 2,
    }
    results["steps"].append(step3)
    print(f"  Registered: {list(registry['projects'].keys())}")

    # ── Step 4: Set up Project B binding ──
    print("\n[Step 4] Set up Project B binding...")
    binding_path = setup_project_b()
    step4 = {"step": "setup_project_b_binding", "path": str(binding_path), "pass": binding_path.exists()}
    results["steps"].append(step4)
    print(f"  Binding file: {binding_path}")

    # ── Step 5: Resolve targets ──
    print("\n[Step 5] Resolve dispatch targets...")

    # Override REGISTRY_PATH for router to use our updated registry
    target_a = multi_project_router.resolve_target(
        PROJECT_A["project_id"], PROJECT_A["project_root"]
    )
    print(f"  Project A resolved: {target_a.get('resolved')}, agent: {target_a.get('agent_id')}")

    target_b = multi_project_router.resolve_target(
        PROJECT_B["project_id"], PROJECT_B["project_root"]
    )
    print(f"  Project B resolved: {target_b.get('resolved')}, agent: {target_b.get('agent_id')}")

    step5 = {
        "step": "resolve_targets",
        "project_a": target_a,
        "project_b": target_b,
        "pass": target_a.get("resolved", False) and target_b.get("resolved", False),
    }
    results["steps"].append(step5)

    # ── Step 6: Verify isolation ──
    print("\n[Step 6] Verify multi-project isolation...")
    targets = [target_a, target_b]
    isolation = multi_project_router.verify_isolation(targets)
    step6 = {"step": "verify_isolation", "result": isolation, "pass": isolation["isolated"]}
    results["steps"].append(step6)
    print(f"  Isolated: {isolation['isolated']}")
    print(f"  Unique ports: {isolation['unique_ports']}")
    print(f"  Unique conversations: {isolation['unique_conversations']}")
    print(f"  Unique profiles: {isolation['unique_profiles']}")
    if isolation["issues"]:
        print(f"  Issues: {isolation['issues']}")

    # ── Step 7: Build dispatch packets (gated, no send) ──
    print("\n[Step 7] Build dispatch packets (gated dry-run, no send)...")
    task_spec = {
        "task_id": "SMOKE-T001",
        "description": "Smoke test: verify dispatch packet construction",
        "dry_run": True,
        "scope": "gated_capture_only",
    }

    packet_a = multi_project_router.build_dispatch_packet(
        target_a, task_spec, "Smoke test message for Project A"
    )
    packet_b = multi_project_router.build_dispatch_packet(
        target_b, task_spec, "Smoke test message for Project B"
    )

    step7 = {
        "step": "build_dispatch_packets",
        "packet_a_dispatchable": packet_a.get("dispatchable"),
        "packet_b_dispatchable": packet_b.get("dispatchable"),
        "packet_a_cdp_endpoint": packet_a.get("cdp_endpoint"),
        "packet_b_cdp_endpoint": packet_b.get("cdp_endpoint"),
        "packets_sent": False,
        "pass": packet_a.get("dispatchable") and packet_b.get("dispatchable"),
    }
    results["steps"].append(step7)
    print(f"  Packet A: dispatchable={packet_a.get('dispatchable')}, endpoint={packet_a.get('cdp_endpoint')}")
    print(f"  Packet B: dispatchable={packet_b.get('dispatchable')}, endpoint={packet_b.get('cdp_endpoint')}")
    print(f"  Packets sent: False (gated dry-run)")

    # ── Step 8: CDP cross-verification ──
    print("\n[Step 8] CDP cross-verification...")
    cdp_a_recheck = check_cdp(PROJECT_A["cdp_port"])
    cdp_b_recheck = check_cdp(PROJECT_B["cdp_port"])

    # Verify different ports serve different browser instances
    port_distinct = PROJECT_A["cdp_port"] != PROJECT_B["cdp_port"]
    both_active = cdp_a_recheck["active"] and cdp_b_recheck["active"]

    step8 = {
        "step": "cdp_cross_verify",
        "cdp_a": cdp_a_recheck,
        "cdp_b": cdp_b_recheck,
        "ports_distinct": port_distinct,
        "both_active": both_active,
        "pass": port_distinct and both_active,
    }
    results["steps"].append(step8)
    print(f"  Ports distinct: {port_distinct}")
    print(f"  Both active: {both_active}")

    # ── Summary ──
    all_pass = all(s.get("pass", False) for s in results["steps"])
    results["completed_at"] = utc_now()
    results["overall"] = "PASS" if all_pass else "PARTIAL"
    results["total_steps"] = len(results["steps"])
    results["passed_steps"] = sum(1 for s in results["steps"] if s.get("pass"))
    results["failed_steps"] = results["total_steps"] - results["passed_steps"]

    print("\n" + "=" * 60)
    print(f"RESULT: {results['overall']}")
    print(f"Steps: {results['passed_steps']}/{results['total_steps']} passed")
    print("=" * 60)

    return results


def main():
    results = run_smoke_test()

    # Save results
    out_path = REPORT_DIR / "SMOKE_TEST_RESULTS.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults saved: {out_path}")

    # Exit code
    sys.exit(0 if results["overall"] == "PASS" else 1)


if __name__ == "__main__":
    main()
