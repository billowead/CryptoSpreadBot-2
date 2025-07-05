import os
import requests
from flask import Flask
from telegram import Bot
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc

# Твои данные Telegram
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857

app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "TONUSDT",
    "BNBUSDT"
]

EXCHANGES = ["binance", "bybit", "kucoin", "kraken", "coinbase"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/115.0 Safari/537.36"
    )
}

def get_price(exchange, symbol):
    try:
        if exchange == "binance":
            url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return float(data['price'])

        elif exchange == "bybit":
            url = f"https://api.bybit.com/spot/quote/v1/ticker/24hr?symbol={symbol}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if data["retCode"] == 0 and data["result"]:
                return float(data["result"][0]["lastPrice"])
            return None

        elif exchange == "kucoin":
            url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == "200000":
                return float(data["data"]["price"])
            return None

        elif exchange == "kraken":
            kraken_symbol = symbol.replace("USDT", "USD").replace("BUSD", "USD")
            url = f"https://api.kraken.com/0/public/Ticker?pair={kraken_symbol}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if "result" in data:
                first_key = list(data["result"].keys())[0]
                return float(data["result"][first_key]["c"][0])
            return None

        elif exchange == "coinbase":
            url = f"https://api.pro.coinbase.com/products/{symbol}/ticker"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            return float(data['price'])

    except requests.exceptions.HTTPError as http_err:
        print(f"Ошибка получения цены для {symbol} на {exchange}: {http_err}")
    except Exception as e:
        print(f"Общая ошибка для {symbol} на {exchange}: {e}")

    return None

def check_spread():
    for symbol in SYMBOLS:
        prices = {}
        for ex in EXCHANGES:
            price = get_price(ex, symbol)
            if price:
                prices[ex] = price

        if len(prices) < 2:
            print(f"Недостаточно данных для {symbol}, цены: {prices}")
            continue

        ex_list = list(prices.items())
        for i in range(len(ex_list)):
            for j in range(i + 1, len(ex_list)):
                ex1, p1 = ex_list[i]
                ex2, p2 = ex_list[j]
                try:
                    spread = abs(p1 - p2) / min(p1, p2) * 100
                    if spread >= 0.5:
                        message = (f"📊 Спред {spread:.2f}% между {ex1} и {ex2} по {symbol}:\n"
                                   f"{ex1}: {p1}\n{ex2}: {p2}\n"
                                   f"https://www.google.com/search?q={symbol}+{ex1}+vs+{ex2}")
                        print(message)
                        bot.send_message(chat_id=CHAT_ID, text=message)
                except ZeroDivisionError:
                    print(f"Ошибка: деление на ноль для {symbol} при сравнении {ex1} и {ex2}")

scheduler = BackgroundScheduler(timezone=utc)
scheduler.add_job(check_spread, "interval", seconds=20)
scheduler.start()

@app.route("/", methods=["GET"])
def home():
    return "CryptoSpreadBot is running."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
