import logging
import asyncio
from telegram import Bot
import httpx
from aiohttp import web  # Добавляем простой HTTP-сервер

# Ваши данные
BOT_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
PORT = 10000  # Фиксированный порт для Render
CHECK_INTERVAL = 60

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация API (исправленные URL)
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},  # Параметры отдельно
        "price_key": ["data", "price"]
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["price"]
    }
}

bot = Bot(token=BOT_TOKEN)

async def health_check(request):
    """Endpoint для проверки работоспособности"""
    return web.Response(text="Bot is running")

async def fetch_price(exchange):
    """Получаем цену с биржи"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                EXCHANGES[exchange]["url"],
                params=EXCHANGES[exchange]["params"],
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            price = data
            for key in EXCHANGES[exchange]["price_key"]:
                price = price[key]
                
            return float(price)
    except Exception as e:
        logger.error(f"Ошибка {exchange}: {str(e)}")
        return None

async def check_spread():
    """Проверяем спред между биржами"""
    prices = {}
    for exchange in EXCHANGES:
        price = await fetch_price(exchange)
        if price:
            prices[exchange] = price
            if len(prices) >= 2:
                break
    
    if len(prices) >= 2:
        exchange1, exchange2 = prices.keys()
        price1, price2 = prices.values()
        
        spread = abs(price1 - price2)
        spread_percent = (spread / ((price1 + price2) / 2)) * 100

        if spread_percent >= 2:
            msg = (
                f"🚀 *Спред {spread_percent:.2f}%*\n\n"
                f"• {exchange1}: {price1:.2f}\n"
                f"• {exchange2}: {price2:.2f}\n"
                f"💎 Разница: {spread:.2f} USD"
            )
            await bot.send_message(
                chat_id=CHAT_ID,
                text=msg,
                parse_mode="Markdown"
            )

async def background_task(app):
    """Фоновая задача проверки спреда"""
    while True:
        await check_spread()
        await asyncio.sleep(CHECK_INTERVAL)

async def start_app():
    """Создание и запуск приложения"""
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
