#!/bin/bash
set -e

echo "🚀 Starting full affiliate bot deployment..."

# --- Clean Node.js/npm/pm2 install to avoid dependency hell ---
echo "🛠️ Cleaning existing Node.js and npm installations..."
sudo apt-get remove --purge -y nodejs npm || true
sudo apt-get autoremove -y
sudo rm -rf /usr/lib/node_modules /usr/local/lib/node_modules || true

echo "🌐 Installing Node.js 18.x and npm via NodeSource..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "📦 Verifying Node.js and npm installation..."
node -v
npm -v

echo "⚙️ Installing pm2 globally..."
sudo npm install -g pm2

echo "✅ pm2 version:"
pm2 --version

# --- Setup Python environment ---
echo "🐍 Setting up Python 3.8+ virtual environment..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip build-essential libffi-dev libssl-dev

# Create venv if missing
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate

echo "📥 Upgrading pip and installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# --- Environment variables ---
echo "⚙️ Writing .env file..."
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

echo "✅ .env file created."

# --- PM2 start script ---
echo "🔄 Starting affiliate bot with pm2..."

# Kill existing pm2 process with this name if exists
pm2 delete affiliate-bot || true

pm2 start main.py --interpreter ./venv/bin/python --name affiliate-bot

echo "✅ Bot started under pm2 process manager."

# --- Fail-safe notes ---
echo "⚠️ Note: This deploy script assumes main.py is your bot entry point."
echo "⚠️ Make sure main.py uses updated OpenAI API calls (>=1.0.0) and CapCut for video generation."
echo "⚠️ Ensure your bot handles asyncio loops correctly. If you face asyncio.run errors, consider applying fixes in your Python code to close existing loops before running."
echo "⚠️ Check logs anytime with 'pm2 logs affiliate-bot'."

echo "🎉 Deployment complete. Your affiliate bot is now running 24/7."
