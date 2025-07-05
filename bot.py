import threading
import time
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters

TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857
SPREAD_THRESHOLD = 0.01  # минимальный порог для теста

bot = Bot(token=TOKEN)
app = Flask(__name__)

def get_prices():
    # Пример двух бирж Binance и Bybit для пары BTCUSDT
    try:
        r1 = requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT', timeout=5)
        r2 = requests.get('https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT', timeout=5)
        if r1.status_code == 200 and r2.status_code == 200:
            price_binance = float(r1.json()['price'])
            price_bybit = float(r2.json()['result'][0]['last_price'])
            return price_binance, price_bybit
    except Exception as e:
        print(f"Ошибка при получении цен: {e}")
    return None, None

def monitor_spreads():
    print("▶️ Запущен фоновый мониторинг спредов...")
    while True:
        price_binance, price_bybit = get_prices()
        if price_binance and price_bybit:
            spread = abs(price_binance - price_bybit) / ((price_binance + price_bybit) / 2) * 100
            if spread >= SPREAD_THRESHOLD:
                message = (
                    f"🚨 СПРЕД! BTC/USDT: {spread:.2f}% между "
                    f"[Binance](https://www.binance.com/en/trade/BTC_USDT) и "
                    f"[Bybit](https://www.bybit.com/trade-spot/BTCUSDT)"
                )
                bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='Markdown')
        time.sleep(10)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

def start(update, context):
    update.message.reply_text(
        "Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление."
    )

def test(update, context):
    update.message.reply_text(
        "Тестовое сообщение: спред 0.05% между Binance и Bybit.\n"
        "[Binance](https://www.binance.com/en/trade/BTC_USDT) vs "
        "[Bybit](https://www.bybit.com/trade-spot/BTCUSDT)",
        parse_mode='Markdown'
    )

dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('test', test))

if __name__ == '__main__':
    threading.Thread(target=monitor_spreads, daemon=True).start()
    app.run(host='0.0.0.0', port=10000)
