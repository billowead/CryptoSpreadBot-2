import logging
import asyncio
from telegram import Bot
import httpx
from aiohttp import web

# ===== ВАШИ ДАННЫЕ =====
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
PORT = 10000  # Фиксированный порт для Render
# =======================

# Настройки
CHECK_INTERVAL = 60
LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Исправленные API-эндпоинты
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},  # Параметры отдельно!
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
    return web.Response(text="Bot is working")

async def get_price(exchange):
    try:
        config = EXCHANGES[exchange]
        async with httpx.AsyncClient() as client:
            r = await client.get(
                config["url"],
                params=config["params"],  # Параметры передаются правильно
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            r.raise_for_status()
            data = r.json()
            price = data
            for key in config["price_key"]:
                price = price[key]
            return float(price)
    except Exception as e:
        logger.error(f"{exchange} error: {str(e)}")
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
        spread = abs(prices[exch1] - prices[exch2])
        spread_percent = (spread / ((prices[exch1] + prices[exch2])/2)) * 100

        if spread_percent >= 2:
            msg = (
                f"🚨 Спред {spread_percent:.2f}%\n"
                f"{exch1}: {prices[exch1]:.2f} USD\n"
                f"{exch2}: {prices[exch2]:.2f} USD\n"
                f"Разница: {spread:.2f} USD"
            )
            await bot.send_message(chat_id=CHAT_ID, text=msg)

async def background_task(app):
    while True:
        await check_spread()
        await asyncio.sleep(CHECK_INTERVAL)

async def start_app():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    app.on_startup.append(lambda app: asyncio.create_task(background_task(app)))
    return app

if __name__ == "__main__":
    try:
        logger.info(f"🚀 Starting bot on port {PORT}")
        app = asyncio.run(start_app())
        web.run_app(app, host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
