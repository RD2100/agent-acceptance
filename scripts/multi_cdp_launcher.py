#!/usr/bin/env python3
"""Single-CDP Launcher — manages one persistent Chrome instance for all projects.

All projects share a single Chrome instance with:
- One remote debugging port (default 9222)
- One persistent user-data-dir (cookies/login survive restarts)
- One CDP endpoint

Project isolation is achieved through **distinct ChatGPT conversations**,
not separate browser instances.  Each project opens a different
chatgpt.com/c/<conversation-id> tab in the shared Chrome.

Usage:
  python multi_cdp_launcher.py launch          # start shared Chrome
  python multi_cdp_launcher.py status          # check Chrome + tab count
  python multi_cdp_launcher.py register --project-id X --port 9222
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO / ".agent" / "PROJECT_REGISTRY.json"

# Chrome executable paths (Windows/macOS/Linux)
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
]

DEFAULT_CDP_PORT = 9222
DEFAULT_PROFILE_DIR = REPO / "_cdp_profiles" / "shared"


def _find_chrome() -> str | None:
    """Find Chrome executable on the system."""
    for p in CHROME_PATHS:
        if Path(p).exists():
            return p
    return None


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_port(port: int) -> bool:
    """Check if a CDP port is already active."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def _get_version(port: int) -> dict | None:
    """Get CDP version info from a port."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def _get_pages(port: int) -> list[dict]:
    """Get list of open pages from CDP."""
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json", timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []


# ── Registry Management ───────────────────────────────────────────────


def load_registry() -> dict:
    """Load the global project registry."""
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return {
        "schema_version": "2.0.0",
        "awsp_version": "1.3.0",
        "architecture": "single_chrome_shared_cdp",
        "generated_at": _utc_now(),
        "projects": {},
    }


def save_registry(registry: dict) -> None:
    """Save the global project registry."""
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    registry["updated_at"] = _utc_now()
    # Ensure v2 shared-CDP fields are always present
    registry.setdefault("architecture", "single_chrome_shared_cdp")
    registry.setdefault("shared_cdp_port", DEFAULT_CDP_PORT)
    registry.setdefault("shared_cdp_endpoint", f"http://localhost:{DEFAULT_CDP_PORT}")
    registry.setdefault("shared_profile_dir", str(DEFAULT_PROFILE_DIR))
    REGISTRY_PATH.write_text(
        json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# ── Chrome Instance Management ─────────────────────────────────────────


def launch_chrome(
    port: int = DEFAULT_CDP_PORT,
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    chrome_path: str | None = None,
) -> dict:
    """Launch a single shared Chrome instance with persistent profile.

    All projects share this one Chrome.  Login state persists across
    restarts because we use one persistent user-data-dir.

    Returns a dict with launch result.
    """
    if chrome_path is None:
        chrome_path = _find_chrome()
    if chrome_path is None:
        return {
            "launched": False,
            "error": "Chrome executable not found",
        }

    profile_dir.mkdir(parents=True, exist_ok=True)

    # Check if CDP port is already active
    if _check_port(port):
        version = _get_version(port)
        return {
            "launched": False,
            "already_active": True,
            "browser": version.get("Browser", "unknown") if version else "unknown",
            "cdp_endpoint": f"http://localhost:{port}",
            "profile_dir": str(profile_dir),
        }

    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    try:
        if sys.platform == "win32":
            process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            process = subprocess.Popen(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        return {
            "launched": True,
            "pid": process.pid,
            "cdp_endpoint": f"http://localhost:{port}",
            "profile_dir": str(profile_dir),
            "launched_at": _utc_now(),
        }
    except Exception as e:
        return {
            "launched": False,
            "error": str(e),
        }


def verify_instance(port: int = DEFAULT_CDP_PORT) -> dict:
    """Verify the shared Chrome instance is responsive."""
    version = _get_version(port)
    if version is None:
        return {"port": port, "active": False}

    pages = _get_pages(port)
    chat_pages = [p for p in pages if isinstance(p, dict) and "chatgpt.com" in p.get("url", "")]

    return {
        "port": port,
        "active": True,
        "browser": version.get("Browser"),
        "protocol_version": version.get("Protocol-Version"),
        "total_pages": len(pages),
        "chatgpt_pages": len(chat_pages),
    }


def list_chatgpt_tabs(port: int = DEFAULT_CDP_PORT) -> list[dict]:
    """List all open ChatGPT conversation tabs in the shared Chrome."""
    pages = _get_pages(port)
    tabs = []
    for p in pages:
        if not isinstance(p, dict):
            continue
        url = p.get("url", "")
        if "chatgpt.com" not in url:
            continue
        # Extract conversation ID from URL
        conv_id = None
        if "/c/" in url:
            conv_id = url.split("/c/")[-1].split("?")[0].split("#")[0]
        tabs.append({
            "title": p.get("title", ""),
            "url": url,
            "conversation_id": conv_id,
        })
    return tabs


# ── CLI ────────────────────────────────────────────────────────────────


def cmd_launch(args) -> int:
    """Launch the shared Chrome instance."""
    profile_dir = Path(args.profile_dir)
    result = launch_chrome(args.port, profile_dir)

    if result.get("already_active"):
        print(f"Chrome already active on port {args.port}")
        print(f"  Browser: {result.get('browser')}")
        print(f"  CDP:     {result.get('cdp_endpoint')}")
        return 0

    if result.get("launched"):
        print(f"Chrome launched on port {args.port} (pid: {result.get('pid')})")
        print(f"  CDP:     {result.get('cdp_endpoint')}")
        print(f"  Profile: {result.get('profile_dir')}")
        print(f"\nAll projects share this single Chrome instance.")
        print(f"Log in to ChatGPT once — the session persists across restarts.")
        return 0

    print(f"Failed: {result.get('error', 'unknown')}")
    return 1


def cmd_status(args) -> int:
    """Show status of the shared Chrome and open ChatGPT tabs."""
    status = verify_instance(args.port)

    if not status["active"]:
        print(f"Chrome NOT active on port {args.port}")
        return 1

    print(f"Chrome active on port {args.port}")
    print(f"  Browser:      {status.get('browser', '-')}")
    print(f"  Protocol:     {status.get('protocol_version', '-')}")
    print(f"  Total pages:  {status['total_pages']}")
    print(f"  ChatGPT tabs: {status['chatgpt_pages']}")

    if status["chatgpt_pages"] > 0:
        print(f"\nOpen ChatGPT conversations:")
        tabs = list_chatgpt_tabs(args.port)
        for tab in tabs:
            conv = tab.get("conversation_id", "unknown")
            title = tab.get("title", "")[:50]
            print(f"  [{conv[:12]}...] {title}")

    return 0


def cmd_register(args) -> int:
    """Register a project in the shared registry."""
    registry = load_registry()

    # Ensure architecture field is set
    registry.setdefault("architecture", "single_chrome_shared_cdp")
    registry.setdefault("shared_cdp_port", args.port)
    registry.setdefault("shared_cdp_endpoint", f"http://localhost:{args.port}")
    registry.setdefault("shared_profile_dir", str(DEFAULT_PROFILE_DIR))

    registry["projects"][args.project_id] = {
        "project_id": args.project_id,
        "project_root": args.project_root,
        "binding_status": "pending_binding",
        "registered_at": _utc_now(),
    }
    save_registry(registry)
    print(f"Registered {args.project_id}")
    print(f"  All projects share CDP on port {args.port}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Single-CDP Chrome Launcher")
    sub = parser.add_subparsers(dest="command")

    p_launch = sub.add_parser("launch", help="Launch shared Chrome")
    p_launch.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_launch.add_argument("--profile-dir", default=str(DEFAULT_PROFILE_DIR))

    p_status = sub.add_parser("status", help="Show Chrome status")
    p_status.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)

    p_reg = sub.add_parser("register", help="Register project")
    p_reg.add_argument("--project-id", required=True)
    p_reg.add_argument("--port", type=int, default=DEFAULT_CDP_PORT)
    p_reg.add_argument("--project-root", default=None)

    args = parser.parse_args()

    if args.command == "launch":
        sys.exit(cmd_launch(args))
    elif args.command == "status":
        sys.exit(cmd_status(args))
    elif args.command == "register":
        sys.exit(cmd_register(args))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
