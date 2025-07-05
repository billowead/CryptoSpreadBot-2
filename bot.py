import os
import logging
import asyncio
from telegram import Bot
import httpx

# Конфигурация
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PORT = int(os.environ.get('PORT', 10000))  # Render использует порт 10000
CHECK_INTERVAL = 60

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Правильные конфигурации API
API_CONFIG = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},  # Параметры передаются отдельно
        "price_key": ["data", "price"],
        "trade_url": "https://www.kucoin.com/trade/BTC-USDT"
    },
    "huobi": {
        "url": "https://api.huobi.pro/market/detail/merged",
        "params": {"symbol": "btcusdt"},
        "price_key": ["tick", "close"],
        "trade_url": "https://www.huobi.com/en-us/exchange/btc_usdt"
    }
}

bot = Bot(token=TOKEN)

async def get_price(exchange: str):
    try:
        config = API_CONFIG[exchange]
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Правильное формирование запроса с параметрами
            response = await client.get(
                config["url"],
                params=config["params"],  # Параметры передаются правильно
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if response.status_code != 200:
                logger.warning(f"{exchange} status: {response.status_code}")
                return None
                
            data = response.json()
            price = data
            for key in config["price_key"]:
                price = price[key]
            return float(price)
            
    except Exception as e:
        logger.error(f"Error getting {exchange} price: {str(e)}")
        return None

async def check_spread():
    prices = {}
    for exchange in API_CONFIG:
        price = await get_price(exchange)
        if price is not None:
            prices[exchange] = price
            if len(prices) >= 2:
                break
    
    if len(prices) >= 2:
        exchanges = list(prices.keys())
        spread = abs(prices[exchanges[0]] - prices[exchanges[1]])
        spread_percent = (spread / ((prices[exchanges[0]] + prices[exchanges[1]]) / 2)) * 100

        if spread_percent >= 2:
            msg = (
                "🚨 Обнаружен спред BTC/USDT > 2%\n\n"
                f"📊 {exchanges[0]}: {prices[exchanges[0]]:.2f} USDT\n"
                f"📊 {exchanges[1]}: {prices[exchanges[1]]:.2f} USDT\n"
                f"💰 Разница: {spread:.2f} USDT ({spread_percent:.2f}%)\n\n"
                f"🔗 {exchanges[0]}: {API_CONFIG[exchanges[0]]['trade_url']}\n"
                f"🔗 {exchanges[1]}: {API_CONFIG[exchanges[1]]['trade_url']}"
            )
            try:
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                logger.info(f"Спред обнаружен: {spread_percent:.2f}%")
            except Exception as e:
                logger.error(f"Ошибка отправки: {str(e)}")

async def run_scheduler():
    while True:
        await check_spread()
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    logger.info(f"Бот запущен на порту {PORT}")
    # Добавляем искусственное ожидание порта для Render
    await asyncio.sleep(1)
    await run_scheduler()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
