import requests
import threading
import time
from flask import Flask, request
from telegram import Bot

# Твои данные:
TELEGRAM_TOKEN = "ВАШ_ТОКЕН_ТЕЛЕГРАМ"
CHAT_ID = ВАШ_CHAT_ID  # например, число без кавычек

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

SPREAD_THRESHOLD = 0.1  # в процентах, минимальный спред для уведомления
CHECK_INTERVAL = 30  # секунд между проверками

def get_binance_price():
    try:
        resp = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return float(data['price'])
    except Exception as e:
        print(f"Binance API error: {e}")
        return None

def get_bybit_price():
    try:
        resp = requests.get("https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT", timeout=5)
        resp.raise_for_status()
        data = resp.json()
        if 'result' in data and len(data['result']) > 0:
            return float(data['result'][0]['last_price'])
        else:
            return None
    except Exception as e:
        print(f"Bybit API error: {e}")
        return None

def check_spread():
    while True:
        price_binance = get_binance_price()
        price_bybit = get_bybit_price()

        if price_binance is None or price_bybit is None:
            print("Ошибка получения цены")
        else:
            spread = abs(price_binance - price_bybit) / ((price_binance + price_bybit) / 2) * 100
            print(f"Binance: {price_binance}, Bybit: {price_bybit}, Spread: {spread:.3f}%")
            if spread >= SPREAD_THRESHOLD:
                message = (f"🚨 СПРЕД! BTC/USDT: {spread:.2f}% между Binance и Bybit\n"
                           f"Binance: https://www.binance.com/en/trade/BTC_USDT\n"
                           f"Bybit: https://www.bybit.com/en-US/trade/spot/BTCUSDT")
                bot.send_message(chat_id=CHAT_ID, text=message)
        time.sleep(CHECK_INTERVAL)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if 'message' in update and 'text' in update['message']:
        text = update['message']['text']
        chat_id = update['message']['chat']['id']

        if text.lower() == '/start':
            bot.send_message(chat_id=chat_id, text="Привет! Я мониторю спреды BTC/USDT между Binance и Bybit.")
        return '', 200
    return '', 400

def run_flask():
    app.run(host='0.0.0.0', port=10000)

if __name__ == '__main__':
    # Запускаем Flask сервер в отдельном потоке
    threading.Thread(target=run_flask).start()

    # Запускаем мониторинг спреда
    check_spread()
