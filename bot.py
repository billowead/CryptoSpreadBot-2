import os
import logging
import asyncio
from telegram import Bot
import httpx
from aiohttp import web

# Ваши данные (замените на актуальные)
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"  # Ваш токен
CHAT_ID = 593059857  # Ваш chat_id
PORT = 10000  # Порт для Render
CHECK_INTERVAL = 60  # Проверка каждую минуту

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка данных
if not TELEGRAM_TOKEN or not CHAT_ID:
    logger.error("ОШИБКА: Не заданы TELEGRAM_TOKEN или CHAT_ID!")
    exit(1)

# Конфигурация API (только стабильные биржи)
API_CONFIG = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},
        "price_key": ["data", "price"],
        "trade_url": "https://www.kucoin.com/trade/BTC-USDT"
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["price"],
        "trade_url": "https://www.mexc.com/exchange/BTC_USDT"
    }
}

bot = Bot(token=TELEGRAM_TOKEN)

async def health_check(request):
    return web.Response(text="Bot is working!")

async def get_price(exchange: str):
    try:
        config = API_CONFIG[exchange]
        async with httpx.AsyncClient() as client:
            r = await client.get(
                config["url"],
                params=config["params"],
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
        logger.error(f"{exchange} error: {e}")
        return None

async def check_spread():
    prices = {}
    for exchange in API_CONFIG:
        price = await get_price(exchange)
        if price:
            prices[exchange] = price
            if len(prices) >= 2:
                break
    
    if len(prices) >= 2:
        exchanges = list(prices.keys())
        spread = abs(prices[exchanges[0]] - prices[exchanges[1]])
        spread_percent = (spread / ((prices[exchanges[0]] + prices[exchanges[1]]) / 2)) * 100

        if spread_percent >= 2:
            msg = (
                f"🚨 Спред BTC/USDT > 2% ({spread_percent:.2f}%)\n"
                f"📊 {exchanges[0]}: {prices[exchanges[0]]:.2f}\n"
                f"📊 {exchanges[1]}: {prices[exchanges[1]]:.2f}\n"
                f"🔗 {API_CONFIG[exchanges[0]]['trade_url']}"
            )
            await bot.send_message(chat_id=CHAT_ID, text=msg)

async def background_tasks(app):
    app['task'] = asyncio.create_task(run_scheduler())

async def run_scheduler():
    while True:
        await check_spread()
        await asyncio.sleep(CHECK_INTERVAL)

async def start_app():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    app.on_startup.append(background_tasks)
    return app

if __name__ == "__main__":
    logger.info("Запуск бота с вашими данными...")
    try:
        app = asyncio.run(start_app())
        web.run_app(app, host='0.0.0.0', port=PORT)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
