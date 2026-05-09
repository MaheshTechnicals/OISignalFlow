# ⚡ OISignalFlow — Deployment Instructions

Complete guide to deploy your scanner on DigitalOcean and your dashboard on Netlify.

**Your Repo:** https://github.com/MaheshTechnicals/OISignalFlow
**Your VM:**   167.71.224.25 (Ubuntu)

---

## Architecture — How Everything Connects

```
┌──────────────────────────────────────────────────────────────────┐
│  DigitalOcean VM — 167.71.224.25                                 │
│                                                                  │
│  ┌──────────────────────────────────┐                            │
│  │  OISignalFlow.py  (systemd)      │                            │
│  │  Scans 209 FNO stocks every 5min │                            │
│  │  Sends Telegram alerts           │                            │
│  │  Writes  ──▶  config.json        │                            │
│  └──────────────────────────────────┘                            │
│                        │                                         │
│                        ▼                                         │
│  ┌──────────────────────────────────┐                            │
│  │  cors_server.py  (systemd)       │◀── fetch every 2s ──┐     │
│  │  Serves config.json on port 8080 │                      │     │
│  │  Adds CORS headers               │                      │     │
│  └──────────────────────────────────┘                      │     │
│                                                            │     │
└────────────────────────────────────────────────────────────┼─────┘
                                                             │
  Netlify — https://your-site.netlify.app                   │
  ┌──────────────────────────────────┐                       │
  │  index.html   (dashboard UI)     ├───────────────────────┘
  │  styles.css   (dark theme)       │
  │  script.js    (polling logic)    │
  │  dashboard-config.js (API URL)   │
  └──────────────────────────────────┘
```

| Component | Runs On | Role |
|-----------|---------|------|
| `OISignalFlow.py` | DigitalOcean VM | Scans NSE FNO stocks, writes `config.json`, sends Telegram |
| `cors_server.py` | DigitalOcean VM :8080 | Exposes `config.json` with CORS headers over HTTP |
| `index.html` + `styles.css` + `script.js` | Netlify | Live monitoring dashboard UI |
| `dashboard-config.js` | Netlify | Auto-detects local vs Netlify, sets correct API URL |

---

## PART 1 — DigitalOcean VM Deployment

### Step 1 — SSH Into Your VM

```bash
ssh ubuntu@167.71.224.25
```

---

### Step 2 — Clone Your GitHub Repository

```bash
cd ~
git clone https://github.com/MaheshTechnicals/OISignalFlow.git
cd OISignalFlow
```

> If you already cloned it, pull the latest code:
> ```bash
> cd ~/OISignalFlow
> git pull origin main
> ```

---

### Step 3 — Run the Automated Setup Script

One command installs everything: Python, venv, packages, systemd services, and opens the firewall.

```bash
bash deploy/setup.sh
```

**What it does automatically:**
- Installs `python3`, `pip`, `venv`, `git`, `ufw` via apt
- Creates Python virtual environment at `~/OISignalFlow/venv/`
- Installs all packages from `requirements.txt`
- Installs and enables `oiflow.service` and `cors_server.service` as systemd services
- Opens port `8080` in UFW firewall

---

### Step 4 — Create Your `.env` File

The scanner needs your Telegram credentials. This file is in `.gitignore` — it is **never committed**.

```bash
cp ~/OISignalFlow/.env.example ~/OISignalFlow/.env
nano ~/OISignalFlow/.env
```

Set these values:

```ini
# ── Telegram (required) ────────────────────────────────────
# Get from: https://t.me/BotFather  →  /newbot
TELEGRAM_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefgh

# Get from: https://t.me/userinfobot  →  /start
TELEGRAM_CHAT_ID=987654321

# ── Scan Parameters ────────────────────────────────────────
OI_CHANGE_MIN=2.0
PRICE_CHANGE_MIN=0.3
VOLUME_MULT=1.5
SCAN_INTERVAL=5

# ── Output ─────────────────────────────────────────────────
OUTPUT_FILE=OISignalFlow_Results.xlsx
LOG_LEVEL=INFO

# Set False on server — no desktop environment
ENABLE_DESKTOP_NOTIFICATIONS=False
```

