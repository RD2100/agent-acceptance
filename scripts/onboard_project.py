#!/usr/bin/env python3
"""onboard_project.py — 一键为新项目绑定GPT对话。

用法:
  python scripts/onboard_project.py --project project-alpha --port 9223 --url https://chatgpt.com/c/你的对话ID

这条命令会:
  1. 在指定端口启动独立Chrome（如果未启动）
  2. 验证CDP连接
  3. 验证ChatGPT页面存在
  4. 更新CONVERSATION_BINDING.json
  5. 更新PROJECT_REGISTRY.json
  6. 运行隔离验证
  7. 输出结果

首次使用（手动步骤）:
  1. 运行本脚本（不带--url），它会启动Chrome并告诉你去登录
  2. 在弹出的Chrome窗口登录ChatGPT
  3. 开一个新对话，复制URL
  4. 再次运行本脚本，带上--url参数

示例:
  # 第一步：启动Chrome（去窗口里登录ChatGPT）
  python scripts/onboard_project.py --project project-alpha --port 9223

  # 第二步：登录完毕后，绑定对话URL
  python scripts/onboard_project.py --project project-alpha --port 9223 --url https://chatgpt.com/c/xxxxx
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import multi_cdp_launcher
import multi_project_router

PROFILES_DIR = REPO / "_cdp_profiles"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def check_cdp(port: int) -> dict:
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
            "active": True,
            "browser": version.get("Browser"),
            "pages": len(pages),
            "chatgpt_pages": len(chatgpt_pages),
            "chatgpt_urls": [p.get("url", "") for p in pages if "chatgpt.com" in p.get("url", "")],
        }
    except Exception as e:
        return {"active": False, "error": str(e)}


def launch_chrome_for_project(project_id: str, port: int) -> bool:
    profile_dir = PROFILES_DIR / project_id
    profile_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    try:
        if sys.platform == "win32":
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        print(f"  Chrome launched on port {port}")
        print(f"  Profile: {profile_dir}")
        return True
    except Exception as e:
        print(f"  ERROR launching Chrome: {e}")
        return False


def update_registry(project_id: str, port: int):
    registry = multi_cdp_launcher.load_registry()
    registry["projects"][project_id] = {
        "project_id": project_id,
        "cdp_port": port,
        "cdp_endpoint": f"http://localhost:{port}",
        "project_root": str(REPO / "_projects" / project_id),
        "profile_dir": str(PROFILES_DIR / project_id),
        "binding_status": "pending_manual_binding",
        "registered_at": utc_now(),
    }
    multi_cdp_launcher.save_registry(registry)
    print(f"  Registry updated: {project_id} -> port {port}")


def update_binding(project_id: str, port: int, conversation_id: str, profile_id: str):
    proj_dir = REPO / "_projects" / project_id
    agent_dir = proj_dir / ".agent"
    agent_dir.mkdir(parents=True, exist_ok=True)

    chat_url = f"https://chatgpt.com/c/{conversation_id}"

    binding = {
        "schema_version": "1.0.0",
        "awsp_version": "1.3.0",
        "project_id": project_id,
        "project_root": str(proj_dir),
        "bindings": [{
            "agent_id": f"agent-{project_id}-001",
            "role": "executor",
            "binding_status": "active",
            "conversation_id": conversation_id,
            "chat_url": chat_url,
            "browser_profile_id": profile_id,
            "cdp_endpoint": f"http://localhost:{port}",
            "allowed_task_scope": ["*"],
            "capture_policy": {
                "must_match_run_id": True,
                "must_match_task_id": True,
                "must_include_end_marker": True,
                "forbid_last_message_only_capture": True,
            },
        }],
    }

    binding_path = agent_dir / "CONVERSATION_BINDING.json"
    binding_path.write_text(json.dumps(binding, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Binding updated: {binding_path}")
    print(f"  Conversation: {chat_url}")

    # Update registry binding_status
    registry = multi_cdp_launcher.load_registry()
    if project_id in registry["projects"]:
        registry["projects"][project_id]["binding_status"] = "active"
        multi_cdp_launcher.save_registry(registry)
        print(f"  Registry status: active")

    return chat_url


def verify_isolation_for_project(project_id: str) -> dict:
    targets = multi_project_router.resolve_all()
    iso = multi_project_router.verify_isolation(targets)
    return iso


def main():
    parser = argparse.ArgumentParser(
        description="一键绑定项目GPT对话",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--project", required=True, help="项目ID，如 project-alpha")
    parser.add_argument("--port", type=int, required=True, help="CDP端口，如 9223")
    parser.add_argument("--url", default=None, help="ChatGPT对话URL，如 https://chatgpt.com/c/xxxxx")
    args = parser.parse_args()

    project_id = args.project
    port = args.port
    profile_id = f"cdp-profile-{project_id}"

    print(f"\n{'='*60}")
    print(f"项目上线: {project_id} (port {port})")
    print(f"{'='*60}")

    # Step 1: Check or launch Chrome
    print(f"\n[1] 检查CDP端口 {port}...")
    cdp = check_cdp(port)

    if cdp["active"]:
        print(f"  Chrome已运行: {cdp.get('browser', 'unknown')}")
        print(f"  ChatGPT页面: {cdp.get('chatgpt_pages', 0)}")
    else:
        print(f"  端口 {port} 未响应，启动Chrome...")
        if not launch_chrome_for_project(project_id, port):
            sys.exit(1)

        print(f"\n  等待Chrome启动...")
        time.sleep(5)
        cdp = check_cdp(port)

        if not cdp["active"]:
            print(f"  ERROR: Chrome启动失败")
            sys.exit(1)

        print(f"\n  ★ 请在弹出的Chrome窗口中:")
        print(f"    1. 登录你的ChatGPT账号")
        print(f"    2. 开一个新对话（命名为: {project_id} Reviews）")
        print(f"    3. 从地址栏复制对话URL")
        print(f"    4. 重新运行本命令，加上 --url 参数:")
        print(f"       python scripts/onboard_project.py --project {project_id} --port {port} --url https://chatgpt.com/c/你的对话ID")
        sys.exit(0)

    # Step 2: If no URL provided, show instructions
    if not args.url:
        print(f"\n  Chrome已就绪。请按以下步骤操作:")
        if cdp.get("chatgpt_pages", 0) > 0:
            print(f"\n  已发现ChatGPT页面:")
            for u in cdp.get("chatgpt_urls", []):
                print(f"    - {u}")
            print(f"\n  如果上面有你要用的对话URL，直接复制并运行:")
        else:
            print(f"\n  1. 在端口{port}的Chrome窗口中登录ChatGPT")
            print(f"  2. 开一个新对话")
            print(f"  3. 复制URL后运行:")

        print(f"     python scripts/onboard_project.py --project {project_id} --port {port} --url https://chatgpt.com/c/你的对话ID")
        sys.exit(0)

    # Step 3: Parse URL and bind
    print(f"\n[2] 绑定对话...")
    url = args.url
    conv_id = url.split("/c/")[-1].split("?")[0].split("#")[0] if "/c/" in url else url
    print(f"  Conversation ID: {conv_id}")

    # Verify this conversation exists in CDP pages
    if conv_id not in str(cdp.get("chatgpt_urls", [])):
        print(f"  WARNING: 对话ID在CDP页面列表中未找到（可能需要刷新页面）")
        print(f"  CDP页面: {cdp.get('chatgpt_urls', [])}")
        # Still proceed — the URL might be valid even if not currently in page list

    update_registry(project_id, port)
    chat_url = update_binding(project_id, port, conv_id, profile_id)

    # Step 4: Verify isolation
    print(f"\n[3] 隔离验证...")
    iso = verify_isolation_for_project(project_id)
    print(f"  isolated: {iso['isolated']}")
    print(f"  unique_ports: {iso['unique_ports']}")
    print(f"  unique_conversations: {iso['unique_conversations']}")
    print(f"  unique_profiles: {iso['unique_profiles']}")
    if iso["issues"]:
        print(f"  问题:")
        for issue in iso["issues"]:
            print(f"    - {issue}")

    # Summary
    print(f"\n{'='*60}")
    print(f"项目 {project_id} 上线完成!")
    print(f"  端口: {port}")
    print(f"  对话: {chat_url}")
    print(f"  配置文件: {profile_id}")
    print(f"  隔离状态: {'通过' if iso['isolated'] else '有冲突（见上方）'}")
    print(f"{'='*60}")

    # Save onboard result
    result = {
        "project_id": project_id,
        "port": port,
        "conversation_id": conv_id,
        "chat_url": chat_url,
        "profile_id": profile_id,
        "isolated": iso["isolated"],
        "issues": iso["issues"],
        "onboarded_at": utc_now(),
    }
    result_dir = REPO / "_reports" / "multi-project-batch-init-a1"
    result_dir.mkdir(parents=True, exist_ok=True)
    result_path = result_dir / f"ONBOARD_{project_id}.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
