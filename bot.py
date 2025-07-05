import os
import logging
import asyncio
from telegram import Bot
import httpx

# Ваши данные (вставьте свои значения)
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"  # Ваш токен
CHAT_ID = "593059857"  # Ваш chat_id (в кавычках!)
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

# Простая конфигурация API
EXCHANGES = {
    "binance": {
        "url": "https://api.binance.com/api/v3/ticker/price",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["price"]
    },
    "bybit": {
        "url": "https://api.bybit.com/v2/public/tickers",
        "params": {"symbol": "BTCUSD"},
        "price_key": ["result", 0, "last_price"]
    }
}

bot = Bot(token=TELEGRAM_TOKEN)

async def get_price(exchange):
    try:
        config = EXCHANGES[exchange]
        async with httpx.AsyncClient() as client:
            r = await client.get(
                config["url"],
                params=config["params"],
                timeout=10
            )
            data = r.json()
            price = data
            for key in config["price_key"]:
                price = price[key]
            return float(price)
    except Exception as e:
        logger.error(f"Ошибка {exchange}: {str(e)}")
        return None

async def main():
    logger.info("Бот запущен!")
    while True:
        try:
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
                        f"{exch1}: {prices[exch1]:.2f}\n"
                        f"{exch2}: {prices[exch2]:.2f}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=msg)
            
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
