"""Quick fix: git add + commit + push binding."""
import subprocess, sys

def git(cmd):
    r = subprocess.run(["git"] + cmd, capture_output=True, text=True, timeout=120, cwd="D:/agent-acceptance")
    return r.returncode, r.stdout + r.stderr

# Reset old tracked files
code, out = git(["reset", "HEAD", "--", ".ai/tasks/"])
code, out = git(["add", "PROJECT_HISTORY.md"])
code, out = git(["commit", "-m", "docs: bind PAPER-C4 accepted_with_limitation"])
print(out[-200:])
if code != 0:
    # Check if nothing to commit
    code2, out2 = git(["status", "--short"])
    if "PROJECT_HISTORY" not in out2:
        print("Nothing to commit - already committed")
    else:
        print(f"Commit failed: {out}")
        sys.exit(1)

code, out = git(["push", "origin", "master"])
print(out[-100:])
print("DONE" if code == 0 else f"PUSH exit={code}")
sys.exit(code)
