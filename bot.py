import os
import random
import asyncio
from aiohttp import web
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# Список пар валют
pairs = [
    ("BTC", "USDT"),
    ("ETH", "USDT"),
    ("DOGE", "USDT"),
    ("LTC", "USDT"),
    ("BTC", "DOGE"),
    ("ETH", "DOGE"),
    ("LTC", "BTC"),
    ("DOGE", "ETH")
]

# Биржи
exchanges = ["Binance", "Bybit"]

# Пример функции для получения спреда
async def check_spread(pair):
    await asyncio.sleep(0.1)
    return random.uniform(0, 5), random.choice(exchanges), random.choice(exchanges)

# Основной цикл
async def main_loop():
    while True:
        for base, quote in pairs:
            spread, ex1, ex2 = await check_spread((base, quote))
            if spread > 2:
                url1 = f"https://www.{ex1.lower()}.com"
                url2 = f"https://www.{ex2.lower()}.com"
                message = (
                    f"💹 Спред между {base}/{quote} = {spread:.2f}%\n"
                    f"📈 {ex1}: {url1}\n"
                    f"📉 {ex2}: {url2}"
                )
                await bot.send_message(chat_id=CHAT_ID, text=message)
        await asyncio.sleep(60)

# Обработчик для Render (порт)
async def handle(request):
    return web.Response(text="Bot is running!")

# Запуск
def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(main_loop())

    app = web.Application()
    app.router.add_get("/", handle)
    web.run_app(app, port=10000)

if __name__ == "__main__":
    run()
