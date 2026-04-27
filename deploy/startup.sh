#!/usr/bin/env bash
# =============================================================================
# G Telepathy — GCP VM Startup / Bootstrap Script
#
# Run this ONCE on a fresh Debian/Ubuntu GCP VM instance.
# It installs all dependencies, clones the repo, sets up the service,
# installs nginx, and configures SSL with Let's Encrypt.
#
# Usage:
#   1. SSH into your VM:  gcloud compute ssh gtelepath-vm --zone=ZONE
#   2. Upload this script: gcloud compute scp deploy/startup.sh gtelepath-vm:~/
#   3. Run it:             chmod +x ~/startup.sh && sudo ~/startup.sh
#
# Or paste it into the "Startup script" field in GCP console for auto-run.
# =============================================================================
set -euo pipefail

# ── Configuration — edit these before running ─────────────────────────────────
REPO_URL="https://github.com/voidx-hash/G-Telepathy.git"
DOMAIN="your-domain-or-vm-ip"          # e.g. api.gtelepathy.com or 34.x.x.x
APP_DIR="/opt/gtelepath"
APP_USER="gtelepath"
PYTHON_VERSION="3.11"

# ─────────────────────────────────────────────────────────────────────────────
echo "==> [1/8] Updating system packages..."
apt-get update -y
apt-get upgrade -y
apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python3-pip \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    ufw \
    unzip \
    build-essential \
    libpq-dev

echo "==> [2/8] Creating application user and directories..."
# Create dedicated service user with no login shell
if ! id "$APP_USER" &>/dev/null; then
    useradd -r -m -d "$APP_DIR" -s /sbin/nologin "$APP_USER"
fi
mkdir -p "$APP_DIR/logs"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "==> [3/8] Cloning repository..."
if [ -d "$APP_DIR/.git" ]; then
    echo "  Repo already exists, pulling latest..."
    sudo -u "$APP_USER" git -C "$APP_DIR" pull origin main
else
    sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
fi

echo "==> [4/8] Setting up Python virtual environment..."
sudo -u "$APP_USER" python${PYTHON_VERSION} -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install --no-cache-dir \
    -r "$APP_DIR/backend/requirements.txt"

echo "==> [5/8] Setting up environment variables..."
if [ ! -f "$APP_DIR/.env" ]; then
    echo "  IMPORTANT: Creating .env from example."
    echo "  You MUST edit $APP_DIR/.env with your real secrets before starting the service!"
    cp "$APP_DIR/.env.example" "$APP_DIR/.env"
    # Set correct permissions — only the app user can read secrets
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"

    # Auto-set ENVIRONMENT to production in the .env
    sed -i 's/^ENVIRONMENT=.*/ENVIRONMENT=production/' "$APP_DIR/.env" 2>/dev/null || \
        echo "ENVIRONMENT=production" >> "$APP_DIR/.env"
else
    echo "  .env already exists, skipping."
fi

echo "==> [6/8] Installing systemd service..."
cp "$APP_DIR/deploy/gtelepath.service" /etc/systemd/system/gtelepath.service
# Update paths in service file to match installation
sed -i "s|/opt/gtelepath|$APP_DIR|g" /etc/systemd/system/gtelepath.service
systemctl daemon-reload
systemctl enable gtelepath

echo "==> [7/8] Configuring nginx..."
# Replace placeholder domain in nginx config
cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/gtelepath
sed -i "s/YOUR_DOMAIN_OR_IP/$DOMAIN/g" /etc/nginx/sites-available/gtelepath

# Enable the site
ln -sf /etc/nginx/sites-available/gtelepath /etc/nginx/sites-enabled/gtelepath
rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
nginx -t
systemctl restart nginx
systemctl enable nginx

echo "==> [8/8] Configuring firewall..."
# Allow SSH (always keep this!), HTTP, HTTPS
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
# Deny direct access to the Python port from outside (nginx is the only entry)
ufw deny 8000/tcp

echo ""
echo "======================================================="
echo "  Bootstrap complete!"
echo "======================================================="
echo ""
echo "  NEXT STEPS:"
echo ""
echo "  1. Edit your secrets:"
echo "     sudo nano $APP_DIR/.env"
echo "     (Fill in SUPABASE_*, JWT_SECRET_KEY, GOOGLE_*, ELEVENLABS_*)"
echo ""
echo "  2. Set CORS_ORIGINS to include your frontend URL:"
echo "     CORS_ORIGINS=https://your-frontend.vercel.app"
echo ""
if [[ "$DOMAIN" != *"."* ]] || [[ "$DOMAIN" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "  3. You are using an IP address ($DOMAIN)."
    echo "     SSL/HTTPS requires a domain name. Skip Let's Encrypt for now."
    echo "     The nginx config currently serves HTTP only on port 80."
    echo "     To add SSL later: set up a domain, then run:"
    echo "     sudo certbot --nginx -d your-domain.com"
else
    echo "  3. Obtain SSL certificate (requires DNS to point to this VM):"
    echo "     sudo certbot --nginx -d $DOMAIN"
    echo "     Certbot will auto-renew via cron."
fi
echo ""
echo "  4. Start the backend service:"
echo "     sudo systemctl start gtelepath"
echo "     sudo systemctl status gtelepath"
echo ""
echo "  5. View logs:"
echo "     sudo journalctl -u gtelepath -f"
echo ""
