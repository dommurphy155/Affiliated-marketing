#!/bin/bash

# Affiliate Marketing Bot Deployment Script (100% Final Version)
# Compatible with Ubuntu 20.04+ and Python 3.8+

set -e

APP_NAME="affiliate-bot"
REPO_URL="https://github.com/dommurphy155/Affiliated-marketing.git"
APP_DIR="$HOME/affiliate-bot"
VENV_DIR="$APP_DIR/venv"
LOG_FILE="$APP_DIR/deployment.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
    exit 1
}

log "🚀 Starting Deployment of $APP_NAME"

if [[ $EUID -eq 0 ]]; then error "Do NOT run as root. Use a regular user account."; fi

log "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

log "🔧 Installing dependencies..."
sudo apt install -y python3 python3-venv python3-pip git curl nodejs npm build-essential     libnss3 libxss1 libasound2 libatk-bridge2.0-0 libxcomposite1 libxdamage1 libxrandr2     libgbm1 libxkbcommon0 libgtk-3-0 libgconf-2-4 fonts-liberation sqlite3

log "🧪 Checking Python version..."
PY_VER=$(python3 -V | cut -d " " -f 2)
[[ $(echo "$PY_VER >= 3.8" | bc) -eq 1 ]] || error "Python 3.8+ required"

log "📂 Cloning repo if not present..."
[ ! -d "$APP_DIR" ] && git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR" || error "Failed to cd into $APP_DIR"

log "🐍 Setting up virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

log "⬆️ Upgrading pip..."
pip install --upgrade pip

log "📦 Installing Python dependencies..."
cat > requirements.txt <<EOF
python-telegram-bot==20.7
python-dotenv==1.0.0
playwright==1.40.0
openai==0.28.1
aiohttp==3.9.1
EOF

pip install -r requirements.txt
python -m playwright install
python -m playwright install-deps

log "📄 Creating .env template if not found..."
[ ! -f ".env" ] && cat > .env <<EOF
OPENAI_API_KEY=sk-xxx
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx
CLICKBANK_NICKNAME=digiprof25
TIKTOK_EMAIL=dommurphy155@outlook.com
TIKTOK_PASSWORD=Lorenzo1!
EOF

log "🛠️ Creating PM2 config..."
npm install -g pm2
cat > ecosystem.config.js <<EOF
module.exports = {
  apps: [{
    name: "affiliate-bot",
    script: "main.py",
    interpreter: "./venv/bin/python",
    autorestart: true,
    watch: false,
    max_memory_restart: "1G",
    env: {
      NODE_ENV: "production",
      PYTHONUNBUFFERED: "1"
    }
  }]
};
EOF

log "🔧 Creating systemd fallback service..."
sudo tee /etc/systemd/system/affiliate-bot.service > /dev/null <<EOF
[Unit]
Description=Affiliate Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/python $APP_DIR/main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable affiliate-bot.service

log "✅ Starting bot with PM2..."
pm2 start ecosystem.config.js
pm2 save
pm2 startup systemd -u $USER --hp $HOME

log "🎉 Deployment complete. Bot is now live."
