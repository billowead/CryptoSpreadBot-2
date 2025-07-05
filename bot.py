import os
import logging
import asyncio
from telegram import Bot
import httpx

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
PORT = int(os.environ.get('PORT', 10000))
WEBHOOK_URL = f"https://cryptospreadbot-2-2.onrender.com/{TOKEN}"

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация API
API_CONFIG = {
    "binance": {
        "url": "https://api.binance.com/api/v3/ticker/price",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["price"]
    },
    "bybit": {
        "url": "https://api.bybit.com/v2/public/tickers",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["result", 0, "last_price"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    }
}

bot = Bot(token=TOKEN)

async def get_price(exchange: str):
    try:
        config = API_CONFIG[exchange]
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["url"],
                params=config["params"],
                headers=config.get("headers", {})
            )
            response.raise_for_status()
            data = response.json()
            
            # Достаем цену по указанному пути
            price = data
            for key in config["price_key"]:
                price = price[key]
            return float(price)
            
    except Exception as e:
        logger.error(f"Ошибка при запросе к {exchange}: {e}")
        return None

async def check_spread():
    prices = {}
    for exchange in API_CONFIG:
        price = await get_price(exchange)
        if price is not None:
            prices[exchange] = price
    
    if len(prices) >= 2:
        exchanges = list(prices.keys())
        spread = abs(prices[exchanges[0]] - prices[exchanges[1]])
        spread_percent = (spread / ((prices[exchanges[0]] + prices[exchanges[1]]) / 2)) * 100

        if spread_percent >= 2:
            msg = (
                f"💰 Спред BTC/USDT: {spread:.2f} USDT ({spread_percent:.2f}%)\n"
                f"📊 {exchanges[0]}: {prices[exchanges[0]]}\n"
                f"📊 {exchanges[1]}: {prices[exchanges[1]]}\n\n"
                f"🔗 Binance: https://www.binance.com/en/trade/BTC_USDT\n"
                f"🔗 Bybit: https://www.bybit.com/en/trade/spot/BTC/USDT"
            )
            await bot.send_message(chat_id=CHAT_ID, text=msg)
            logger.info(f"Спред обнаружен: {spread_percent:.2f}%")

async def run_scheduler():
    while True:
        try:
            await check_spread()
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(10)

async def main():
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("✅ Webhook установлен")
    
    scheduler_task = asyncio.create_task(run_scheduler())
    
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        scheduler_task.cancel()
        await scheduler_task

if __name__ == "__main__":
    asyncio.run(main())
