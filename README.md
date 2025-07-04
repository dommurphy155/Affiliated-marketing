# 💸 The Boys — AI-Powered Affiliate Profit Bot

**The Boys** is a fully automated affiliate marketing ecosystem built for passive income generation. Once deployed, it scrapes high-converting digital products, creates content, posts across major social platforms, and tracks earnings — all hands-free.

---

## 🚀 Features

- 🔥 Automatically scrapes viral, high-payout digital products from:
  - ClickBank
  - Gumroad (Marketplace only)
  - Payhip (Marketplace only)
- 📲 Auto-posts AI-generated content to:
  - TikTok
  - Instagram
  - YouTube
  - Facebook
  - Twitter (X)
- 🤖 Integrates OpenAI to generate content and captions
- 🧠 Self-learning: Bot adapts product selection every 5 days
- 📈 Smart offer engine to prioritize high-profit viral offers
- 🔐 Content-lock redirection funnel (CPA-style)
- 🧵 Telegram control panel:
  - `/status` — View current bot state
  - `/earnings` — See today's profit
  - `/start` — Launch the bot
  - `/stop` — Kill switch
- 🔁 Auto-refresh system every 5 days to rotate offers
- 📦 Zero inventory. 100% digital delivery.
- 💸 No upfront budget needed. Runs on free-tier Oracle Cloud.

---

## ✅ Setup Requirements

### 1. Environment Variables (`.env` or GitHub Secrets)

- **Telegram Bot**
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`

- **OpenAI**
  - `OPENAI_API_KEY`

- **Affiliate**
  - `CLICKBANK_NICKNAME`
  - `GUMROAD_API_KEY` *(optional — scraper used if blank)*
  - `PAYHIP_API_KEY` *(optional — scraper used if blank)*

- **Social Media Credentials (GitHub Secrets ONLY)**
  - `TWITTER_EMAIL`, `TWITTER_PASSWORD`
  - `INSTAGRAM_EMAIL`, `INSTAGRAM_PASSWORD`
  - `TIKTOK_EMAIL`, `TIKTOK_PASSWORD`
  - `YOUTUBE_EMAIL`, `YOUTUBE_PASSWORD`

---

## 🛠️ Installation (Oracle Cloud / Linux VPS)

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Install dependencies
pip install -r requirements.txt

# Run the bot
python3 main.py
