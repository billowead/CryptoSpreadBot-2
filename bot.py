import os
import logging
import asyncio
from telegram import Bot
import httpx

# Конфигурация
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
PORT = int(os.environ.get('PORT', 10000))
WEBHOOK_URL = f"https://cryptospreadbot-2-2.onrender.com/{TOKEN}"
CHECK_INTERVAL = 60  # секунды

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация API
API_CONFIG = {
    "binance": {
        "url": "https://api1.binance.com/api/v3/ticker/price",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["price"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    },
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},
        "price_key": ["data", "price"],
        "headers": {"Accept": "application/json"}
    }
}

bot = Bot(token=TOKEN)

async def get_price(exchange: str):
    try:
        config = API_CONFIG[exchange]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                config["url"],
                params=config["params"],
                headers=config.get("headers", {})
            )
            
            if response.status_code != 200:
                logger.warning(f"{exchange} status: {response.status_code}")
                return None
                
            data = response.json()
            price = data
            for key in config["price_key"]:
                if isinstance(price, (list, tuple)) and isinstance(key, int):
                    if len(price) <= key:
                        return None
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
                "🚨 BTC/USDT Spread > 2%\n\n"
                f"📊 {exchanges[0]}: {prices[exchanges[0]]:.2f}\n"
                f"📊 {exchanges[1]}: {prices[exchanges[1]]:.2f}\n"
                f"💰 Diff: {spread:.2f} ({spread_percent:.2f}%)\n\n"
                "🔗 Binance: https://www.binance.com/en/trade/BTC_USDT\n"
                "🔗 KuCoin: https://www.kucoin.com/trade/BTC-USDT"
            )
            try:
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                logger.info(f"Sent alert: {spread_percent:.2f}%")
            except Exception as e:
                logger.error(f"Send message error: {str(e)}")

async def run_scheduler():
    while True:
        await check_spread()
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    try:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook set")
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
    
    await run_scheduler()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
