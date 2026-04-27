# G Telepathy — Complete Deployment Guide

> **Beta** · End-to-end encrypted communication platform with AI voice cloning and real-time translation.

---

## Project Structure (Clean)

```
G-Telepathy/
├── backend/              ← FastAPI + Socket.io (Python)
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── routers/         (auth, chat, calls, rooms, translate)
│   ├── services/        (translation)
│   ├── sockets/         (chat, calls — Socket.io handlers)
│   └── tests/           (60 pytest tests)
├── frontend/             ← Next.js 14 (React/TypeScript)
│   ├── src/app/
│   ├── package.json
│   └── next.config.js
├── supabase/             ← DB schema (PostgreSQL via Supabase)
│   └── schema.sql
├── deploy/               ← All deployment files
│   ├── GCP_SETUP.md     (GCP-specific details)
│   ├── startup.sh       (VM bootstrap)
│   ├── deploy.sh        (push updates)
│   ├── nginx.conf       (reverse proxy)
│   └── gtelepath.service (systemd)
└── .env.example          ← Copy → .env and fill in secrets
```

---

## Architecture Decision: Where Does Everything Live?

```
┌─────────────────────────────────────────────────────────────┐
│                     RECOMMENDED SETUP                       │
│                                                             │
│  Frontend  →  Vercel (free, global CDN, zero config)        │
│  Backend   →  GCP VM e2-small (you control it)              │
│  Database  →  Supabase (managed PostgreSQL + Auth + storage) │
│                                                             │
│  Why this split?                                            │
│  • Frontend is static HTML/JS — Vercel/Netlify are free     │
│    and 10x faster than self-hosting for this.               │
│  • Backend needs WebSockets (Socket.io) — only a VM can     │
│    keep persistent connections. Vercel/serverless can't.    │
│  • Database on Supabase = managed backups, Row-Level         │
│    Security, Auth, and real-time subscriptions built in.    │
│    Running your own Postgres adds ops burden with no gain.  │
└─────────────────────────────────────────────────────────────┘
```

---

## Part 1 — Database (Supabase)

### Do NOT self-host the database. Use Supabase.

**Why:** Supabase gives you managed PostgreSQL + Auth + real-time + storage for free (up to 500MB).

