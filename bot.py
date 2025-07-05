import requests
from flask import Flask, request
import threading
import time
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

THRESHOLD = 0.1  # порог спреда в процентах

PAIRS = ["BTC/USDT", "ETH/USDT"]

BINANCE_API = "https://api.binance.com/api/v3/ticker/price?symbol="
BYBIT_API = "https://api.bybit.com/v2/public/tickers?symbol="

def get_binance_price(symbol):
    formatted = symbol.replace("/", "")
    response = requests.get(BINANCE_API + formatted)
    return float(response.json()["price"])

def get_bybit_price(symbol):
    formatted = symbol.replace("/", "")
    response = requests.get(BYBIT_API + formatted)
    data = response.json()
    for ticker in data["result"]:
        if ticker["symbol"] == formatted:
            return float(ticker["last_price"])
    return None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def monitor_spread():
    while True:
        try:
            for pair in PAIRS:
                binance_price = get_binance_price(pair)
                bybit_price = get_bybit_price(pair)

                if binance_price and bybit_price:
                    spread = abs(binance_price - bybit_price) / ((binance_price + bybit_price) / 2) * 100
                    if spread >= THRESHOLD:
                        message = (
                            f"🚨 СПРЕД! <b>{pair}</b>: <b>{spread:.2f}%</b>\n"
                            f"<b>Binance:</b> {binance_price}\n"
                            f"<b>Bybit:</b> {bybit_price}\n\n"
                            f"📈 <a href='https://www.binance.com/en/trade/{pair.replace('/', '_')}'>Binance</a> | "
                            f"<a href='https://www.bybit.com/trade/usdt/{pair.lower().replace('/', '')}'>Bybit</a>"
                        )
                        send_telegram_message(message)
        except Exception as e:
            print(f"Ошибка: {e}")
        time.sleep(15)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        if text == "/start":
            send_telegram_message("Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление.")
    return "ok", 200

def run_bot():
    app.run(host="0.0.0.0", port=10000)

if __name__ == '__main__':
    threading.Thread(target=monitor_spread).start()
    run_bot()