Save: `Ctrl+X` → `Y` → `Enter`

---

### Step 5 — Start Both Services

```bash
# Start the CORS server first (so the dashboard can connect immediately)
sudo systemctl start cors_server

# Start the OISignalFlow scanner
sudo systemctl start oiflow
```

---

### Step 6 — Verify Services are Running

```bash
sudo systemctl status oiflow cors_server
```

**Expected output:**
```
● oiflow.service — OISignalFlow — NSE FNO OI Scanner
     Active: active (running) since ...

● cors_server.service — OISignalFlow — CORS Config Server (port 8080)
     Active: active (running) since ...
```

Both must show `active (running)`. ✅

---

### Step 7 — Test the CORS Server (from your local machine)

Open your browser or run from your local terminal:

```bash
curl http://167.71.224.25:8080/config.json
```

**Expected:** JSON response like:
```json
{
  "status": { "system_status": "ready", "market_open": false, ... },
  "configuration": { "fno_stocks_total": 209, ... },
  "statistics": { "total_scans": 0, ... },
  "recent_signals": [],
  "all_scan_results": []
}
```

If you see this JSON — the VM is working. ✅

> **If connection refused on port 8080:**
> DigitalOcean has TWO firewalls. You need to open port 8080 in BOTH:
> 1. **UFW (on VM):** `sudo ufw allow 8080/tcp` ← setup.sh does this
> 2. **Cloud Firewall (DigitalOcean panel):** Login → Networking → Firewalls → Add TCP 8080 inbound rule

---

### VM Management Commands

```bash
# ── Logs ────────────────────────────────────────────────────────
sudo journalctl -u oiflow -f          # Scanner logs (live)
sudo journalctl -u cors_server -f     # CORS server logs
sudo journalctl -u oiflow -n 50       # Last 50 scanner log lines

# ── Service Control ─────────────────────────────────────────────
sudo systemctl restart oiflow         # Restart scanner
sudo systemctl restart cors_server    # Restart CORS server
sudo systemctl stop oiflow            # Stop scanner
sudo systemctl stop cors_server       # Stop CORS server

# ── Update Code from GitHub ─────────────────────────────────────
cd ~/OISignalFlow
git pull origin main
sudo systemctl restart oiflow cors_server

# ── Firewall ────────────────────────────────────────────────────
sudo ufw status                        # Check firewall rules
sudo ufw allow 8080/tcp               # Manually open port 8080

# ── Check .env ──────────────────────────────────────────────────
cat ~/OISignalFlow/.env               # View (ensure token is set)
```

---

## PART 2 — Netlify Deployment

### Step 1 — Push New Files to GitHub (from your local machine)

The new deployment files need to be pushed before Netlify can use them:

```bash
# On your LOCAL machine (not the VM)
cd /path/to/OISignalFlow

# Check what's new
git status

# Add all new deployment files
git add dashboard-config.js netlify.toml deploy/ INSTRUCTION.md

# Also add updated files
git add index.html script.js styles.css README.md SETUP.md QUICK_START.md

git commit -m "Add dashboard-config, netlify.toml, deploy scripts"
git push origin main
```

**Verify `dashboard-config.js` has the correct VM IP before pushing:**
```javascript
var VM_IP   = '167.71.224.25';   // ← your DigitalOcean VM IP
var VM_PORT = '8080';
```

---

### Step 2 — Deploy to Netlify

1. Go to **https://app.netlify.com**
2. Click **"Add new site"** → **"Import an existing project"**
3. Click **"Deploy with GitHub"**
4. Authorise Netlify to access your GitHub
5. Search for **OISignalFlow** and select it

---

### Step 3 — Configure Build Settings

On the build configuration screen:

