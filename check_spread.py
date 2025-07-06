import os
import requests
from flask import Flask, request
from telegram import Bot

app = Flask(__name__)

# Твои данные (заполни свои данные прямо здесь)
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"  # Твой токен Telegram-бота
CHAT_ID = "593059857"  # Твой Telegram chat_id
RAPIDAPI_KEY = "6ce956ea3amsh45b17d8a9c691a4p1f4badjsnbc9d72aff450"  # Твой RapidAPI ключ
PORT = int(os.getenv("PORT", 10001))  # Порт для рендера, по умолчанию 10001

bot = Bot(token=TELEGRAM_TOKEN)

HEADERS_BINANCE = {
    "x-rapidapi-host": "binance43.p.rapidapi.com",
    "x-rapidapi-key": RAPIDAPI_KEY,
}

HEADERS_BYBIT = {
    "x-rapidapi-host": "bybit4.p.rapidapi.com",
    "x-rapidapi-key": RAPIDAPI_KEY,
}

PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]

SPREAD_THRESHOLD = 1.0  # Порог в процентах

def get_binance_prices():
    url = "https://binance43.p.rapidapi.com/ticker/24hr"
    try:
        response = requests.get(url, headers=HEADERS_BINANCE, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = {}
        for item in data:
            symbol = item.get("symbol")
            if symbol in PAIRS:
                prices[symbol] = float(item.get("lastPrice"))
        return prices
    except Exception as e:
        print(f"Error getting Binance prices: {e}")
        return {}

def get_bybit_prices():
    url = "https://bybit4.p.rapidapi.com/perpetual/usdc/openapi/public/v1/tick"
    try:
        response = requests.get(url, headers=HEADERS_BYBIT, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = {}
        for item in data.get("result", []):
            symbol = item.get("symbol")
            if symbol in PAIRS:
                prices[symbol] = float(item.get("lastPrice"))
        return prices
    except Exception as e:
        print(f"Error getting Bybit prices: {e}")
        return {}

def check_spreads():
    binance_prices = get_binance_prices()
    bybit_prices = get_bybit_prices()

    messages = []
    for pair in PAIRS:
        b_price = binance_prices.get(pair)
        y_price = bybit_prices.get(pair)
        if b_price and y_price:
            spread = abs(b_price - y_price) / ((b_price + y_price) / 2) * 100
            if spread >= SPREAD_THRESHOLD:
                msg = (
                    f"Спред по {pair}:\n"
                    f"Binance: {b_price}\n"
                    f"Bybit: {y_price}\n"
                    f"Разница: {spread:.2f}%\n"
                    f"https://www.binance.com/en/trade/{pair}\n"
                    f"https://www.bybit.com/trade/usdc/{pair.lower()}"
                )
                messages.append(msg)
    return messages

@app.route("/check", methods=["GET"])
def check():
    messages = check_spreads()
    if messages:
        for msg in messages:
            bot.send_message(chat_id=CHAT_ID, text=msg)
        return {"status": "sent", "count": len(messages)}, 200
    else:
        return {"status": "no_spreads"}, 200

@app.route("/")
def index():
    return "Crypto Spread Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
