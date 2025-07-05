import os
import logging
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes
import httpx

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857  # Твой Telegram ID
WEBHOOK_URL = f"https://cryptospreadbot-2-2.onrender.com/{TOKEN}"

app = Flask(__name__)
bot = Bot(token=TOKEN)
application = ApplicationBuilder().token(TOKEN).build()

logging.basicConfig(level=logging.INFO)

# ✅ Основная логика проверки спреда
async def check_spread():
    try:
        async with httpx.AsyncClient() as client:
            # Пример запроса к Binance и Bybit
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

    except Exception as e:
        logging.error(f"Ошибка при проверке спреда: {e}")

# ✅ Планировщик задач
async def run_scheduler():
    while True:
        await check_spread()
        await asyncio.sleep(60)  # Проверка каждую минуту

# ✅ Webhook обработчик
@app.post(f"/{TOKEN}")
async def telegram_webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, bot)
        await application.process_update(update)
    except Exception as e:
        logging.error(f"Webhook error: {e}")
    return "ok"

# ✅ Установка webhook и запуск планировщика
async def start_bot():
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("✅ Webhook установлен")
    asyncio.create_task(run_scheduler())

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_bot())
    app.run(host="0.0.0.0", port=10000)
