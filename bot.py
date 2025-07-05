from flask import Flask, request
import requests
import threading
import time

app = Flask(__name__)

TELEGRAM_TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857
THRESHOLD = 1.0  # порог спреда в процентах
CHECK_INTERVAL = 30  # интервал проверки в секундах

# Последний отправленный спред, чтобы не слать одинаковые уведомления слишком часто
last_alert = {}

def send_telegram_message(chat_id, text, parse_mode=None):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text,
    }
    if parse_mode:
        data['parse_mode'] = parse_mode
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Ошибка отправки сообщения:", e)

def get_binance_price(pair):
    symbol = pair.replace('/', '').upper()  # BTCUSDT
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return float(r.json()['price'])
    except Exception as e:
        print("Ошибка Binance API:", e)
    return None

def get_bybit_price(pair):
    symbol = pair.replace('/', '').upper()
    url = f'https://api.bybit.com/v2/public/tickers?symbol={symbol}'
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        if r.status_code == 200 and data.get('ret_msg') == 'OK':
            return float(data['result'][0]['last_price'])
    except Exception as e:
        print("Ошибка Bybit API:", e)
    return None

def calculate_spread(price1, price2):
    if price1 is None or price2 is None:
        return None
    return abs(price1 - price2) / min(price1, price2) * 100

def send_spread_alert(pair, spread, exchange1, price1, exchange2, price2):
    global last_alert
    key = f"{pair}_{exchange1}_{exchange2}"
    # Чтобы не спамить, отправляем только если изменился спред или прошло 10 минут
    now = time.time()
    if key in last_alert:
        last_spread, last_time = last_alert[key]
        if abs(spread - last_spread) < 0.1 and (now - last_time) < 600:
            return
    last_alert[key] = (spread, now)

    msg = (
        f"🚨 СПРЕД!\n"
        f"{pair}: {spread:.2f}% между "
        f"[{exchange1}](https://www.binance.com/en/trade/{pair.replace('/', '_')}) (цена {price1}) и "
        f"[{exchange2}](https://www.bybit.com/trade/{pair.replace('/', '')}) (цена {price2})"
    )
    send_telegram_message(CHAT_ID, msg, parse_mode="Markdown")

def monitor_spread():
    pair = 'BTC/USDT'
    while True:
        price_binance = get_binance_price(pair)
        price_bybit = get_bybit_price(pair)

        if price_binance and price_bybit:
            spread = calculate_spread(price_binance, price_bybit)
            if spread and spread >= THRESHOLD:
                send_spread_alert(pair, spread, 'Binance', price_binance, 'Bybit', price_bybit)
        else:
            print("Не удалось получить цены для пары", pair)
        
        time.sleep(CHECK_INTERVAL)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    # Можно сюда добавить обработку команд, например /start
    return 'OK'

if __name__ == '__main__':
    threading.Thread(target=monitor_spread, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
