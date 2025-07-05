from flask import Flask, request
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import requests

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857  # Твой Telegram chat ID числом

bot = Bot(token=TOKEN)
app = Flask(__name__)

def check_spread():
    # Пример проверки спреда — тут твоя логика получения и сравнения курсов
    # Ниже заглушка, меняй под себя
    price_binance = get_price_binance()
    price_bybit = get_price_bybit()
    spread = abs(price_binance - price_bybit) / min(price_binance, price_bybit) * 100

    threshold = 2.0  # порог в процентах для уведомления
    if spread >= threshold:
        message = f"Спред между Binance и Bybit: {spread:.2f}%\nBinance: {price_binance}\nBybit: {price_bybit}"
        bot.send_message(chat_id=CHAT_ID, text=message)

def get_price_binance():
    try:
        r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
        return float(r.json()['price'])
    except Exception:
        return 0

def get_price_bybit():
    try:
        r = requests.get("https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT")
        return float(r.json()['result'][0]['last_price'])
    except Exception:
        return 0

scheduler = BackgroundScheduler(timezone=pytz.utc)
scheduler.add_job(check_spread, "interval", seconds=20)
scheduler.start()

@app.route("/", methods=["GET", "HEAD"])
def index():
    return "Bot is running"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10001))
    print("▶️ Старт мониторинга спредов...")
    app.run(host="0.0.0.0", port=port)
