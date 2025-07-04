import os
import asyncio
import random
from aiohttp import web
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

pairs = [
    ('BTC', 'USDT'),
    ('ETH', 'USDT'),
    ('DOGE', 'USDT'),
    ('LTC', 'USDT'),
    ('BTC', 'DOGE'),
    ('ETH', 'DOGE'),
    ('LTC', 'BTC'),
    ('DOGE', 'ETH')
]

async def check_spreads():
    await asyncio.sleep(5)
    while True:
        for base, quote in pairs:
            spread = random.uniform(0, 5)
            if spread > 2:
                msg = f"💹 Спред между {base}/{quote} = {spread:.2f}%"
                try:
                    await bot.send_message(chat_id=CHAT_ID, text=msg)
                except Exception as e:
                    print("Ошибка отправки:", e)
        await asyncio.sleep(60)

async def handle(request):
    return web.Response(text="Бот работает!")

app = web.Application()
app.add_routes([web.get('/', handle)])

async def on_startup(app):
    app['task'] = asyncio.create_task(check_spreads())

app.on_startup.append(on_startup)

if __name__ == '__main__':
    web.run_app(app, port=10000)
