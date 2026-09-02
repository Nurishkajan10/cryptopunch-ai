import asyncio
import logging
import os

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from anthropic import Anthropic

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CHECK_INTERVAL_SECONDS = 300  # как часто проверять новости (5 минут)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
claude = Anthropic(api_key=ANTHROPIC_API_KEY)

# id пользователей, подписанных на алерты
subscribers: set[int] = set()

# id новостей, которые уже обработали, чтобы не слать дубли
seen_news_ids: set[int] = set()


async def fetch_crypto_news() -> list[dict]:
    """Тянем последние новости с CryptoPanic (бесплатный публичный API)."""
    url = "https://cryptopanic.com/api/v1/posts/?public=true&kind=news"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                logging.warning(f"CryptoPanic request failed: {resp.status}")
                return []
            data = await resp.json()
            return data.get("results", [])


def score_news_with_claude(title: str) -> dict:
    """Просим Claude оценить значимость новости и дать краткое объяснение."""
    prompt = f"""You are a crypto market analyst. Rate how significant this news
headline is for crypto markets on a scale of 1-10, and give a one-sentence
explanation of why. Respond ONLY in this exact format, nothing else:

SCORE: <number>
REASON: <one sentence>

Headline: "{title}"
"""
    response = claude.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text.strip()

    score, reason = 0, ""
    for line in text.splitlines():
        if line.startswith("SCORE:"):
            try:
                score = int(line.replace("SCORE:", "").strip())
            except ValueError:
                score = 0
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    return {"score": score, "reason": reason}


async def news_monitor_loop():
    """Фоновая задача: раз в N секунд проверяем новости и шлём алерты."""
    while True:
        try:
            news_items = await fetch_crypto_news()
            for item in news_items:
                news_id = item.get("id")
                title = item.get("title", "")
                source_url = item.get("url", "")

                if news_id in seen_news_ids or not title:
                    continue
                seen_news_ids.add(news_id)

                analysis = score_news_with_claude(title)

                # шлём только значимые новости, чтобы не спамить
                if analysis["score"] >= 6:
                    alert_text = (
                        f"🚨 Significance: {analysis['score']}/10\n\n"
                        f"{title}\n\n"
                        f"💡 {analysis['reason']}\n\n"
                        f"🔗 {source_url}"
                    )
                    for user_id in subscribers:
                        try:
                            await bot.send_message(user_id, alert_text)
                        except Exception as e:
                            logging.warning(f"Failed to send to {user_id}: {e}")

        except Exception as e:
            logging.error(f"Error in news monitor loop: {e}")

        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


@dp.message(CommandStart())
async def cmd_start(message: Message):
    subscribers.add(message.from_user.id)
    await message.answer(
        "👋 Welcome to CryptoPunch AI!\n\n"
        "I'll monitor crypto news and alert you when something significant "
        "happens, with an AI-generated explanation of why it matters.\n\n"
        "You're now subscribed. Use /stop to unsubscribe."
    )


@dp.message(Command("stop"))
async def cmd_stop(message: Message):
    subscribers.discard(message.from_user.id)
    await message.answer("You've been unsubscribed. Use /start to subscribe again.")


async def main():
    asyncio.create_task(news_monitor_loop())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
