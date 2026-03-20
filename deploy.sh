#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_HOST="${DEPLOY_SSH_HOST:-ovh2}"
REMOTE_PATH="/opt/cantheyfuckme"
REBOOT_SCRIPT="${HOME}/Projects/shared/reboot-vps.sh"

# SSH kicker: test connectivity, reboot via OVH API if unreachable
ensure_ssh() {
  if ssh -o ConnectTimeout=10 -o BatchMode=yes "$SSH_HOST" "true" 2>/dev/null; then
    return 0
  fi
  echo "SSH unreachable — kicking server via OVH API..."
  if [[ -x "$REBOOT_SCRIPT" ]]; then
    "$REBOOT_SCRIPT" ovh2 --wait
  else
    echo "ERROR: reboot script not found: $REBOOT_SCRIPT" >&2
    exit 1
  fi
}

echo "=== cantheyfuckme Deploy ==="
ensure_ssh
echo ""

# Step 1: Sync project to server
echo ">> Syncing to ${SSH_HOST}:${REMOTE_PATH}..."
ssh "${SSH_HOST}" "sudo mkdir -p ${REMOTE_PATH} && sudo chown ubuntu:ubuntu ${REMOTE_PATH}"
rsync -az --delete \
  --exclude='node_modules/' \
  --exclude='.git/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='.env' \
  --exclude='frontend/dist/' \
  -e "ssh" \
  "$SCRIPT_DIR/" \
  "${SSH_HOST}:${REMOTE_PATH}/"

# Step 2: Build and start containers
echo ""
echo ">> Building and starting containers..."
ssh "${SSH_HOST}" "cd ${REMOTE_PATH} && docker compose -f docker-compose.prod.yml up -d --build"

# Step 3: Sync Caddy config and reload
echo ""
echo ">> Updating Caddy config..."
scp -q "$SCRIPT_DIR/caddy.conf" "${SSH_HOST}:/tmp/cantheyfuckme.com"
ssh "${SSH_HOST}" "sudo mv /tmp/cantheyfuckme.com /etc/caddy/sites/cantheyfuckme.com && sudo systemctl reload caddy"

# Step 4: Health check
echo ""
echo ">> Checking health..."
sleep 5
ssh "${SSH_HOST}" "curl -sf http://127.0.0.1:8081/api/health && echo"

echo ""
echo "=== Deploy complete ==="
echo "Site: https://cantheyfuckme.com"
