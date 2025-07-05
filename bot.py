import os
import threading
import time
import requests
from flask import Flask, request
from telegram import Bot

# Твои данные
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
SPREAD_THRESHOLD = 0.5  # Процент спреда для уведомления

bot = Bot(token=TOKEN)
app = Flask(__name__)

def get_price_binance():
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10)
        res.raise_for_status()
        return float(res.json()["price"])
    except Exception as e:
        print(f"Ошибка Binance: {e}")
        return None

def get_price_bybit():
    try:
        res = requests.get("https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT", timeout=10)
        res.raise_for_status()
        data = res.json()
        if data["ret_code"] == 0:
            return float(data["result"][0]["last_price"])
        else:
            print("Ошибка Bybit: неверный код ret_code")
            return None
    except Exception as e:
        print(f"Ошибка Bybit: {e}")
        return None

def check_spread():
    while True:
        price_binance = get_price_binance()
        price_bybit = get_price_bybit()
        if price_binance and price_bybit:
            spread = abs(price_binance - price_bybit) / min(price_binance, price_bybit) * 100
            print(f"Binance: {price_binance}, Bybit: {price_bybit}, Spread: {spread:.4f}%")
            if spread >= SPREAD_THRESHOLD:
                msg = (
                    f"🚨 СПРЕД BTC/USDT: {spread:.2f}% между "
                    f"[Binance](https://www.binance.com/en/trade/BTC_USDT) и "
                    f"[Bybit](https://www.bybit.com/trade/BTCUSDT)\n\n"
                    f"Binance: ${price_binance:.2f}\n"
                    f"Bybit: ${price_bybit:.2f}"
                )
                try:
                    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='Markdown', disable_web_page_preview=True)
                except Exception as e:
                    print(f"Ошибка отправки сообщения: {e}")
        else:
            print("Не удалось получить цены с обеих бирж.")
        time.sleep(60)  # Проверять раз в минуту

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json(force=True)
    if 'message' in data and 'text' in data['message']:
        text = data['message']['text']
        chat_id = data['message']['chat']['id']

        if text == '/start':
            bot.send_message(chat_id=chat_id, text="Привет! Я мониторю спреды между Binance и Bybit по BTC/USDT.\n"
                                                   f"Я пришлю уведомление, когда спред превысит {SPREAD_THRESHOLD}%.")

    return 'OK', 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', '10000')))

if __name__ == '__main__':
    # Запускаем Flask в отдельном потоке
    threading.Thread(target=run_flask).start()
    print("▶️ Запущен фоновый мониторинг спредов...")
    check_spread()
