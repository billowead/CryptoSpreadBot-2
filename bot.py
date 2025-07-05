from flask import Flask, request
import threading
import time
import requests

app = Flask(__name__)

TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = '593059857'

def send_message(text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f'Ошибка отправки сообщения: {e}')

def monitor_spreads():
    while True:
        try:
            print("Проверяем спреды...")

            # Пример заглушки — сюда вставь реальный запрос к биржам
            binance_price = 30000  # заменить на API Binance
            bybit_price = 30100    # заменить на API Bybit

            spread = abs(bybit_price - binance_price) / binance_price
            threshold = 0.001  # 0.1%

            if spread >= threshold:
                msg = (f"🚨 СПРЕД! {spread*100:.2f}% между Binance и Bybit\n"
                       f"<b>Binance:</b> {binance_price} USD\n"
                       f"<b>Bybit:</b> {bybit_price} USD\n"
                       f"<a href='https://www.binance.com/en/trade/BTC_USDT'>Binance BTC/USDT</a>\n"
                       f"<a href='https://www.bybit.com/trade/btc-usdt'>Bybit BTC/USDT</a>")
                send_message(msg)

        except Exception as e:
            print(f'Ошибка в мониторинге: {e}')

        time.sleep(30)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print('Получены данные:', data)

    if 'message' in data and 'text' in data['message']:
        text = data['message']['text']
        chat_id = data['message']['chat']['id']

        if text == '/start':
            send_message("Привет! Я мониторю спреды между биржами и сообщу, когда будет больше порога.")
    return 'ok'

if __name__ == '__main__':
    monitor_thread = threading.Thread(target=monitor_spreads, daemon=True)
    monitor_thread.start()

    app.run(host='0.0.0.0', port=10000)
