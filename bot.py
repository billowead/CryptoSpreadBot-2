import os
import logging
import asyncio
from telegram import Bot
import httpx
from aiohttp import web

# Ваши переменные (используем ТОЧНО ТЕ ЖЕ названия)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # Ваш токен
CHAT_ID = os.getenv("CHAT_ID")                # Ваш chat_id
PORT = 10000  # Фиксированный порт для Render
CHECK_INTERVAL = 60

# Проверка переменных
if not TELEGRAM_TOKEN:
    logging.error("❌ ОШИБКА: Не задана переменная TELEGRAM_TOKEN!")
    exit(1)

if not CHAT_ID:
    logging.error("❌ ОШИБКА: Не задана переменная CHAT_ID!")
    exit(1)

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфиг API
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},
        "price_key": ["data", "price"]
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["price"]
    }
}

bot = Bot(token=TELEGRAM_TOKEN)

async def health_check(request):
    return web.Response(text="Bot is working!")

async def get_price(exchange):
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                EXCHANGES[exchange]["url"],
                params=EXCHANGES[exchange]["params"],
                timeout=10
            )
            data = r.json()
            price = data
            for key in EXCHANGES[exchange]["price_key"]:
                price = price[key]
            return float(price)
    except Exception as e:
        logger.error(f"Ошибка {exchange}: {str(e)}")
        return None

async def check_spread():
    prices = {}
    for exchange in EXCHANGES:
        price = await get_price(exchange)
        if price:
            prices[exchange] = price
            if len(prices) >= 2:
                break
    
    if len(prices) >= 2:
        exch1, exch2 = list(prices.keys())
        price1, price2 = prices.values()
        spread = abs(price1 - price2)
        spread_percent = (spread / ((price1 + price2)/2)) * 100

        if spread_percent >= 2:
            msg = f"🚀 Спред {spread_percent:.2f}%\n{exch1}: {price1:.2f}\n{exch2}: {price2:.2f}"
            await bot.send_message(chat_id=CHAT_ID, text=msg)

async def background_task(app):
    while True:
        await check_spread()
        await asyncio.sleep(CHECK_INTERVAL)

async def start_app():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    app.on_startup.append(lambda a: asyncio.create_task(background_task(a)))
    return app

if __name__ == "__main__":
    logger.info(f"🔄 Запуск бота на порту {PORT}...")
    try:
        app = asyncio.run(start_app())
        web.run_app(app, host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"⛔ Ошибка: {str(e)}")
