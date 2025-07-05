import requests
import threading
import time
from flask import Flask, request
from telegram import Bot

TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857
PORT = 10000
threshold = 0.01  # 1%

pairs = ['BTC/USDT', 'ETH/USDT']

exchanges = {
    'Binance': 'https://api.binance.com/api/v3/ticker/price?symbol=',
    'Bybit': 'https://api.bybit.com/v2/public/tickers?symbol='
}

app = Flask(__name__)
bot = Bot(token=TOKEN)

def get_binance_price(pair):
    symbol = pair.replace('/', '')
    url = exchanges['Binance'] + symbol
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        price = float(data['price'])
        print(f"Binance {pair}: {price}")
        return price
    except Exception as e:
        print(f"Ошибка Binance для {pair}: {e}")
        return None

def get_bybit_price(pair):
    symbol = pair.replace('/', '')
    url = exchanges['Bybit'] + symbol
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        data = r.json()
        if data.get('ret_msg') == 'OK' and data.get('result'):
            price = float(data['result'][0]['last_price'])
            print(f"Bybit {pair}: {price}")
            return price
        else:
            print(f"Bybit ответ не OK для {pair}: {data}")
            return None
    except Exception as e:
        print(f"Ошибка Bybit для {pair}: {e}")
        return None

def send_message(text):
    try:
        bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML', disable_web_page_preview=True)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

def check_spreads():
    while True:
        print("=== Проверка спредов ===")
        for pair in pairs:
            binance_price = get_binance_price(pair)
            bybit_price = get_bybit_price(pair)
            if binance_price is None or bybit_price is None:
                print(f"Пропускаем {pair} из-за ошибки в получении цены")
                continue

            spread = abs(binance_price - bybit_price) / min(binance_price, bybit_price)
            spread_percent = spread * 100
            print(f"Спред {pair} Binance-Bybit: {spread_percent:.4f}%")

            if spread >= threshold:
                msg = (f"🚨 <b>СПРЕД!</b> {pair}: {spread_percent:.2f}% между Binance и Bybit\n"
                       f"<a href='https://www.binance.com/en/trade/{pair.replace('/', '_')}'>Binance</a>\n"
                       f"<a href='https://www.bybit.com/trade/spot/{pair.replace('/', '')}'>Bybit</a>")
                send_message(msg)
        time.sleep(60)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')

        if text == '/start':
            send_message("Привет! Я мониторю спреды между Binance и Bybit. При спреде >1% пришлю уведомление.")
        else:
            send_message("Команда не распознана. Используйте /start")
    return 'ok'

if __name__ == '__main__':
    threading.Thread(target=check_spreads, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
