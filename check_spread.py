import os
import time
import requests
from flask import Flask
from telegram import Bot

# Получение данных из переменных окружения
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Инициализация бота и Flask
bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

def get_price_coingecko():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        price = r.json()['bitcoin']['usd']
        print(f"CoinGecko BTC price: {price}")
        return float(price)
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return None

def get_price_binance():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        price = float(r.json()['price'])
        print(f"Binance BTC price: {price}")
        return price
    except Exception as e:
        print(f"Binance error: {e}")
        return None

@app.route("/")
def index():
    return "✅ Crypto Spread Monitor is running!"

def monitor_spread():
    THRESHOLD = 0.005  # 0.5%
    print("▶️ Старт мониторинга спредов...")

    while True:
        price1 = get_price_coingecko()
        price2 = get_price_binance()

        if price1 is None or price2 is None:
            print("❌ Ошибка получения цен")
            time.sleep(15)
            continue

        spread = abs(price1 - price2) / ((price1 + price2) / 2)
        spread_percent = spread * 100
        print(f"🔍 Текущий спред: {spread_percent:.3f}%")

        if spread >= THRESHOLD:
            msg = (
                f"🚨 СПРЕД BTC:\n"
                f"{spread_percent:.2f}% между Coingecko и Binance\n"
                f"Coingecko: {price1} $\nBinance: {price2} $\n"
                f"<a href='https://www.binance.com/en/trade/BTC_USDT'>Binance</a>"
            )
            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
                print("✅ Уведомление отправлено!")
            except Exception as e:
                print(f"❌ Ошибка отправки в Telegram: {e}")

        time.sleep(15)

if __name__ == '__main__':
    import threading

    # Запускаем мониторинг в отдельном потоке
    threading.Thread(target=monitor_spread, daemon=True).start()

    # Поддерживаем web-сервер для Render
    PORT = int(os.environ.get("PORT", 10000))  # берём из окружения
    app.run(host='0.0.0.0', port=PORT)
