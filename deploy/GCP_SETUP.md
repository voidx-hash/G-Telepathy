# G Telepathy — GCP VM Deployment Guide

This guide walks you through deploying the G Telepathy backend on a **Google Cloud Platform (GCP) VM instance** (Compute Engine).

## Architecture Overview

```
Internet
  │
  ▼
GCP VM (e2-small or larger)
  │
  ├── nginx (port 80/443) ← SSL termination, rate limiting
  │     │
  │     └── proxy_pass → uvicorn (port 8000, localhost only)
  │                         │
  │                         └── FastAPI + Socket.io app
  │
  └── systemd (gtelepath.service) ← keeps uvicorn alive
```

---

## Step 1 — Create a GCP VM Instance

### Via GCP Console
1. Go to **Compute Engine → VM Instances → Create Instance**
2. Configure:

| Setting | Recommended Value |
|---|---|
| Name | `gtelepath-vm` |
| Region | `us-central1` (or closest to users) |
| Machine type | `e2-small` (2 vCPU, 2 GB RAM) — upgrade if needed |
| Boot disk OS | **Debian 12** or **Ubuntu 22.04 LTS** |
| Boot disk size | 20 GB (SSD) |
| Firewall | ✅ Allow HTTP traffic, ✅ Allow HTTPS traffic |

3. Under **Networking → Network tags**, add: `http-server`, `https-server`

### Via gcloud CLI (faster)
```bash
gcloud compute instances create gtelepath-vm \
  --zone=us-central1-a \
  --machine-type=e2-small \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server \
  --metadata=enable-oslogin=TRUE
```

---

## Step 2 — Configure Firewall Rules

Make sure GCP allows ports 80 and 443 (these should be automatic with the `http-server`/`https-server` tags, but verify):

```bash
# Allow HTTP (for Let's Encrypt ACME challenge)
gcloud compute firewall-rules create allow-http \
  --allow tcp:80 \
  --target-tags http-server

# Allow HTTPS
gcloud compute firewall-rules create allow-https \
  --allow tcp:443 \
  --target-tags https-server
```

> **Note:** Port 8000 (uvicorn) should NOT be open to the internet. Nginx is the only public entry point.

---

## Step 3 — SSH Into the VM

```bash
gcloud compute ssh gtelepath-vm --zone=us-central1-a
```

---

## Step 4 — Run the Bootstrap Script

Copy `startup.sh` to the VM and run it:

```bash
# From your local machine (in the repo root):
gcloud compute scp deploy/startup.sh gtelepath-vm:~/ --zone=us-central1-a

# On the VM:
chmod +x ~/startup.sh
sudo ~/startup.sh
```

> The script installs Python 3.11, nginx, certbot, clones your repo, creates a service user, configures systemd and firewall.

---

## Step 5 — Configure Secrets

**This is the most critical step.** Edit the `.env` file on the VM:

```bash
sudo nano /opt/gtelepath/.env
```

Fill in **all** of these:

```env
ENVIRONMENT=production
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET_KEY=<generate: python3 -c "import secrets; print(secrets.token_hex(32))">
GOOGLE_TRANSLATE_API_KEY=your-key
ELEVENLABS_API_KEY=your-key
CORS_ORIGINS=https://your-frontend.vercel.app
```

The file is automatically `chmod 600` (only readable by the `gtelepath` service user).

---

## Step 6 — Set Up Google Cloud Auth (Recommended)

Instead of API keys, use a **Service Account** for Google APIs on the VM:

```bash
# On your local machine:
# 1. Create a service account in GCP Console → IAM → Service Accounts
# 2. Grant it: Cloud Translation API Editor, Cloud Speech-to-Text Editor
# 3. Download the JSON key file
# 4. Upload to the VM:
gcloud compute scp service-account.json gtelepath-vm:/opt/gtelepath/ --zone=us-central1-a

# On the VM:
sudo chown gtelepath:gtelepath /opt/gtelepath/service-account.json
sudo chmod 600 /opt/gtelepath/service-account.json
```

Then in `/opt/gtelepath/.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=/opt/gtelepath/service-account.json
```

---

## Step 7 — Set Up SSL with Let's Encrypt (if you have a domain)

Point your domain's DNS `A` record to the VM's external IP, then:

```bash
sudo certbot --nginx -d your-domain.com
```

Certbot will automatically edit the nginx config and set up auto-renewal.

> **No domain?** Use the VM's external IP address. Nginx will serve HTTP only (no HTTPS without a domain). Update `nginx.conf` to remove the HTTPS block and serve on port 80 only.

---

## Step 8 — Start the Backend

```bash
sudo systemctl start gtelepath
sudo systemctl status gtelepath

# Should show: Active: active (running)
```

Test the health endpoint:
```bash
curl http://localhost:8000/health
# → {"status":"healthy"}
```

---

## Step 9 — Update Your Frontend

In your **Vercel** project settings, update environment variables:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `https://your-domain.com` or `http://VM_IP` |

---

## Ongoing Deployments

After pushing code changes to GitHub, deploy to the VM with:

```bash
# From your local machine:
./deploy/deploy.sh gtelepath-vm us-central1-a
```

This pulls latest code, updates dependencies, and restarts the service.

---

## Useful Commands on the VM

```bash
# View live logs
sudo journalctl -u gtelepath -f

# Restart the backend
sudo systemctl restart gtelepath

# Restart nginx
sudo systemctl restart nginx

# View nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check service status
sudo systemctl status gtelepath nginx
```

---

## VM Sizing Guide

| Users | Machine Type | RAM | vCPU | Estimated Cost/mo |
|---|---|---|---|---|
| 0–100 concurrent | `e2-small` | 2 GB | 2 | ~$14 |
| 100–500 concurrent | `e2-medium` | 4 GB | 2 | ~$27 |
| 500–2000 concurrent | `e2-standard-2` | 8 GB | 2 | ~$48 |
| 2000+ concurrent | `e2-standard-4` | 16 GB | 4 | ~$96 |

> For a beta launch with a small team, `e2-small` is sufficient.

---

## Security Checklist

- [x] Backend port 8000 not exposed to internet (ufw deny)
- [x] nginx is the only public entry point
- [x] HTTPS enforced (if domain is configured)
- [x] HSTS header set (1 year)
- [x] Rate limiting on auth routes (10 req/min)
- [x] Rate limiting on API routes (30 req/min)
- [x] Service runs as non-root user `gtelepath`
- [x] `.env` file is `chmod 600`
- [x] `ENVIRONMENT=production` blocks weak JWT secrets
- [x] `/docs` and `/redoc` endpoints disabled in production
- [x] Server version headers stripped
