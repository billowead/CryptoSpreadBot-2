import os
import asyncio
import random
from telegram import Bot
from aiohttp import web

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

# Примеры бирж (можно заменить на реальные ссылки позже)
EXCHANGES = {
    "binance": "https://www.binance.com/en/trade/{}_{}",
    "bybit": "https://www.bybit.com/trade/spot/{}-{}"
}

# Валютные пары для отслеживания
PAIRS = [
    ("BTC", "USDT"),
    ("ETH", "USDT"),
    ("DOGE", "USDT"),
    ("LTC", "USDT"),
    ("BTC", "DOGE"),
    ("ETH", "DOGE"),
    ("LTC", "BTC"),
    ("DOGE", "ETH")
]

# Проверка спреда (заглушка, позже подключим API)
async def check_spread(base, quote):
    spread = random.uniform(0, 5)
    return spread

# Основной цикл
async def main_loop():
    while True:
        for base, quote in PAIRS:
            spread = await check_spread(base, quote)
            if spread > 2:
                message = (
                    f"📊 Спред между {base}/{quote} = {spread:.2f}%\n\n"
                    f"🔗 Binance: {EXCHANGES['binance'].format(base, quote)}\n"
                    f"🔗 Bybit: {EXCHANGES['bybit'].format(base, quote)}"
                )
                try:
                    await bot.send_message(chat_id=CHAT_ID, text=message)
                except Exception as e:
                    print(f"Ошибка отправки: {e}")
        await asyncio.sleep(60)

# HTTP сервер для Render (чтобы не ругался на порты)
async def handle(request):
    return web.Response(text="CryptoSpreadBot работает")

def run():
    loop = asyncio.get_event_loop()
    loop.create_task(main_loop())

    app = web.Application()
    app.router.add_get("/", handle)
    web.run_app(app, port=10000)

if __name__ == "__main__":
    run()
