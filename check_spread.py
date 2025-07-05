import os
import requests
from flask import Flask
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

bot = Bot(token=TOKEN)

PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "DOGE/USDT",
    "ADA/USDT",
    "TON/USDT",
    "BNB/USDT"
]

def get_price(pair, exchange):
    symbol = pair.replace("/", "")
    url = ""

    if exchange == "binance":
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    elif exchange == "bybit":
        url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        if exchange == "binance":
            return float(data["price"])
        elif exchange == "bybit":
            return float(data["result"][0]["last_price"])

    except Exception as e:
        print(f"Ошибка получения цены для {pair} на {exchange}: {e}")
        return None

def check_spread():
    for pair in PAIRS:
        price_binance = get_price(pair, "binance")
        price_bybit = get_price(pair, "bybit")

        if price_binance is None or price_bybit is None or min(price_binance, price_bybit) == 0:
            continue

        spread = abs(price_binance - price_bybit) / min(price_binance, price_bybit) * 100

        if spread >= 2:
            message = (
                f"📊 Спред {pair} превышает 2%\n\n"
                f"💱 Binance: {price_binance}\n"
                f"💱 Bybit: {price_bybit}\n"
                f"📈 Spread: {spread:.2f}%\n\n"
                f"🔗 Binance: https://www.binance.com/en/trade/{pair.replace('/', '_')}\n"
                f"🔗 Bybit: https://www.bybit.com/en/trade/spot/{pair.replace('/', '')}"
            )
            bot.send_message(chat_id=CHAT_ID, text=message)

@app.route("/")
def index():
    return "Crypto spread bot is running!"

if __name__ == "__main__":
    print("▶️ Старт мониторинга спредов...")
    scheduler = BackgroundScheduler(timezone=pytz.utc)
    scheduler.add_job(check_spread, "interval", seconds=20)
    scheduler.start()
    port = int(os.environ.get("PORT", 10001))
    app.run(host="0.0.0.0", port=port)
