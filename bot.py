import requests
import threading
import time
from flask import Flask, request
from telegram import Bot

TELEGRAM_TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/113.0.0.0 Safari/537.36'
}

def get_coingecko_price():
    try:
        url = 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        price = response.json()['bitcoin']['usd']
        print(f"CoinGecko BTC price: {price}")
        return price
    except Exception as e:
        print(f"CoinGecko API error: {e}")
        return None

def get_bybit_price(symbol='BTCUSDT'):
    try:
        url = f'https://api.bybit.com/v2/public/tickers?symbol={symbol}'
        response = requests.get(url, headers=HEADERS, timeout=5)
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
            price_coingecko = get_coingecko_price()
            price_bybit = get_bybit_price(symbol)

            if price_coingecko is None or price_bybit is None:
                print("Ошибка получения цен, пропускаем цикл.")
                time.sleep(60)  # увеличил паузу
                continue

            spread = abs(price_coingecko - price_bybit) / ((price_coingecko + price_bybit) / 2)
            spread_percent = spread * 100

            print(f"Текущий спред: {spread_percent:.4f}%")

            if spread >= THRESHOLD:
                msg = (
                    f"🚨 СПРЕД! {symbol}:\n"
                    f"{spread_percent:.2f}% между "
                    f"CoinGecko и "
                    f"<a href='https://www.bybit.com/trade/{symbol}'>Bybit</a>\n"
                    f"Цены:\nCoinGecko: {price_coingecko}\nBybit: {price_bybit}"
                )
                print("Отправляем уведомление в Telegram")
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')

            time.sleep(60)  # увеличил паузу, чтобы снизить риск блокировки
        except Exception as e:
            print(f"Ошибка в check_spread: {e}")
            time.sleep(60)

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
    threading.Thread(target=check_spread, daemon=True).start()
    run_flask()
