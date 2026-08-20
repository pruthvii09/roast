#!/usr/bin/env bash
# Runs on the EC2 instance itself — either manually over SSH, or invoked by
# .github/workflows/deploy.yml on every push to main that touches
# roast-be/ (a frontend-only push doesn't trigger this — see that
# workflow's `paths:` filter). Pulls the latest code, rebuilds, and
# restarts the stack with zero manual steps beyond this one command.
#
# No --env-file flag below on purpose: `docker compose` already defaults
# to a file literally named ".env" in the project directory for both
# ${VAR} substitution AND is what every service's `env_file: - .env`
# (docker-compose.prod.yml) resolves against — the two mechanisms only
# stay in sync if neither is told to use a different filename.
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/roast/roast-be}"
cd "$DEPLOY_DIR"

echo "==> Pulling latest code"
git fetch origin
git reset --hard origin/main

if [ ! -f .env ]; then
  echo "ERROR: .env not found in $DEPLOY_DIR — copy .env.prod.example to .env and fill it in first."
  echo "See docs/DEPLOY_EC2.md."
  exit 1
fi

COMPOSE="docker compose -f docker-compose.prod.yml -f docker-compose.ec2.yml"

echo "==> Building and starting the stack (this box is disk-constrained — the"
echo "    root volume is ~7GB, not the 30GB free-tier allowance; building all"
echo "    three service images at once via 'up --build' needs more peak disk"
echo "    than that leaves free and reliably fails with ENOSPC mid-build. So:"
echo "    build+recreate one service at a time, pruning between each, keeping"
echo "    peak usage to roughly one image's worth rather than three's)."
for service in web worker beat; do
  echo "==> Building $service"
  $COMPOSE build "$service"
  echo "==> Recreating $service"
  $COMPOSE up -d --no-build "$service"
  echo "==> Reclaiming space from the image $service just replaced"
  docker image prune -af >/dev/null
done

docker builder prune -af >/dev/null

echo "==> Waiting for web to report ready..."
for _ in $(seq 1 20); do
  if $COMPOSE exec -T web python -c \
      "import urllib.request as u; u.urlopen('http://localhost:8000/api/v1/health/ready/', timeout=3)" 2>/dev/null; then
    echo "==> Deploy complete — web is healthy."
    exit 0
  fi
  sleep 3
done

echo "WARNING: web didn't report ready within ~60s. Check logs:"
echo "  $COMPOSE logs --tail 100 web"
exit 1
