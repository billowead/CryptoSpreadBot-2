from flask import Flask
import requests
import os
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot

app = Flask(__name__)

# Твои данные
BOT_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
SPREAD_THRESHOLD = 0.5  # порог в процентах

bot = Bot(token=BOT_TOKEN)

TRADING_PAIRS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"
]

def get_price_kraken(symbol):
    try:
        symbol_map = {
            "BTCUSDT": "XBTUSDT", "ETHUSDT": "ETHUSDT", "SOLUSDT": "SOLUSDT",
            "XRPUSDT": "XRPUSDT", "DOGEUSDT": "DOGEUSDT", "ADAUSDT": "ADAUSDT"
        }
        url = f"https://api.kraken.com/0/public/Ticker?pair={symbol_map[symbol]}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = list(data["result"].values())[0]["c"][0]
        return float(price)
    except Exception as e:
        print(f"Ошибка Kraken {symbol}: {e}")
        return None

def get_price_kucoin(symbol):
    try:
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        return float(data["data"]["price"])
    except Exception as e:
        print(f"Ошибка KuCoin {symbol}: {e}")
        return None

def check_spread():
    for pair in TRADING_PAIRS:
        price_kraken = get_price_kraken(pair)
        price_kucoin = get_price_kucoin(pair)

        prices = {
            "kraken": price_kraken,
            "kucoin": price_kucoin
        }

        if None in prices.values():
            print(f"Недостаточно данных для {pair}, цены: {prices}")
            continue

        max_price = max(prices.values())
        min_price = min(prices.values())
        spread = (max_price - min_price) / min_price * 100

        if spread >= SPREAD_THRESHOLD:
            msg = (
                f"📈 Спред по {pair} — {spread:.2f}%\n"
                f"Kraken: {price_kraken}\nKuCoin: {price_kucoin}"
            )
            bot.send_message(chat_id=CHAT_ID, text=msg)
            print(f"🔔 {msg}")
        else:
            print(f"✅ {pair}: спред {spread:.2f}% — не превышает порог")

@app.route("/")
def index():
    return "Crypto spread bot работает!"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_spread, "interval", seconds=30)
    scheduler.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
