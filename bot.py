import requests
import threading
import time
from flask import Flask, request
from telegram import Bot

# Твои данные:
TELEGRAM_TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

def get_binance_price(symbol='BTCUSDT'):
    try:
        url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        price = float(response.json()['price'])
        print(f"Binance {symbol} price: {price}")
        return price
    except Exception as e:
        print(f"Binance API error: {e}")
        return None

def get_bybit_price(symbol='BTCUSDT'):
    try:
        url = f'https://api.bybit.com/v2/public/tickers?symbol={symbol}'
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        price = float(data['result'][0]['last_price'])
        print(f"Bybit {symbol} price: {price}")
        return price
    except Exception as e:
        print(f"Bybit API error: {e}")
        return None

def check_spread():
    THRESHOLD = 0.001  # 0.1%
    symbol = 'BTCUSDT'

    print("▶️ Запущен фоновый мониторинг спредов...")
    while True:
        try:
            print("Проверяем цены...")
            price_binance = get_binance_price(symbol)
            price_bybit = get_bybit_price(symbol)

            if price_binance is None or price_bybit is None:
                print("Ошибка получения цен, пропускаем цикл.")
                time.sleep(15)
                continue

            spread = abs(price_binance - price_bybit) / ((price_binance + price_bybit) / 2)
            spread_percent = spread * 100

            print(f"Текущий спред: {spread_percent:.4f}%")

            if spread >= THRESHOLD:
                msg = (
                    f"🚨 СПРЕД! {symbol}:\n"
                    f"{spread_percent:.2f}% между "
                    f"<a href='https://www.binance.com/en/trade/{symbol}'>Binance</a> и "
                    f"<a href='https://www.bybit.com/trade/{symbol}'>Bybit</a>\n"
                    f"Цены:\nBinance: {price_binance}\nBybit: {price_bybit}"
                )
                print("Отправляем уведомление в Telegram")
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

            time.sleep(15)
        except Exception as e:
            print(f"Ошибка в check_spread: {e}")
            time.sleep(15)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    print("Получено обновление:", update)

    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        text = update['message']['text']

        if text == '/start':
            bot.send_message(chat_id=chat_id, text="Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление.")
    return 'ok'

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    threading.Thread(target=check_spread).start()
