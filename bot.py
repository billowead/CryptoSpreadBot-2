import threading
import time
import requests
from flask import Flask, request
from telegram import Bot

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
SPREAD_THRESHOLD = 0.001  # 0.1%

bot = Bot(token=TOKEN)
app = Flask(__name__)

exchanges = {
    'Binance': 'https://api.binance.com/api/v3/ticker/price?symbol={}',
    'Bybit': 'https://api.bybit.com/v2/public/tickers?symbol={}'
}

pairs = ['BTCUSDT', 'ETHUSDT']  # валютные пары для мониторинга

def get_price_binance(symbol):
    try:
        response = requests.get(exchanges['Binance'].format(symbol))
        data = response.json()
        price = float(data['price'])
        return price
    except Exception as e:
        print(f"[Binance] Ошибка получения цены {symbol}: {e}")
        return None

def get_price_bybit(symbol):
    try:
        # Bybit API возвращает список тикеров, ищем нужный
        response = requests.get(exchanges['Bybit'].format(symbol))
        data = response.json()
        for item in data['result']:
            if item['symbol'] == symbol:
                price = float(item['last_price'])
                return price
        return None
    except Exception as e:
        print(f"[Bybit] Ошибка получения цены {symbol}: {e}")
        return None

def check_spread():
    while True:
        print("=== Проверка спредов ===")
        for pair in pairs:
            price_binance = get_price_binance(pair)
            price_bybit = get_price_bybit(pair)
            print(f"Пара {pair} - Binance: {price_binance}, Bybit: {price_bybit}")
            if price_binance and price_bybit:
                diff = abs(price_binance - price_bybit)
                avg = (price_binance + price_bybit) / 2
                spread = diff / avg
                spread_percent = spread * 100
                print(f"Спред: {spread_percent:.4f}%")
                if spread >= SPREAD_THRESHOLD:
                    msg = (
                        f"🚨 СПРЕД! {pair}: {spread_percent:.2f}% между "
                        f"Binance и Bybit\n"
                        f"Binance: {price_binance}\n"
                        f"Bybit: {price_bybit}\n"
                        f"https://www.binance.com/en/trade/{pair}\n"
                        f"https://www.bybit.com/trade/{pair}"
                    )
                    print(f"Отправляем уведомление:\n{msg}")
                    try:
                        bot.send_message(chat_id=CHAT_ID, text=msg)
                    except Exception as e:
                        print(f"Ошибка отправки сообщения: {e}")
            else:
                print(f"Не удалось получить цены для {pair}")
        print("=== Проверка окончена. Ждём 60 секунд... ===\n")
        time.sleep(60)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        text = update['message']['text'].lower()
        if text == '/start':
            bot.send_message(chat_id=chat_id, text="Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление.")
    return 'ok'

if __name__ == '__main__':
    thread = threading.Thread(target=check_spread)
    thread.daemon = True
    thread.start()
    app.run(host='0.0.0.0', port=10000)
