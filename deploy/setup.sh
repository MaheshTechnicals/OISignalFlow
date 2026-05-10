#!/usr/bin/env bash
# ============================================================
# OISignalFlow — deploy/setup.sh
# One-command setup script for Ubuntu DigitalOcean VM
#
# Run as the ubuntu user (NOT as root):
#   bash deploy/setup.sh
#
# What it does:
#   1. Updates apt and installs Python, pip, git
#   2. Creates and activates a Python venv
#   3. Installs all Python requirements
#   4. Copies systemd service files and enables both services
#   5. Opens port 8080 in UFW firewall
#   6. Prints next steps (create your .env)
# ============================================================

set -euo pipefail

# ── Colours ─────────────────────────────────────────────────
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'
BOLD='\033[1m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

# ── Guards ───────────────────────────────────────────────────
[[ "$(id -u)" -eq 0 ]] && error "Do NOT run as root. Run as the 'ubuntu' user."

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
info "Project root: $PROJECT_DIR"

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║  OISignalFlow — VM Setup Script          ║${RESET}"
echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════╝${RESET}"
echo ""

# ── Step 1: System packages ──────────────────────────────────
info "Step 1/6 — Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv git curl ufw
success "System packages installed"

# ── Step 2: Python virtual environment ──────────────────────
info "Step 2/6 — Creating Python virtual environment..."
cd "$PROJECT_DIR"

# Always recreate venv — prevents stale/broken state from previous runs
if [ -d "venv" ]; then
    warn "Removing old venv to ensure clean install..."
    rm -rf venv
fi
python3 -m venv venv
success "virtualenv created at $PROJECT_DIR/venv"

# ── Step 3: Install Python requirements ─────────────────────
info "Step 3/6 — Installing Python requirements..."

# 1. Upgrade pip to latest (old pip can't find Python 3.12 wheels)
"$PROJECT_DIR/venv/bin/pip" install --quiet --upgrade pip

# 2. setuptools + wheel MUST come first on Python 3.12+
#    (pkg_resources lives in setuptools — not included in 3.12 venvs by default)
"$PROJECT_DIR/venv/bin/pip" install --quiet --upgrade setuptools wheel

# 3. Install all project requirements
"$PROJECT_DIR/venv/bin/pip" install --quiet -r "$PROJECT_DIR/requirements.txt"
# NOTE: plyer installs fine on headless servers.
# Desktop notifications are automatically disabled
# via ENABLE_DESKTOP_NOTIFICATIONS=False in your .env
# No action needed — this is expected behaviour.
success "Python packages installed"

# ── Step 4: systemd service files ───────────────────────────
info "Step 4/6 — Installing systemd services..."

# Patch WorkingDirectory and ExecStart with actual project path
DEPLOY_DIR="$PROJECT_DIR/deploy"
ACTUAL_USER="$(whoami)"

# oiflow.service
sed \
  -e "s|/home/ubuntu/OISignalFlow|$PROJECT_DIR|g" \
  -e "s|User=ubuntu|User=$ACTUAL_USER|g" \
  -e "s|Group=ubuntu|Group=$ACTUAL_USER|g" \
  "$DEPLOY_DIR/oiflow.service" | sudo tee /etc/systemd/system/oiflow.service > /dev/null

# cors_server.service
sed \
  -e "s|/home/ubuntu/OISignalFlow|$PROJECT_DIR|g" \
  -e "s|User=ubuntu|User=$ACTUAL_USER|g" \
  -e "s|Group=ubuntu|Group=$ACTUAL_USER|g" \
  "$DEPLOY_DIR/cors_server.service" | sudo tee /etc/systemd/system/cors_server.service > /dev/null

sudo systemctl daemon-reload
sudo systemctl enable oiflow cors_server
success "systemd services installed and enabled"

# ── Step 5: Firewall ─────────────────────────────────────────
info "Step 5/6 — Configuring UFW firewall..."

# Enable UFW if not active, preserving SSH
sudo ufw allow OpenSSH     > /dev/null 2>&1 || true
sudo ufw allow 8080/tcp    > /dev/null 2>&1   # CORS server for dashboard
sudo ufw --force enable    > /dev/null 2>&1 || true
success "Port 8080 opened (UFW active)"

# ── Step 6: .env check ──────────────────────────────────────
info "Step 6/6 — Checking .env configuration..."

if [ -f "$PROJECT_DIR/.env" ]; then
    success ".env file found"
    # Quick credential check
    if grep -q "YOUR_BOT_TOKEN_HERE" "$PROJECT_DIR/.env"; then
        warn ".env exists but TELEGRAM_TOKEN is still the placeholder — update it!"
    else
        success "TELEGRAM_TOKEN appears to be set"
    fi
else
    warn ".env file NOT found — you must create it before starting the scanner!"
    echo ""
    echo -e "  Run: ${CYAN}cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env${RESET}"
    echo -e "  Then edit .env and add your TELEGRAM_TOKEN and TELEGRAM_CHAT_ID"
fi

# ── Done ─────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════════${RESET}"
echo -e "${BOLD}${GREEN}  Setup complete!${RESET}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════════${RESET}"
echo ""
echo -e "  ${BOLD}Next steps:${RESET}"
echo ""
echo -e "  1. ${CYAN}Create your .env:${RESET}"
echo -e "     cp $PROJECT_DIR/.env.example $PROJECT_DIR/.env"
echo -e "     nano $PROJECT_DIR/.env"
echo ""
echo -e "  2. ${CYAN}Start services:${RESET}"
echo -e "     sudo systemctl start cors_server"
echo -e "     sudo systemctl start oiflow"
echo ""
echo -e "  3. ${CYAN}Check status:${RESET}"
echo -e "     sudo systemctl status oiflow cors_server"
echo ""
echo -e "  4. ${CYAN}Watch logs:${RESET}"
echo -e "     sudo journalctl -u oiflow -f"
echo ""
echo -e "  5. ${CYAN}Test CORS server:${RESET}"
echo -e "     curl http://localhost:8080/config.json"
echo ""
