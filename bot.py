import logging
import asyncio
from telegram import Bot
import httpx

# Ваши данные (вставьте свои значения)
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
CHECK_INTERVAL = 60  # Проверка каждую минуту

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ИСПРАВЛЕННЫЕ API-эндпоинты
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

async def get_price(exchange):
    """Получаем цену с биржи с правильными параметрами"""
    try:
        config = EXCHANGES[exchange]
        async with httpx.AsyncClient() as client:
            # Правильное формирование запроса
            response = await client.get(
                config["url"],
                params=config["params"],  # Параметры передаются отдельно
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            data = response.json()
            
            # Извлекаем цену по указанному пути
            price = data
            for key in config["price_key"]:
                price = price[key]
                
            return float(price)
    except Exception as e:
        logger.error(f"Ошибка {exchange}: {str(e)}")
        return None

async def check_spread():
    """Проверяем спред между биржами"""
    prices = {}
    for exchange in EXCHANGES:
        price = await get_price(exchange)
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
            await bot.send_message(chat_id=CHAT_ID, text=msg)
            logger.info(f"Отправлено уведомление о спреде {spread_percent:.2f}%")

async def main():
    """Основная функция"""
    logger.info("🟢 Бот запущен в режиме long-polling")
    while True:
        try:
            await check_spread()
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🔴 Бот остановлен")
    except Exception as e:
        logger.error(f"⛔ Критическая ошибка: {str(e)}")
