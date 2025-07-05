import os
import logging
import pytz
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# Твои данные
TOKEN = "твой_токен_от_телеграм_бота"
CHAT_ID = твой_чат_id_целым_числом  # например: 123456789
PORT = int(os.environ.get("PORT", 10001))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
app = Flask(__name__)

# Функция проверки спреда (пример)
def check_spread():
    try:
        # Пример: запрос цен с двух бирж (замени на свои API)
        binance_price = float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT").json()["price"])
        bybit_price = float(requests.get("https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT").json()["result"][0]["last_price"])
        
        spread = abs(binance_price - bybit_price) / ((binance_price + bybit_price) / 2) * 100

        logging.info(f"Spread: {spread:.2f}%")

        threshold = 2.0  # Порог в процентах

        if spread > threshold:
            message = (
                f"🚨 Спред превышает порог {threshold}%!\n"
                f"Binance: {binance_price:.2f} USD\n"
                f"Bybit: {bybit_price:.2f} USD\n"
                f"Спред: {spread:.2f}%"
            )
            bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Ошибка при проверке спреда: {e}")

# Пример простой команды /start
def start(update, context):
    update.message.reply_text("Привет! Я мониторю спреды криптовалют.")

# Настройка Telegram dispatcher для обработки команд
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))

# Flask endpoint для webhook (если нужен)
@app.route("/", methods=["GET", "POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "ok"
    else:
        return "Bot is running"

if __name__ == "__main__":
    print("▶️ Старт мониторинга спредов...")

    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(check_spread, "interval", seconds=20)
    scheduler.start()

    app.run(host="0.0.0.0", port=PORT)
