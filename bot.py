import os
import logging
import asyncio
from telegram import Bot
import httpx

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
PORT = int(os.environ.get('PORT', 10000))
WEBHOOK_URL = f"https://cryptospreadbot-2-2.onrender.com/{TOKEN}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)

async def check_spread():
    try:
        async with httpx.AsyncClient() as client:
            binance = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
            bybit = await client.get("https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT")

            binance_price = float(binance.json()["price"])
            bybit_price = float(bybit.json()["result"][0]["last_price"])

            spread = abs(binance_price - bybit_price)
            spread_percent = (spread / ((binance_price + bybit_price) / 2)) * 100

            if spread_percent >= 2:
                msg = (
                    f"💰 Спред BTC/USDT: {spread:.2f} USDT ({spread_percent:.2f}%)\n\n"
                    f"🔗 Binance: https://www.binance.com/en/trade/BTC_USDT\n"
                    f"🔗 Bybit: https://www.bybit.com/en/trade/spot/BTC/USDT"
                )
                await bot.send_message(chat_id=CHAT_ID, text=msg)
                logger.info(f"Отправлено сообщение о спреде: {spread_percent:.2f}%")

    except Exception as e:
        logger.error(f"Ошибка при проверке спреда: {e}")

async def run_scheduler():
    while True:
        try:
            await check_spread()
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")
            await asyncio.sleep(10)  # Пауза перед повторной попыткой

async def main():
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("✅ Webhook установлен")
    
    # Запускаем планировщик в фоне
    scheduler_task = asyncio.create_task(run_scheduler())
    
    # Просто ждём (можно добавить другую логику)
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        scheduler_task.cancel()
        await scheduler_task

if __name__ == "__main__":
    asyncio.run(main())
