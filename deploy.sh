#!/bin/bash

# ✅ Affiliate Marketing Bot Auto Deployment Script
# Works on Ubuntu 20.04+ with Python 3.8+
# Created by Dom’s request – Full deployment, no placeholders

set -e

# === Variables ===
APP_NAME="affiliate-bot"
APP_DIR="$HOME/affiliate-bot"
VENV_DIR="$APP_DIR/venv"
REPO_URL="https://github.com/dommurphy155/Affiliated-marketing.git"
PYTHON_VERSION="3.8"

# === Logging Helpers ===
log() { echo -e "\033[1;32m[✔] $1\033[0m"; }
err() { echo -e "\033[1;31m[✖] $1\033[0m"; exit 1; }

# === Pre-check ===
[ "$EUID" -eq 0 ] && err "Don't run as root. Use a normal user."

log "Starting deployment of $APP_NAME..."

# === Update system & install dependencies ===
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    python3 python3-pip python3-venv python3-dev \
    build-essential git curl wget nodejs npm sqlite3 \
    libsqlite3-dev libnss3 libatk-bridge2.0-0 libxss1 \
    libgconf-2-4 libxcomposite1 libxdamage1 libxrandr2 \
    libgtk-3-0 libasound2 libxkbcommon0 libgbm1 ca-certificates

# === Install PM2 ===
sudo npm install -g pm2

# === Clone Repo ===
rm -rf "$APP_DIR"
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"

# === Create .env with Dom’s credentials ===
cat > .env <<EOF
OPENAI_API_KEY=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
TELEGRAM_BOT_TOKEN=7970729024:AAFIFzpY8-m2OLY07chzcYWJevgXXcTbZUs
TELEGRAM_CHAT_ID=7108900627
CLICKBANK_NICKNAME=digiprof25
TIKTOK_EMAIL=dommurphy155@gmail.com
TIKTOK_PASSWORD=Lorenzo1!
CAPCUT_EMAIL=dommurphy155@gmail.com
CAPCUT_PASSWORD=Lorenzo1!
EOF

chmod 600 .env

# === Python Environment ===
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# === Requirements ===
cat > requirements.txt <<EOF
python-telegram-bot==20.7
python-dotenv==1.0.0
playwright==1.40.0
openai==1.14.3
aiohttp==3.9.1
EOF

pip install -r requirements.txt
python -m playwright install

# === AsyncIO Failsafe Fix (if needed) ===
cat > run_safe.py <<'EOF'
import asyncio
from main import AffiliateBot

def run_bot():
    try:
        asyncio.run(AffiliateBot().run())
    except RuntimeError as e:
        if "asyncio.run()" in str(e):
            loop = asyncio.get_event_loop()
            loop.run_until_complete(AffiliateBot().run())

if __name__ == "__main__":
    run_bot()
EOF

# === PM2 Config ===
cat > ecosystem.config.js <<EOF
module.exports = {
  apps: [{
    name: "$APP_NAME",
    script: "run_safe.py",
    interpreter: "$VENV_DIR/bin/python",
    cwd: "$APP_DIR",
    autorestart: true,
    watch: false,
    max_memory_restart: "512M",
    env: {
      NODE_ENV: "production"
    }
  }]
}
EOF

# === PM2 Startup ===
pm2 stop $APP_NAME || true
pm2 delete $APP_NAME || true
pm2 start ecosystem.config.js
pm2 save
pm2 startup systemd -u $USER --hp $HOME

log "Deployment complete!"
log "Use 'pm2 logs $APP_NAME' to monitor."
