import os
import time
import requests
from telegram import Bot
from flask import Flask
from dotenv import load_dotenv

# Загрузка токенов из .env
load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)
app = Flask(__name__)

# Порог спреда в %
SPREAD_THRESHOLD = 2.0

def get_price_binance(symbol="BTCUSDT"):
    try:
        response = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")
        return float(response.json()['price'])
    except Exception as e:
        print(f"Binance error: {e}")
        return None

def get_price_bybit(symbol="BTCUSDT"):
    try:
        response = requests.get(f"https://api.bybit.com/v2/public/tickers?symbol={symbol}")
        return float(response.json()['result'][0]['last_price'])
    except Exception as e:
        print(f"Bybit error: {e}")
        return None

def check_spread():
    binance_price = get_price_binance()
    bybit_price = get_price_bybit()

    if binance_price is None or bybit_price is None:
        print("❌ Ошибка получения цен")
        return

    spread = abs(binance_price - bybit_price) / ((binance_price + bybit_price) / 2) * 100

    print(f"Binance: {binance_price}, Bybit: {bybit_price}, Spread: {spread:.2f}%")

    if spread >= SPREAD_THRESHOLD:
        message = (
            f"📊 Обнаружен спред:\n\n"
            f"💰 Binance: {binance_price} $\n"
            f"💰 Bybit: {bybit_price} $\n"
            f"📈 Разница: {spread:.2f}%\n\n"
            f"[Binance](https://www.binance.com/en/trade/BTC_USDT)\n"
            f"[Bybit](https://www.bybit.com/en/trade/usdt/BTCUSDT)"
        )
        bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')

@app.route("/")
def home():
    return "✅ CryptoSpreadBot запущен!"

if __name__ == "__main__":
    print("▶️ Старт мониторинга спредов...")
    while True:
        check_spread()
        time.sleep(15)  # Проверка каждые 15 секунд
