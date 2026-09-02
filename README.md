# CryptoPunch AI

AI-powered Telegram bot that monitors crypto news in real time, scores how
significant each story is using Claude, and alerts you only when something
actually matters — cutting through the noise.

Built for VoltHacks 2026.

## What it does

- Pulls the latest crypto news from CryptoPanic
- Sends each headline to Claude for a significance score (1-10) and a
  one-sentence explanation
- Alerts subscribed Telegram users when a story scores 6+
- Simple `/start` and `/stop` subscription commands

## Setup

1. Clone this repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Get a Telegram bot token from [@BotFather](https://t.me/BotFather).

3. Get an Anthropic API key from [console.anthropic.com](https://console.anthropic.com).

4. Set environment variables:
   ```bash
   export TELEGRAM_BOT_TOKEN="your-telegram-token"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

6. Open your bot in Telegram and send `/start`.

## Tech stack

Python, aiogram, Anthropic Claude API, CryptoPanic API

## Roadmap

- Personalized alerts based on a user's portfolio
- More news sources
- Alert history and accuracy tracking
