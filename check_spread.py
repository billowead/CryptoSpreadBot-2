import os
import requests
import threading
import time
from flask import Flask
from telegram import Bot

# === Настройки ===
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
RAPIDAPI_KEY = "6ce956ea3amsh45b17d8a9c691a4p1f4badjsnbc9d72aff450"
PORT = int(os.getenv("PORT", 10001))

# === Настройка Flask ===
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

# === Заголовки RapidAPI ===
HEADERS_BINANCE = {
    "x-rapidapi-host": "binance43.p.rapidapi.com",
    "x-rapidapi-key": RAPIDAPI_KEY,
}
HEADERS_BYBIT = {
    "x-rapidapi-host": "bybit4.p.rapidapi.com",
    "x-rapidapi-key": RAPIDAPI_KEY,
}

# === Мониторим пары ===
PAIRS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT"]
SPREAD_THRESHOLD = 1.0  # в процентах

# === Получение цен с Binance ===
def get_binance_prices():
    try:
        url = "https://binance43.p.rapidapi.com/ticker/24hr"
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
        print(f"[Binance] Ошибка: {e}")
        return {}

# === Получение цен с Bybit ===
def get_bybit_prices():
    try:
        url = "https://bybit4.p.rapidapi.com/perpetual/usdc/openapi/public/v1/tick"
        response = requests.get(url, headers=HEADERS_BYBIT, timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = {}
        for item in data.get("result", []):
            symbol = item.get("symbol", "").replace("-", "").upper()
            if symbol in PAIRS:
                prices[symbol] = float(item.get("lastPrice"))
        return prices
    except Exception as e:
        print(f"[Bybit] Ошибка: {e}")
        return {}

# === Проверка спредов ===
def check_spreads():
    binance = get_binance_prices()
    bybit = get_bybit_prices()
    messages = []

    for pair in PAIRS:
        b_price = binance.get(pair)
        y_price = bybit.get(pair)
        if b_price and y_price:
            spread = abs(b_price - y_price) / ((b_price + y_price) / 2) * 100
            if spread >= SPREAD_THRESHOLD:
                msg = (
                    f"📊 Спред по {pair}:\n"
                    f"Binance: {b_price}\n"
                    f"Bybit: {y_price}\n"
                    f"Разница: {spread:.2f}%\n"
                    f"https://www.binance.com/en/trade/{pair}\n"
                    f"https://www.bybit.com/trade/usdc/{pair.lower()}"
                )
                messages.append(msg)

    if messages:
        for msg in messages:
            try:
                bot.send_message(chat_id=CHAT_ID, text=msg)
            except Exception as e:
                print(f"[Telegram] Ошибка отправки сообщения: {e}")
    else:
        print("[Info] Нет значимых спредов")

# === Фоновая проверка каждые 60 сек ===
def background_task():
    while True:
        print("[Info] Запуск фоновой проверки...")
        check_spreads()
        time.sleep(60)

# === Flask-маршруты ===
@app.route("/")
def home():
    return "✅ Crypto Spread Bot работает!"

@app.route("/check", methods=["GET"])
def manual_check():
    check_spreads()
    return {"status": "manual check complete"}, 200

# === Запуск приложения и фоновой задачи ===
if __name__ == "__main__":
    threading.Thread(target=background_task, daemon=True).start()
    app.run(host="0.0.0.0", port=PORT)
