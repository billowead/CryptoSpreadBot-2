import os
import logging
import asyncio
from telegram import Bot
import httpx

# Конфигурация
BOT_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"  # Ваш токен
CHAT_ID = 593059857  # Ваш chat_id
CHECK_INTERVAL = 60  # Проверка каждые 60 секунд

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Проверка данных
if not BOT_TOKEN or not CHAT_ID:
    logger.error("ОШИБКА: Не заданы BOT_TOKEN или CHAT_ID!")
    exit(1)

# Конфигурация API (исправленные URL)
API_CONFIG = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},  # Параметры отдельно от URL
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

bot = Bot(token=BOT_TOKEN)

async def get_price(exchange: str):
    """Получаем цену с биржи"""
    try:
        config = API_CONFIG[exchange]
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config["url"],
                params=config["params"],  # Параметры передаются правильно
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # Безопасное извлечение цены
            price = data
            for key in config["price_key"]:
                if isinstance(price, (list, tuple)) and isinstance(key, int):
                    if len(price) <= key:
                        raise ValueError(f"Неверный индекс {key}")
                price = price[key]
                
            return float(price)
            
    except Exception as e:
        logger.error(f"Ошибка при запросе к {exchange}: {str(e)}")
        return None

async def check_spread():
    """Проверяем спред между биржами"""
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

async def main():
    """Основная функция"""
    logger.info("Бот запущен в режиме long-polling")
    while True:
        try:
            await check_spread()
            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {str(e)}")
            await asyncio.sleep(10)  # Пауза при ошибке

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
