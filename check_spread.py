import os
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import utc
from telegram import Bot

# === Твои данные ===
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
SPREAD_THRESHOLD = 0.5  # в процентах

# === Валютные пары ===
TRADING_PAIRS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT",
    "ADAUSDT", "TONUSDT", "BNBUSDT"
]

# === Flask app ===
app = Flask(__name__)
bot = Bot(token=TELEGRAM_TOKEN)

@app.route("/")
def home():
    return "Crypto Spread Bot is running!"

# === Получение цены ===
def get_price_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return float(response.json()["price"])
    except Exception as e:
        print(f"Ошибка получения цены для {symbol} на binance: {e}")
        return None

def get_price_bybit(symbol):
    try:
        url = f"https://api.bybit.com/spot/quote/v1/ticker/24hr?symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return float(response.json()["lastPrice"])
    except Exception as e:
        print(f"Ошибка получения цены для {symbol} на bybit: {e}")
        return None

# === Проверка спреда ===
def check_spread():
    for pair in TRADING_PAIRS:
        price_binance = get_price_binance(pair)
        price_bybit = get_price_bybit(pair)

        if price_binance is None or price_bybit is None:
            continue

        try:
            spread = abs(price_binance - price_bybit) / min(price_binance, price_bybit) * 100
            if spread >= SPREAD_THRESHOLD:
                message = (
                    f"🔔 Арбитраж найден для {pair}:\n"
                    f"Binance: {price_binance}\n"
                    f"Bybit: {price_bybit}\n"
                    f"Спред: {spread:.2f}%"
                )
                bot.send_message(chat_id=CHAT_ID, text=message)
                print("✅ Отправлено:", message)
        except Exception as e:
            print(f"Ошибка расчета спреда для {pair}: {e}")

# === Планировщик ===
if __name__ == "__main__":
    scheduler = BackgroundScheduler(timezone=utc)
    scheduler.add_job(check_spread, "interval", seconds=30)
    scheduler.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
