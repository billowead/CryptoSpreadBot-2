import logging
import asyncio
from telegram import Bot
import httpx

# Ваши данные (вставьте свои значения)
BOT_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
CHECK_INTERVAL = 60  # Проверка каждые 60 секунд

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Упрощенная конфигурация API
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "symbol": "BTC-USDT",
        "price_key": ["data", "price"]
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "symbol": "BTCUSDT",
        "price_key": ["price"]
    }
}

bot = Bot(token=BOT_TOKEN)

async def fetch_price(exchange):
    """Получение цены с биржи"""
    try:
        url = EXCHANGES[exchange]["url"]
        params = {"symbol": EXCHANGES[exchange]["symbol"]}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params=params,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Извлекаем цену по указанному пути
            price = data
            for key in EXCHANGES[exchange]["price_key"]:
                price = price[key]
                
            return float(price)
            
    except Exception as e:
        logger.error(f"Ошибка при запросе к {exchange}: {str(e)}")
        return None

async def monitor_spread():
    """Мониторинг спреда между биржами"""
    while True:
        try:
            prices = {}
            for exchange in EXCHANGES:
                price = await fetch_price(exchange)
                if price is not None:
                    prices[exchange] = price
                    if len(prices) >= 2:
                        break
            
            if len(prices) >= 2:
                exchange1, exchange2 = list(prices.keys())
                price1, price2 = prices.values()
                
                spread = abs(price1 - price2)
                spread_percent = (spread / ((price1 + price2) / 2)) * 100

                if spread_percent >= 2:
                    message = (
                        f"🚀 *Спред обнаружен!* \n\n"
                        f"• *{exchange1}*: {price1:.2f} USD\n"
                        f"• *{exchange2}*: {price2:.2f} USD\n"
                        f"💎 *Разница*: {spread:.2f} USD ({spread_percent:.2f}%)"
                    )
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="Markdown"
                    )
                    logger.info(f"Спред {spread_percent:.2f}% отправлен")
            
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {str(e)}")
            await asyncio.sleep(10)

async def main():
    logger.info("🔔 Бот для мониторинга спреда запущен")
    await monitor_spread()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {str(e)}")