| Field | Value |
|-------|-------|
| **Owner** | Your Netlify account |
| **Branch to deploy** | `main` |
| **Base directory** | *(leave empty)* |
| **Build command** | *(leave empty — no build needed)* |
| **Publish directory** | *(leave empty or type `.`)* |

> The repo root contains `index.html` directly — Netlify auto-detects this as a static site.

Click **"Deploy site"**

---

### Step 4 — Wait for Deployment (~30 seconds)

You'll get a live URL like:
```
https://random-name-abc123.netlify.app
```

---

### Step 5 — Verify the Dashboard

1. Open the Netlify URL in your browser
2. Press `F12` → **Console** tab
3. Look for:
   ```
   ⚡ OISignalFlow Dashboard
   API Mode: REMOTE VM
   Fetching: http://167.71.224.25:8080/config.json
   ```
4. The connection indicator in the header should show 🟢 **Live**
5. KPI cards will populate after the first scan cycle

---

### Step 6 — (Optional) Rename Your Site

1. In Netlify → **Site configuration** → **Site details**
2. Click **"Change site name"**
3. Set something like `oisignalflow-dashboard`
4. Your URL becomes: `https://oisignalflow-dashboard.netlify.app`

---

### Step 7 — Auto-Deploy is Already Active

Every `git push origin main` automatically triggers Netlify to redeploy. No manual action needed.

```bash
# Make any change, then:
git add .
git commit -m "Update dashboard"
git push origin main
# Netlify auto-redeploys in ~30 seconds
```

---

## PART 3 — Full Verification Checklist

Run through this after completing both deployments:

```
VM CHECKS:
  □  SSH works:               ssh ubuntu@167.71.224.25
  □  oiflow running:          sudo systemctl status oiflow
  □  cors_server running:     sudo systemctl status cors_server
  □  Port 8080 open (UFW):    sudo ufw status | grep 8080
  □  Port 8080 open (DO):     DigitalOcean panel → Networking → Firewalls
  □  config.json reachable:   curl http://167.71.224.25:8080/config.json
  □  Scanner logs flowing:    sudo journalctl -u oiflow -f
  □  .env is set:             grep TELEGRAM_TOKEN ~/OISignalFlow/.env

NETLIFY CHECKS:
  □  Site deploys:            https://your-site.netlify.app loads
  □  API mode = REMOTE VM:    Browser console shows "API Mode: REMOTE VM"
  □  Connection = Live:       Green dot in top-right header
  □  Data appearing:          KPIs show numbers after scanner runs once
  □  No CORS errors:          Browser console has no "CORS" errors
  □  Auto-deploy works:       Push a commit, verify Netlify redeploys
```

---

## PART 4 — Troubleshooting

### ❌ Scanner not starting (`oiflow` service fails)

```bash
# See full error
sudo journalctl -u oiflow -n 50 --no-pager

# Common: .env missing or has placeholder token
cat ~/OISignalFlow/.env

# Common: packages not installed
~/OISignalFlow/venv/bin/pip list | grep nselib

# Fix missing packages
~/OISignalFlow/venv/bin/pip install -r ~/OISignalFlow/requirements.txt
sudo systemctl restart oiflow
```

---

### ❌ Port 8080 not reachable from outside

```bash
# Step 1: Fix UFW on VM
sudo ufw allow 8080/tcp
sudo ufw status

# Step 2: Fix DigitalOcean Cloud Firewall (web panel)
# → Login to digitalocean.com
# → Networking → Firewalls
# → Find your Droplet's firewall
# → Add Inbound Rule: Type=Custom, Protocol=TCP, Port=8080, Sources=All IPv4
```

Test from your local machine:
```bash
curl -v http://167.71.224.25:8080/config.json
```

---

### ❌ Netlify dashboard stuck at "Connecting..."

```bash
# 1. Verify the VM CORS server is running
sudo systemctl status cors_server

# 2. Test from browser DevTools console:
fetch('http://167.71.224.25:8080/config.json').then(r => r.json()).then(console.log)
```