### Setup
1. Go to [supabase.com](https://supabase.com) → **New Project**
2. Choose a region close to your GCP VM region (e.g. both `us-central`)
3. Copy your credentials:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_ANON_KEY`
   - **service_role key** → `SUPABASE_SERVICE_ROLE_KEY`
4. Run the schema in Supabase SQL Editor:
   ```sql
   -- Paste the contents of supabase/schema.sql here
   ```

---

## Part 2 — Backend on GCP VM

### Method A: Git Clone + Manual Setup (Recommended for first time)

#### 2A-1. Create the VM

```bash
# Install gcloud CLI first: https://cloud.google.com/sdk/docs/install
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID

gcloud compute instances create gtelepath-vm \
  --zone=us-central1-a \
  --machine-type=e2-small \
  --image-family=debian-12 \
  --image-project=debian-cloud \
  --boot-disk-size=20GB \
  --boot-disk-type=pd-ssd \
  --tags=http-server,https-server
```

#### 2A-2. SSH Into the VM

```bash
gcloud compute ssh gtelepath-vm --zone=us-central1-a
```

#### 2A-3. Install Dependencies on the VM

```bash
sudo apt-get update -y
sudo apt-get install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx git ufw
```

#### 2A-4. Clone Your Repository

```bash
# Option 1: HTTPS (works everywhere, ask for password if private)
git clone https://github.com/voidx-hash/G-Telepathy.git /opt/gtelepath

# Option 2: SSH (faster for private repos, requires SSH key setup)
# First add your VM's public key to GitHub:
ssh-keygen -t ed25519 -C "gtelepath-vm"
cat ~/.ssh/id_ed25519.pub   # copy this → GitHub Settings → SSH Keys
git clone git@github.com:voidx-hash/G-Telepathy.git /opt/gtelepath

# Option 3: GitHub Personal Access Token (best for private repos with CI)
git clone https://YOUR_PAT_TOKEN@github.com/voidx-hash/G-Telepathy.git /opt/gtelepath
```

#### 2A-5. Set Up Python Environment

```bash
cd /opt/gtelepath
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
```

#### 2A-6. Configure Secrets

```bash
cp .env.example .env
nano .env   # fill in all values — see .env.example for what's needed
chmod 600 .env
```

**Required values in `.env` for production:**
```env
ENVIRONMENT=production
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
JWT_SECRET_KEY=<run: python3 -c "import secrets; print(secrets.token_hex(32))">
GOOGLE_TRANSLATE_API_KEY=AIza...
ELEVENLABS_API_KEY=sk_...
CORS_ORIGINS=https://your-frontend.vercel.app
```

#### 2A-7. Test the Backend Manually

```bash
cd /opt/gtelepath/backend
source /opt/gtelepath/venv/bin/activate
uvicorn main:socket_app --host 0.0.0.0 --port 8000
# Open another terminal: curl http://VM_EXTERNAL_IP:8000/health
# Should return: {"status":"healthy"}
# Press Ctrl+C when done
```

#### 2A-8. Install as a System Service (Auto-start on reboot)

```bash
sudo cp /opt/gtelepath/deploy/gtelepath.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gtelepath
sudo systemctl start gtelepath
sudo systemctl status gtelepath   # check it's running
```

#### 2A-9. Configure Nginx

```bash
sudo cp /opt/gtelepath/deploy/nginx.conf /etc/nginx/sites-available/gtelepath

# Edit it: replace YOUR_DOMAIN_OR_IP with your actual VM IP or domain
sudo nano /etc/nginx/sites-available/gtelepath

sudo ln -s /etc/nginx/sites-available/gtelepath /etc/nginx/sites-enabled/gtelepath
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t        # test config — must say "syntax is ok"
sudo systemctl restart nginx
```

#### 2A-10. Open Firewall

```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp   # uvicorn should NEVER be public, only nginx
sudo ufw status
```

#### 2A-11. Get SSL Certificate (only if you have a domain)

```bash
# Point your domain DNS A record to VM's external IP first, then:
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

### Method B: Use the Automated Bootstrap Script (Fastest)

```bash
# From your LOCAL machine:
gcloud compute scp deploy/startup.sh gtelepath-vm:~/ --zone=us-central1-a
gcloud compute ssh gtelepath-vm --zone=us-central1-a -- "chmod +x ~/startup.sh && sudo ~/startup.sh"

# Then SSH in and fill secrets:
gcloud compute ssh gtelepath-vm --zone=us-central1-a
sudo nano /opt/gtelepath/.env
sudo systemctl start gtelepath
```

---

### Method C: Docker (If you prefer containers)

#### On the VM:

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Clone the repo
git clone https://github.com/voidx-hash/G-Telepathy.git
cd G-Telepathy/backend

# Build and run
docker build -t gtelepath-backend .
docker run -d \
  --name gtelepath \
  --env-file ../.env \
  -p 127.0.0.1:8000:8000 \
  --restart unless-stopped \
  gtelepath-backend

# Check it's working
docker logs -f gtelepath
curl http://localhost:8000/health
```

> **Note:** Even with Docker, you still need nginx in front of it for WebSocket support, SSL termination and rate limiting. The nginx config in `deploy/nginx.conf` works the same way.

---

### Pushing Code Updates to the VM

After any code change, just run from your local machine:

```bash
./deploy/deploy.sh gtelepath-vm us-central1-a
```

Or manually:

```bash
gcloud compute ssh gtelepath-vm --zone=us-central1-a -- \
  "cd /opt/gtelepath && git pull origin main && sudo systemctl restart gtelepath"
```

---

## Part 3 — Frontend on Vercel (Recommended)

Vercel gives you free global CDN hosting for Next.js with zero configuration needed.

### Method A: Vercel CLI (Fastest)

```bash
# On your LOCAL machine (not the VM):
npm install -g vercel
cd frontend
vercel login
vercel --prod
```

### Method B: Vercel Dashboard

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import from GitHub: `voidx-hash/G-Telepathy`
3. Set **Root Directory** to `frontend`
4. **Build Command:** `npm run build`
5. **Output Directory:** `.next`
6. Set environment variables:

| Key | Value |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | `https://your-vm-domain.com` or `http://VM_IP` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://your-project.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | your anon key |
| `NEXT_PUBLIC_APP_NAME` | `G Telepathy` |

7. Click **Deploy** → Done. Vercel gives you a URL like `g-telepathy.vercel.app`

### Method C: Frontend on the Same GCP VM

Only do this if you specifically don't want Vercel. Costs more (bigger VM) and loses CDN benefits.

```bash
# On the VM, after backend is running:
sudo apt-get install -y nodejs npm

cd /opt/gtelepath/frontend
npm install
npm run build   # builds the Next.js static output

# Run Next.js production server
npm start &     # runs on port 3000

# Add to nginx: proxy port 443 → frontend on 3000, /api/* → backend on 8000
```

Update `nginx.conf` to split traffic:

```nginx
# Frontend (Next.js)
location / {
    proxy_pass http://127.0.0.1:3000;
    ...
}

# Backend API
location /api/ {
    proxy_pass http://127.0.0.1:8000;
    ...
}

# Socket.io
location /socket.io/ {
    proxy_pass http://127.0.0.1:8000/socket.io/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    ...
}
```

> **Recommended VM size for co-hosting:** at least `e2-medium` (4 GB RAM).

---

## Part 4 — Connect Everything Together

Once all three parts are running, update your configs:

### 1. Update CORS in your VM's `.env`
```env
CORS_ORIGINS=https://your-app.vercel.app
```
Then restart: `sudo systemctl restart gtelepath`

### 2. Update Vercel env var
```
NEXT_PUBLIC_BACKEND_URL=https://your-domain.com
```
Redeploy Vercel.

### 3. Verify End-to-End

```bash
# 1. Backend health
curl https://your-domain.com/health

# 2. Auth endpoint
curl -X POST https://your-domain.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass1","display_name":"Tester"}'

# 3. Frontend
open https://your-app.vercel.app
```

---

## Useful Commands Reference

```bash
# --- On the GCP VM ---

# View live backend logs
sudo journalctl -u gtelepath -f

# Restart backend after config change
sudo systemctl restart gtelepath

# Check service status
sudo systemctl status gtelepath

# View nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Restart nginx
sudo systemctl restart nginx

# Pull latest code and restart
cd /opt/gtelepath && git pull origin main && sudo systemctl restart gtelepath

# Run backend tests on VM
cd /opt/gtelepath && source venv/bin/activate
cd backend && python -m pytest tests/ -v

# Get VM external IP
curl ifconfig.me

# --- From your local machine ---

# SSH into VM
gcloud compute ssh gtelepath-vm --zone=us-central1-a

# Deploy latest code
./deploy/deploy.sh gtelepath-vm us-central1-a

# Copy files to VM
gcloud compute scp local-file.txt gtelepath-vm:~/ --zone=us-central1-a
```

---

## VM Sizing Quick Reference

| Stage | Machine Type | RAM | Monthly Cost |
|---|---|---|---|
| Beta / testing | `e2-micro` | 1 GB | ~$7 |
| Small launch (≤100 users) | `e2-small` | 2 GB | ~$14 |
| Growing (≤500 users) | `e2-medium` | 4 GB | ~$27 |
| Scale (≤2000 users) | `e2-standard-2` | 8 GB | ~$48 |

> Start on `e2-small`. GCP lets you resize with zero reinstall:
> `gcloud compute instances set-machine-type gtelepath-vm --machine-type=e2-medium --zone=us-central1-a`

---

## Security Checklist Before Going Live

- [ ] `ENVIRONMENT=production` in `.env` on VM
- [ ] `.env` file is `chmod 600` (readable only by service user)
- [ ] Port 8000 NOT open to internet (`ufw deny 8000`)
- [ ] Port 22 (SSH) restricted to your IP if possible
- [ ] HTTPS enabled (certbot + valid domain)
- [ ] `JWT_SECRET_KEY` is a random 64-char hex string
- [ ] `CORS_ORIGINS` lists only your actual frontend URL(s)
- [ ] `/docs` and `/redoc` are disabled (auto-disabled when `ENVIRONMENT=production`)
- [ ] Supabase Row Level Security (RLS) enabled on all tables
- [ ] Service account JSON key is `chmod 600`
