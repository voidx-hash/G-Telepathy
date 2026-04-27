#!/usr/bin/env bash
# =============================================================================
# G Telepathy — Deploy Script
# Run from your LOCAL machine to push code updates to the GCP VM.
#
# Usage:
#   ./deploy/deploy.sh [VM_NAME] [ZONE]
#
# Example:
#   ./deploy/deploy.sh gtelepath-vm us-central1-a
#
# Requirements:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - SSH access to the VM configured (gcloud compute ssh works)
# =============================================================================
set -euo pipefail

VM_NAME="${1:-gtelepath-vm}"
ZONE="${2:-us-central1-a}"
APP_DIR="/opt/gtelepath"
APP_USER="gtelepath"

echo "==> Deploying G Telepathy backend to $VM_NAME ($ZONE)..."

# ── 1. Push latest code ───────────────────────────────────────────────────────
echo "==> Pulling latest code on VM..."
gcloud compute ssh "$VM_NAME" --zone="$ZONE" -- \
    "sudo -u $APP_USER git -C $APP_DIR pull origin main"

# ── 2. Update dependencies ────────────────────────────────────────────────────
echo "==> Updating Python dependencies..."
gcloud compute ssh "$VM_NAME" --zone="$ZONE" -- \
    "sudo -u $APP_USER $APP_DIR/venv/bin/pip install --no-cache-dir -r $APP_DIR/backend/requirements.txt"

# ── 3. Reload systemd service ─────────────────────────────────────────────────
echo "==> Restarting backend service..."
gcloud compute ssh "$VM_NAME" --zone="$ZONE" -- \
    "sudo systemctl restart gtelepath"

# ── 4. Health check ───────────────────────────────────────────────────────────
echo "==> Waiting for service to start..."
sleep 5
gcloud compute ssh "$VM_NAME" --zone="$ZONE" -- \
    "curl -sf http://localhost:8000/health && echo '  Health check: OK' || echo '  Health check: FAILED'"

echo ""
echo "  Deployment complete!"
echo "  Logs: gcloud compute ssh $VM_NAME --zone=$ZONE -- 'sudo journalctl -u gtelepath -n 50'"