- **JSON returned** → VM is fine. Check `dashboard-config.js` has VM_IP = `'167.71.224.25'`
- **CORS error** → `cors_server` not running on VM
- **net::ERR_CONNECTION_REFUSED** → port 8080 is blocked (see above)

---

### ❌ Dashboard shows "API Mode: LOCAL" on Netlify

Your `dashboard-config.js` has a wrong IP or old code. Fix:

```bash
# Local machine — edit the file
nano /path/to/OISignalFlow/dashboard-config.js
# Set: var VM_IP = '167.71.224.25';
# Set: var VM_PORT = '8080';

git add dashboard-config.js
git commit -m "Fix VM IP in dashboard-config"
git push origin main
# Netlify redeploys automatically
```

---

### ❌ No CE signals in dashboard (market hours only)

- Scanner only runs **9:15 AM – 3:30 PM IST, Monday–Friday**
- Outside these hours, the scanner waits — this is expected
- To test with lower thresholds, edit `.env` on VM:
  ```bash
  nano ~/OISignalFlow/.env
  # Set: OI_CHANGE_MIN=0.5
  # Set: VOLUME_MULT=1.0
  sudo systemctl restart oiflow
  ```

---

### ❌ After pulling new code, services use old version

```bash
cd ~/OISignalFlow
git pull origin main
sudo systemctl daemon-reload        # reload if .service files changed
sudo systemctl restart oiflow cors_server
sudo systemctl status oiflow cors_server
```

---

## PART 5 — File Reference

```
OISignalFlow/          (repo root = https://github.com/MaheshTechnicals/OISignalFlow)
│
├── OISignalFlow.py          ← Scanner — runs on DigitalOcean VM via systemd
├── index.html               ← Dashboard HTML — hosted on Netlify
├── styles.css               ← Dashboard CSS — hosted on Netlify
├── script.js                ← Dashboard JS — hosted on Netlify
├── dashboard-config.js      ← API URL config (auto-detects local vs Netlify)  ← NEW
├── netlify.toml             ← Netlify build settings                           ← NEW
├── config.json              ← Data bridge written by scanner (VM only)
├── requirements.txt         ← Python dependencies
├── .env                     ← Secrets — NEVER commit, VM only
├── .env.example             ← Template for .env
├── .gitignore               ← Excludes .env, *.xlsx, venv/
├── README.md                ← Project documentation
├── SETUP.md                 ← Local setup guide
├── QUICK_START.md           ← Dashboard quick start
├── INSTRUCTION.md           ← This file — deployment guide
│
└── deploy/                                                                     ← NEW
    ├── setup.sh             ← One-command VM setup (run once after clone)
    ├── oiflow.service       ← systemd unit: OISignalFlow.py scanner
    ├── cors_server.service  ← systemd unit: CORS HTTP server
    └── cors_server.py       ← Python CORS server — serves config.json on :8080
```

---

## PART 6 — Quick Reference Card

```
════════════════════════════════════════════════════════════
  REPO      https://github.com/MaheshTechnicals/OISignalFlow
  VM        167.71.224.25
  API       http://167.71.224.25:8080/config.json
  DASHBOARD https://YOUR-SITE.netlify.app
════════════════════════════════════════════════════════════

START SERVICES (VM):
  sudo systemctl start cors_server oiflow

STOP SERVICES (VM):
  sudo systemctl stop oiflow cors_server

UPDATE CODE ON VM:
  cd ~/OISignalFlow
  git pull origin main
  sudo systemctl restart oiflow cors_server

WATCH LIVE SCANNER LOGS:
  sudo journalctl -u oiflow -f

WATCH CORS SERVER LOGS:
  sudo journalctl -u cors_server -f

TEST CORS ENDPOINT:
  curl http://167.71.224.25:8080/config.json

PUSH FRONTEND UPDATE (auto-deploys to Netlify):
  git add . && git commit -m "update" && git push origin main

CHECK SERVICE HEALTH:
  sudo systemctl status oiflow cors_server
════════════════════════════════════════════════════════════
```
