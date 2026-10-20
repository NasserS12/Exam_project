#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

git fetch --quiet origin dev

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/dev)

if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

echo "Deploying $REMOTE"
git merge --ff-only origin/dev
sudo docker compose up -d --build
sudo docker image prune -f
