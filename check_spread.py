import time
import threading
import requests
from flask import Flask
from telegram import Bot
import os

# Загружаем переменные из окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def get_price_coingecko():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        price = r.json()['bitcoin']['usd']
        print(f"[✓] Coingecko BTC price: {price}")
        return float(price)
    except Exception as e:
        print(f"❌ CoinGecko error: {e}")
        return None

def get_price_binance():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        price = float(r.json()['price'])
        print(f"[✓] Binance BTC price: {price}")
        return price
    except Exception as e:
        print(f"❌ Binance error: {e}")
        return None

def monitor_spread():
    THRESHOLD = 0.005  # 0.5%
    print("▶️ Старт мониторинга спредов...")
    while True:
        price1 = get_price_coingecko()
        price2 = get_price_binance()
        if price1 is None or price2 is None:
            print("⚠️ Ошибка получения цен, ждём 30 сек...")
            time.sleep(30)
            continue

        spread = abs(price1 - price2) / ((price1 + price2) / 2)
        spread_percent = spread * 100
        print(f"🔍 Текущий спред: {spread_percent:.3f}%")

        if spread >= THRESHOLD:
            msg = (
                f"🚨 СПРЕД! BTC:\n"
                f"{spread_percent:.2f}% между Coingecko и Binance\n"
                f"Цены:\nCoingecko: {price1}\nBinance: {price2}\n"
                f"<a href='https://www.binance.com/en/trade/BTC_USDT'>Binance</a>"
            )
            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
                print("✅ Отправлено в Telegram")
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
        time.sleep(30)

# Стартуем мониторинг в отдельном потоке
threading.Thread(target=monitor_spread).start()

# ⚠️ Flask-приложение для "обмана" Render
app = Flask(__name__)

@app.route('/')
def index():
    return "✅ Bot is running."

# Запускаем Flask (Render будет думать, что это Web-сервис)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
