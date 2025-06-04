#!/bin/bash

# Squash unpushed commits into a single commit and then push to the remote
# repository.


git fetch origin
# Check if there are any unpushed commits
if [ "$(git rev-list --count HEAD ^origin/$(git rev-parse --abbrev-ref HEAD))" -eq 0 ]; then
    echo "No unpushed commits found."
    exit 0
    fi

# Squash the unpushed commits into a single commit
git reset --soft origin/$(git rev-parse --abbrev-ref HEAD)
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "Autosync: Squashed unpushed commits as of $TIMESTAMP"
# Push the squashed commit to the remote repository
git push origin HEAD:$(git rev-parse --abbrev-ref HEAD) --force
echo "Unpushed commits have been squashed and pushed to the remote repository."
exit 0