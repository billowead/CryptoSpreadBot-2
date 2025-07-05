import logging
import asyncio
from telegram import Bot
import httpx

# ===== ВСТАВЬТЕ СВОИ ДАННЫЕ =====
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
# ================================

# Настройки
CHECK_INTERVAL = 60
LOG_LEVEL = logging.INFO

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Используем API, которые работают на Render
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

class SpreadBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
        logger.info("Бот инициализирован")

    async def get_price(self, exchange):
        try:
            config = EXCHANGES[exchange]
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
            logger.error(f"{exchange} error: {str(e)}")
            return None

    async def check_spread(self):
        prices = {}
        for exchange in EXCHANGES:
            price = await self.get_price(exchange)
            if price is not None:
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
                await self.bot.send_message(chat_id=CHAT_ID, text=msg)
                logger.info(f"Спред обнаружен: {spread_percent:.2f}%")

    async def run(self):
        logger.info("Мониторинг запущен")
        while True:
            try:
                await self.check_spread()
                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Ошибка: {str(e)}")
                await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        bot = SpreadBot()
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {str(e)}")
