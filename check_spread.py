from flask import Flask
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import pytz
import os

app = Flask(__name__)

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857

bot = Bot(token=TOKEN)

def get_price_binance():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        price = float(data["price"])
        return price
    except Exception as e:
        print(f"Ошибка при получении цены Binance: {e}")
        return 0.0

def get_price_bybit():
    try:
        url = "https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        price = float(data["result"][0]["last_price"])
        return price
    except Exception as e:
        print(f"Ошибка при получении цены Bybit: {e}")
        return 0.0

def check_spread():
    price_binance = get_price_binance()
    price_bybit = get_price_bybit()

    if price_binance <= 0 or price_bybit <= 0:
        print("Ошибка: получили нулевую или отрицательную цену, пропускаем проверку.")
        return

    spread = abs(price_binance - price_bybit) / min(price_binance, price_bybit) * 100
    threshold = 2.0  # процент порога для уведомления

    if spread >= threshold:
        message = (
            f"Спред между Binance и Bybit: {spread:.2f}%\n"
            f"Binance: {price_binance}\n"
            f"Bybit: {price_bybit}"
        )
        bot.send_message(chat_id=CHAT_ID, text=message)
        print(f"Отправлено сообщение: {message}")
    else:
        print(f"Спред {spread:.2f}% меньше порога {threshold}% — сообщений не отправляем.")

@app.route("/")
def index():
    return "Crypto Spread Bot is running!"

if __name__ == "__main__":
    scheduler = BackgroundScheduler(timezone=pytz.timezone("UTC"))
    scheduler.add_job(check_spread, "interval", seconds=20)
    scheduler.start()
    print("▶️ Старт мониторинга спредов...")

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10001)))
