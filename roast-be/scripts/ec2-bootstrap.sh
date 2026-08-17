#!/usr/bin/env bash
# One-time setup for a fresh Ubuntu 24.04 EC2 instance. Run once over SSH:
#   ssh ubuntu@<instance-ip>
#   curl -fsSL https://raw.githubusercontent.com/<you>/roast-be/main/scripts/ec2-bootstrap.sh | bash
# (or scp this file over and run it directly, if you'd rather not curl|bash
# something — either is fine, this script doesn't do anything it doesn't
# print to stdout as it goes.)
#
# Idempotent — safe to re-run (e.g. after an instance reboot wiped nothing,
# or to pick up a script update) without duplicating the swap file or
# re-cloning the repo.
set -euo pipefail

REPO_URL="${REPO_URL:-}"
DEPLOY_DIR="${DEPLOY_DIR:-/opt/roast-be}"
SWAP_FILE="/swapfile"
SWAP_SIZE_MB=2048

echo "==> Updating apt and installing base packages"
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg git

echo "==> Setting up a ${SWAP_SIZE_MB}MB swap file (t2/t3.micro's 1GB RAM needs this — see docker-compose.ec2.yml's comment on why)"
if [ ! -f "$SWAP_FILE" ]; then
  sudo fallocate -l "${SWAP_SIZE_MB}M" "$SWAP_FILE"
  sudo chmod 600 "$SWAP_FILE"
  sudo mkswap "$SWAP_FILE"
  sudo swapon "$SWAP_FILE"
  # Persist across reboots.
  if ! grep -q "^$SWAP_FILE" /etc/fstab; then
    echo "$SWAP_FILE none swap sw 0 0" | sudo tee -a /etc/fstab > /dev/null
  fi
else
  echo "    swap file already exists, skipping"
fi
sudo sysctl -w vm.swappiness=10 > /dev/null # prefer RAM over swap when there's a real choice; swap is a safety net, not the default
free -h

echo "==> Installing Docker Engine + Compose plugin (official repo, not the older docker.io apt package)"
if ! command -v docker &> /dev/null; then
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER"
  echo "    Docker installed. You'll need to log out and back in (or run 'newgrp docker')"
  echo "    for the docker group membership to take effect in this shell."
else
  echo "    Docker already installed, skipping"
fi

echo "==> Preparing deploy directory: $DEPLOY_DIR"
if [ ! -d "$DEPLOY_DIR/.git" ]; then
  if [ -z "$REPO_URL" ]; then
    echo "    REPO_URL not set and $DEPLOY_DIR isn't a git checkout yet."
    echo "    Re-run as: REPO_URL=https://github.com/<you>/roast-be.git bash ec2-bootstrap.sh"
    echo "    (or clone it yourself into $DEPLOY_DIR before re-running)"
    exit 1
  fi
  sudo mkdir -p "$DEPLOY_DIR"
  sudo chown "$USER":"$USER" "$DEPLOY_DIR"
  git clone "$REPO_URL" "$DEPLOY_DIR"
else
  echo "    $DEPLOY_DIR already a git checkout, skipping clone"
fi

if [ ! -f "$DEPLOY_DIR/.env" ]; then
  cp "$DEPLOY_DIR/.env.prod.example" "$DEPLOY_DIR/.env"
  # Must be named exactly ".env" — docker-compose.prod.yml's services
  # declare `env_file: - .env` as a literal path. `docker compose`'s
  # --env-file flag only affects ${VAR} substitution within the compose
  # YAML itself, it does NOT redirect that env_file: reference — naming
  # this anything else silently loads the wrong (or no) file at runtime.
  echo "    Created $DEPLOY_DIR/.env from the template — edit it now and fill"
  echo "    in every <CHANGE ME> before your first deploy: nano $DEPLOY_DIR/.env"
else
  echo "    $DEPLOY_DIR/.env already exists, leaving it alone"
fi

echo ""
echo "==> Bootstrap done. Next steps:"
echo "    1. If this was Docker's first install: log out and back in (or 'newgrp docker')."
echo "    2. Edit $DEPLOY_DIR/.env — every <CHANGE ME> must be filled in."
echo "    3. Run the first deploy manually once: cd $DEPLOY_DIR && bash scripts/deploy.sh"
echo "    4. After that works, wire up GitHub Actions (docs/DEPLOY_EC2.md) so every"
echo "       push to main runs scripts/deploy.sh over SSH automatically."
