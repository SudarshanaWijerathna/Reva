# Oracle Cloud Setup Guide — Reva Backend

This guide walks you through deploying the Reva backend on Oracle Cloud Always Free
from zero to a live HTTPS endpoint that your Vercel frontend can call.

**Total estimated time:** 45–60 minutes  
**Cost:** $0 forever (Oracle Always Free)

---

## What You Get

| Resource | Spec | Cost |
|---|---|---|
| ARM A1 VM | 4 OCPUs, 24 GB RAM | Free |
| Block Storage | 200 GB | Free |
| PostgreSQL | On VM via Docker | Free |
| Redis | On VM via Docker | Free |
| HTTPS | Cloudflare Tunnel | Free |

---

## Prerequisites (do these before starting)

- [ ] A credit/debit card (Oracle requires it for identity verification — you are **not** charged)
- [ ] Your project `.env` values handy (Gemini API key, NewsAPI key, MongoDB URL, etc.)
- [ ] Git installed on your local machine

---

## Step 1 — Create an Oracle Cloud Account

1. Go to [cloud.oracle.com](https://cloud.oracle.com) → click **Start for free**
2. Fill in your details. When asked for a **Home Region**, choose **ap-mumbai-1** (Mumbai) — closest to Sri Lanka and usually has Ampere A1 availability
3. Enter your card details (verification only, not charged)
4. Complete email verification
5. Log into the [OCI Console](https://cloud.oracle.com)

> ⚠️ **If you see "Out of Capacity" for the ARM VM in Step 3**, try again later or switch to a different region (ap-singapore-1 is a good alternative).

---

## Step 2 — Provision the Always Free ARM VM

1. In the OCI Console, go to **Compute → Instances → Create Instance**
2. Fill in the form:

| Field | Value |
|---|---|
| **Name** | `reva-backend` |
| **Image** | Canonical Ubuntu 22.04 |
| **Shape** | Click "Change Shape" → Ampere → **VM.Standard.A1.Flex** |
| **OCPUs** | `4` |
| **Memory** | `24 GB` |
| **Boot Volume** | `100 GB` (free up to 200 GB total) |

3. Under **SSH Keys** → select **Generate a key pair for me** → click **Save Private Key** to download your `.key` file. Keep this safe!
4. Click **Create**
5. Wait ~2 minutes for the instance to reach **Running** state
6. Note the **Public IP Address** shown (you will need this throughout)

---

## Step 3 — Open Firewall Ports

Oracle VMs have two firewall layers. You need to open both.

### 3a — OCI Security List (cloud firewall)

1. Go to **Networking → Virtual Cloud Networks → your VCN → Security Lists → Default Security List**
2. Click **Add Ingress Rules** and add these three rules:

| Source CIDR | Protocol | Port | Purpose |
|---|---|---|---|
| `0.0.0.0/0` | TCP | `22` | SSH (already exists) |
| `0.0.0.0/0` | TCP | `80` | HTTP (Nginx / Cloudflare) |
| `0.0.0.0/0` | TCP | `8000` | FastAPI (direct access during setup) |

### 3b — Ubuntu firewall (inside the VM)

You will run this in Step 5 after SSHing in:
```bash
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 4 — SSH Into the VM

On your local machine (replace `<your-oracle-ip>` and path to your key file):

```bash
# Linux / macOS
ssh -i ~/Downloads/reva-backend.key ubuntu@<your-oracle-ip>

# Windows (PowerShell)
ssh -i C:\Users\YourName\Downloads\reva-backend.key ubuntu@<your-oracle-ip>
```

If you get a permissions error on the key file:
```bash
# Linux / macOS only
chmod 400 ~/Downloads/reva-backend.key
```

---

## Step 5 — Install Docker & Docker Compose

Run all of these on the Oracle VM (paste one block at a time):

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Apply group without logging out
newgrp docker

# Verify Docker works
docker run hello-world

# Install Docker Compose plugin
sudo apt install -y docker-compose-plugin

# Verify
docker compose version
```

```bash
# Open VM-level firewall ports (from Step 3b)
sudo apt install -y iptables-persistent
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo netfilter-persistent save
```

---

## Step 6 — Clone the Repo & Configure Environment

```bash
# Clone the repository
git clone https://github.com/SudarshanaWijerathna/Reva.git
cd Reva

# Create your .env from the Oracle template
cp .env.oracle.example .env

# Open the editor and fill in your secrets
nano .env
```

**Fill in these values in `.env`** (everything with `<...>`):

| Variable | Where to get it |
|---|---|
| `POSTGRES_PASSWORD` | Make up a strong password, e.g. `R3va@2025!` |
| `SECRET_KEY` | Run: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `NEWS_API` | [newsapi.org](https://newsapi.org) → free plan |
| `DB_LINK` | Your existing MongoDB connection string |
| `VITE_GOOGLE_CLIENT_ID` | Google Cloud Console → OAuth 2.0 → your web client ID |

Save and exit nano: **Ctrl+X → Y → Enter**

---

## Step 7 — Build & Start the Backend

```bash
# Build and start all containers in the background
docker compose up -d --build
```

The first build will take **10–20 minutes** (downloading TensorFlow, PyTorch, etc.).

```bash
# Watch the build / startup logs
docker compose logs -f backend

# Check all three containers are healthy
docker compose ps
```

You should see:
```
NAME             STATUS
reva_postgres    running (healthy)
reva_redis       running (healthy)
reva_backend     running (healthy)
```

```bash
# Quick smoke test
curl http://localhost:8000/health
# Expected: {"status":"ok"}
```

---

## Step 8 — Set Up Cloudflare Tunnel (Free HTTPS)

Your Vercel frontend is on HTTPS, so the backend **must** also be HTTPS.
Cloudflare Tunnel gives you a free `https://...trycloudflare.com` URL with zero domain purchase.

```bash
# Install cloudflared
curl -L --output cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb
sudo dpkg -i cloudflared.deb

# Create a temporary tunnel (gets a random URL — use this for testing first)
cloudflared tunnel --url http://localhost:8000
```

You will see output like:
```
Your quick Tunnel has been created! Visit it at:
https://some-random-words.trycloudflare.com
```

Test it:
```bash
curl https://some-random-words.trycloudflare.com/health
# Expected: {"status":"ok"}
```

> ⚠️ **Temporary tunnels reset on restart.** For a permanent URL (recommended), create a free Cloudflare account and a Named Tunnel — see Step 8b.

### Step 8b — Permanent Named Tunnel (Recommended)

```bash
# Log in to Cloudflare (opens a browser link — copy and open on your PC)
cloudflared tunnel login

# Create a named tunnel
cloudflared tunnel create reva-backend

# Note the Tunnel ID shown — save it, you need it below
# Create the tunnel config file
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: <your-tunnel-id>
credentials-file: /home/ubuntu/.cloudflared/<your-tunnel-id>.json

ingress:
  - service: http://localhost:8000
EOF

# Run as a background system service (survives VM reboots)
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared

# Check it is running
sudo systemctl status cloudflared
```

With a named tunnel your backend gets a stable URL like:
`https://reva-backend.<your-cloudflare-account>.cfargotunnel.com`

---

## Step 9 — Update Vercel Frontend Environment

1. Go to your [Vercel Dashboard](https://vercel.com) → **reva-front → Settings → Environment Variables**
2. Add or update:

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://your-cloudflare-tunnel-url` (no trailing slash) |

3. Click **Save** → go to **Deployments** → **Redeploy** the latest deployment

---

## Step 10 — Make Backend Auto-Start on VM Reboot

Docker Compose with `restart: unless-stopped` already handles container recovery.
To ensure Docker itself starts on boot:

```bash
sudo systemctl enable docker
```

**Test the full recovery:**
```bash
# Simulate a reboot
sudo reboot
```

Wait ~2 minutes, then SSH back in and check:
```bash
docker compose -f ~/Reva/docker-compose.yml ps
```

All three containers should be `running (healthy)`.

---

## Step 11 — Initialize Admin User (First Time Only)

```bash
cd ~/Reva
docker compose exec backend python init_admin.py
```

---

## Useful Commands

```bash
# View live backend logs
docker compose logs -f backend

# Restart just the backend (after code changes)
docker compose up -d --build backend

# Stop everything
docker compose down

# Stop and wipe all data (careful!)
docker compose down -v

# Enter the Postgres container
docker compose exec postgres psql -U reva_user -d reva

# Check Redis
docker compose exec redis redis-cli ping
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Cannot connect to Docker daemon` | Run `newgrp docker` or log out and back in |
| Backend container exits immediately | Run `docker compose logs backend` to see the error |
| `Port 8000 refused` | Check OCI Security List has port 8000 open AND run `sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT` |
| `Out of capacity` for ARM shape | Try a different OCI region, or retry after a few hours |
| Cloudflare tunnel disconnects | Check `sudo systemctl status cloudflared` and restart with `sudo systemctl restart cloudflared` |
| Frontend gets CORS error | Add the Cloudflare URL to `CORS_ORIGINS` in `.env` and run `docker compose up -d --build backend` |
