import requests
import threading
import time
from flask import Flask, request
from telegram import Bot

# --- Настройки ---
TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'  # твой токен Telegram-бота
CHAT_ID = 593059857  # твой chat_id в Telegram
PORT = 10000
threshold = 0.01  # порог спреда 1% (0.01)

# Пары для мониторинга
pairs = ['BTC/USDT', 'ETH/USDT']

# Биржи и их API для получения цены (Binance и Bybit)
exchanges = {
    'Binance': 'https://api.binance.com/api/v3/ticker/price?symbol=',
    'Bybit': 'https://api.bybit.com/v2/public/tickers?symbol='
}

app = Flask(__name__)
bot = Bot(token=TOKEN)

def get_ticker(url, pair):
    symbol = pair.replace('/', '')
    try:
        if 'binance' in url:
            r = requests.get(url + symbol)
            r.raise_for_status()
            data = r.json()
            return float(data['price'])
        elif 'bybit' in url:
            r = requests.get(url + symbol)
            r.raise_for_status()
            data = r.json()
            if data['ret_msg'] == 'OK' and data['result']:
                return float(data['result'][0]['last_price'])
            else:
                return None
    except Exception as e:
        print(f"Ошибка запроса {url} для {pair}: {e}")
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
            try:
                prices = {}
                for exchange, url in exchanges.items():
                    price = get_ticker(url, pair)
                    if price is not None:
                        prices[exchange] = price
                if len(prices) < 2:
                    print(f"Мало данных для {pair}, пропускаю")
                    continue

                # Сравниваем все пары бирж
                for ex1 in prices:
                    for ex2 in prices:
                        if ex1 == ex2:
                            continue
                        price1 = prices[ex1]
                        price2 = prices[ex2]
                        spread = abs(price1 - price2) / min(price1, price2)
                        spread_percent = spread * 100
                        print(f"Спред {pair} между {ex1} и {ex2}: {spread_percent:.4f}% (цены {price1} / {price2})")

                        if spread >= threshold:
                            msg = (f"🚨 <b>СПРЕД!</b> {pair}: {spread_percent:.2f}% между {ex1} и {ex2}\n"
                                   f"<a href='https://www.{ex1.lower()}.com/trade/{symbol_to_url(pair)}'>{ex1}</a>\n"
                                   f"<a href='https://www.{ex2.lower()}.com/trade/{symbol_to_url(pair)}'>{ex2}</a>")
                            send_message(msg)

            except Exception as e:
                print(f"Ошибка при проверке {pair}: {e}")

        time.sleep(60)  # пауза 60 секунд между проверками

def symbol_to_url(pair):
    # Преобразуем BTC/USDT -> btcusdt для ссылки
    return pair.replace('/', '').lower()

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if 'message' in update:
        chat_id = update['message']['chat']['id']
        text = update['message'].get('text', '')

        if text == '/start':
            send_message("Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление.")
        else:
            send_message("Команда не распознана. Используйте /start")
    return 'ok'

if __name__ == '__main__':
    threading.Thread(target=check_spreads, daemon=True).start()
    app.run(host='0.0.0.0', port=PORT)
