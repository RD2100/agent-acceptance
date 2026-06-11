"""Push agent-acceptance to GitHub via gh CLI token."""
import subprocess, sys, os
os.chdir("D:/agent-acceptance")
# Get token
r = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
if r.returncode != 0:
    print(f"TOKEN FAILED: {r.stderr}")
    sys.exit(1)
token = r.stdout.strip()
print(f"TOKEN: {token[:8]}...")
# Set remote with token
subprocess.run(["git", "remote", "set-url", "origin", f"https://oauth2:{token}@github.com/RD2100/agent-acceptance.git"], check=True)
# Push
env = os.environ.copy()
env["GIT_TERMINAL_PROMPT"] = "0"
push = subprocess.run(["git", "push", "origin", "master"], capture_output=True, text=True, timeout=60, env=env)
print(f"PUSH: exit={push.returncode}")
print(push.stdout[:500])
print(push.stderr[:500])
