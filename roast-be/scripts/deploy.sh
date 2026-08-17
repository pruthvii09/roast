#!/usr/bin/env bash
# Runs on the EC2 instance itself — either manually over SSH, or invoked by
# .github/workflows/deploy.yml on every push to main. Pulls the latest
# code, rebuilds, and restarts the stack with zero manual steps beyond
# this one command.
#
# No --env-file flag below on purpose: `docker compose` already defaults
# to a file literally named ".env" in the project directory for both
# ${VAR} substitution AND is what every service's `env_file: - .env`
# (docker-compose.prod.yml) resolves against — the two mechanisms only
# stay in sync if neither is told to use a different filename.
set -euo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/roast-be}"
cd "$DEPLOY_DIR"

echo "==> Pulling latest code"
git fetch origin
git reset --hard origin/main

if [ ! -f .env ]; then
  echo "ERROR: .env not found in $DEPLOY_DIR — copy .env.prod.example to .env and fill it in first."
  echo "See docs/DEPLOY_EC2.md."
  exit 1
fi

echo "==> Building and starting the stack (this box is memory-constrained — a"
echo "    from-scratch build can take a few minutes; that's expected, not stuck)"
docker compose -f docker-compose.prod.yml -f docker-compose.ec2.yml up -d --build

echo "==> Pruning old, unreferenced images (keeps the 30GB free-tier EBS volume from filling up)"
docker image prune -f

echo "==> Waiting for web to report ready..."
for _ in $(seq 1 20); do
  if docker compose -f docker-compose.prod.yml -f docker-compose.ec2.yml \
      exec -T web python -c "import urllib.request as u; u.urlopen('http://localhost:8000/api/v1/health/ready/', timeout=3)" 2>/dev/null; then
    echo "==> Deploy complete — web is healthy."
    exit 0
  fi
  sleep 3
done

echo "WARNING: web didn't report ready within ~60s. Check logs:"
echo "  docker compose -f docker-compose.prod.yml -f docker-compose.ec2.yml logs --tail 100 web"
exit 1
