import os
import time
import requests
from flask import Flask, request
from telegram import Bot

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
bot = Bot(token=TOKEN)

THRESHOLD = 0.1  # 0.1% спред
SYMBOLS = ["BTC/USDT", "ETH/USDT"]
CHECK_INTERVAL = 15  # секунд

BINANCE_URL = "https://api.binance.com/api/v3/ticker/bookTicker?symbol={}"
BYBIT_URL = "https://api.bybit.com/v2/public/tickers?symbol={}"

def get_binance_price(symbol):
    binance_symbol = symbol.replace("/", "")
    try:
        response = requests.get(BINANCE_URL.format(binance_symbol))
        data = response.json()
        return float(data['askPrice']), float(data['bidPrice'])
    except Exception as e:
        print(f"[BINANCE ERROR] {e}")
        return None, None

def get_bybit_price(symbol):
    bybit_symbol = symbol.replace("/", "")
    try:
        response = requests.get(BYBIT_URL.format(bybit_symbol))
        data = response.json()
        ticker = data["result"][0]
        return float(ticker["ask_price"]), float(ticker["bid_price"])
    except Exception as e:
        print(f"[BYBIT ERROR] {e}")
        return None, None

def check_spread():
    for symbol in SYMBOLS:
        b_ask, b_bid = get_binance_price(symbol)
        y_ask, y_bid = get_bybit_price(symbol)

        if None in [b_ask, b_bid, y_ask, y_bid]:
            continue

        # Разные варианты покупки/продажи
        opportunities = [
            ("Binance", "Bybit", b_bid, y_ask),
            ("Bybit", "Binance", y_bid, b_ask),
        ]

        for from_ex, to_ex, sell_price, buy_price in opportunities:
            spread = ((sell_price - buy_price) / buy_price) * 100
            print(f"[{symbol}] {from_ex} ➝ {to_ex}: Spread = {spread:.2f}%")

            if spread >= THRESHOLD:
                msg = (
                    f"🚨 СПРЕД НАЙДЕН!\n"
                    f"Валюта: {symbol}\n"
                    f"Спред: {spread:.2f}%\n"
                    f"Купить на: {to_ex}\n"
                    f"Продать на: {from_ex}\n\n"
                    f"🔗 Binance: https://www.binance.com/en/trade/{symbol.replace('/', '_')}\n"
                    f"🔗 Bybit: https://www.bybit.com/en/trade/spot/{symbol.replace('/', '')}"
                )
                bot.send_message(chat_id=CHAT_ID, text=msg)

@app.route("/")
def home():
    return "Bot is running"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        if update["message"]["text"] == "/start":
            bot.send_message(
                chat_id=CHAT_ID,
                text="Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление."
            )
    return "ok"

if __name__ == "__main__":
    import threading

    def run_checker():
        while True:
            check_spread()
            time.sleep(CHECK_INTERVAL)

    threading.Thread(target=run_checker, daemon=True).start()
    app.run(host="0.0.0.0", port=10000)
