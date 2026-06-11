#!/bin/bash
cd D:/agent-acceptance
export GIT_TERMINAL_PROMPT=0
TOKEN=$(gh auth token 2>/dev/null)
if [ -n "$TOKEN" ]; then
    git remote set-url origin "https://oauth2:${TOKEN}@github.com/RD2100/agent-acceptance.git" 2>/dev/null
    git push origin master 2>&1
else
    echo "NO TOKEN"
fi
