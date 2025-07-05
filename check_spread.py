import os
import requests
from flask import Flask
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler

# Константы
THRESHOLD = 2.0  # Спред в процентах
PAIR = "BTCUSDT"

# Токены и данные из переменных окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
PORT = int(os.environ.get("PORT", 10000))

bot = Bot(token=TOKEN)
app = Flask(__name__)

def get_price_binance():
    try:
        res = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={PAIR}', timeout=10)
        return float(res.json()["price"])
    except Exception as e:
        print(f"Binance error: {e}")
        return None

def get_price_bybit():
    try:
        res = requests.get(f'https://api.bybit.com/v2/public/tickers?symbol={PAIR}', timeout=10)
        return float(res.json()["result"][0]["last_price"])
    except Exception as e:
        print(f"Bybit error: {e}")
        return None

def check_spread():
    price_binance = get_price_binance()
    price_bybit = get_price_bybit()

    if not price_binance or not price_bybit:
        print("❌ Ошибка получения цен")
        return

    spread = abs(price_binance - price_bybit) / ((price_binance + price_bybit) / 2) * 100

    print(f"Binance: {price_binance}, Bybit: {price_bybit}, Spread: {spread:.2f}%")

    if spread >= THRESHOLD:
        message = (
            f"🚨 Спред превышен!\n\n"
            f"Binance: {price_binance} USDT\n"
            f"Bybit: {price_bybit} USDT\n"
            f"📊 Спред: {spread:.2f}%\n"
            f"\n👉 Binance: https://www.binance.com/ru/trade/{PAIR}\n"
            f"👉 Bybit: https://www.bybit.com/trade/usdt/{PAIR.replace('USDT', '')}"
        )
        bot.send_message(chat_id=CHAT_ID, text=message)

@app.route("/")
def home():
    return "✅ Crypto spread monitor is running"

if __name__ == "__main__":
    print("▶️ Старт мониторинга спредов...")

    scheduler = BackgroundScheduler()
    scheduler.add_job(check_spread, "interval", seconds=20)
    scheduler.start()

    app.run(host="0.0.0.0", port=PORT)
