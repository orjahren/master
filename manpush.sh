#!/bin/bash

# Squash unpushed commits into a single commit and then push to the remote
# repository.

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

git fetch origin

# Get folder from ../akademika/master/essay 
rsync --recursive ../akademika/master/essay/ essay 
if [ $? -ne 0 ]; then
    echo "Mansync: Error during rsync. Please check the logs."
    exit 1
fi  

git add essay

# NOTE: Assumes my fork -> https://github.com/orjahren/ai-commit
AI_MSG=$(node ../ai-commit-message/index.js --message-only 2>> ~/manpush.log)
if [ $? -ne 0 ]; then
    echo "Mansync: Unable to generate commit message. Please check the logs."
    exit 1
fi

git commit -m "Mansync: $AI_MSG"
# Push the squashed commit to the remote repository
git push origin HEAD:$(git rev-parse --abbrev-ref HEAD)
echo "$TIMESTAMP: Unpushed commits have been squashed and pushed to the remote repository." >> ~/manpush.log
exit 0