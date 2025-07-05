import os
import threading
import time
import requests
from flask import Flask, request
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN') or '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = int(os.getenv('CHAT_ID') or 593059857)
PORT = int(os.getenv('PORT') or 10000)

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

def get_price_coingecko():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        price = r.json()['bitcoin']['usd']
        print(f"Coingecko BTC price: {price}")
        return float(price)
    except Exception as e:
        print(f"CoinGecko API error: {e}")
        return None

def get_price_binance():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/115.0 Safari/537.36",
            "Accept": "application/json",
            "Referer": "https://www.binance.com/"
        }
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        price = float(r.json()['price'])
        print(f"Binance BTC price: {price}")
        return price
    except Exception as e:
        print(f"Binance API error: {e}")
        return None

def monitor_spread():
    THRESHOLD = 0.005  # 0.5%
    print("▶️ Запущен фоновый мониторинг спредов...")
    while True:
        price1 = get_price_coingecko()
        price2 = get_price_binance()
        if price1 is None or price2 is None:
            print("Ошибка получения цен, пропускаем цикл.")
            time.sleep(60)  # Задержка 60 секунд при ошибках
            continue

        spread = abs(price1 - price2) / ((price1 + price2) / 2)
        spread_percent = spread * 100
        print(f"Текущий спред: {spread_percent:.3f}%")

        if spread >= THRESHOLD:
            msg = (
                f"🚨 СПРЕД! BTC:\n"
                f"{spread_percent:.2f}% между Coingecko и Binance\n"
                f"Цены:\nCoingecko: {price1}\nBinance: {price2}\n"
                f"<a href='https://www.binance.com/en/trade/BTC_USDT'>Binance</a>"
            )
            print("Отправляем уведомление в Telegram")
            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
            except Exception as e:
                print(f"Ошибка отправки сообщения: {e}")

        time.sleep(60)  # Основная задержка между циклами 60 секунд

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json(force=True)
    print("Получено обновление:", update)
    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        text = update['message']['text']
        if text == '/start':
            bot.send_message(chat_id=chat_id, text="Привет! Я мониторю спреды между биржами. Жди уведомлений!")
    return 'ok'

if __name__ == '__main__':
    threading.Thread(target=monitor_spread, daemon=True).start()
    print(f"Запуск Flask на порту {PORT}")
    app.run(host='0.0.0.0', port=PORT)
