#!/bin/bash

# Squash unpushed commits into a single commit and then push to the remote
# repository.

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

git fetch origin
# Check if there are any unpushed commits
if [ "$(git rev-list --count HEAD ^origin/$(git rev-parse --abbrev-ref HEAD))" -eq 0 ]; then
    echo "$TIMESTAMP: No unpushed commits found." >> ~/autopush.log
    exit 0
    fi

# Squash the unpushed commits into a single commit
git reset --soft origin/$(git rev-parse --abbrev-ref HEAD)
# NOTE: Assumes my fork -> https://github.com/orjahren/ai-commit 
AI_MSG=$(node ai-commit/index.js --message-only 2>/dev/null)
git commit -m "Autosync: $AI_MSG"
# Push the squashed commit to the remote repository
git push origin HEAD:$(git rev-parse --abbrev-ref HEAD) --force
echo "$TIMESTAMP: Unpushed commits have been squashed and pushed to the remote repository.\n" >> ~/autopush.log
exit 0