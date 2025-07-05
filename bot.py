from flask import Flask, request
import requests
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
import threading

TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857
SPREAD_THRESHOLD = 0.1  # 0.1%

app = Flask(__name__)
bot = Bot(token=TOKEN)

def get_binance_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
    data = requests.get(url).json()
    return float(data['bidPrice']), float(data['askPrice'])

def get_bybit_price(symbol):
    url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
    data = requests.get(url).json()
    ticker = data['result'][0]
    return float(ticker['bid_price']), float(ticker['ask_price'])

def check_spread():
    symbols = {
        'BTCUSDT': 'BTC/USDT',
        'ETHUSDT': 'ETH/USDT',
        'SOLUSDT': 'SOL/USDT',
    }

    for symbol, name in symbols.items():
        try:
            bnb_bid, bnb_ask = get_binance_price(symbol)
            byb_bid, byb_ask = get_bybit_price(symbol)

            # Спреды
            spread1 = (byb_bid - bnb_ask) / bnb_ask * 100
            spread2 = (bnb_bid - byb_ask) / byb_ask * 100

            if spread1 > SPREAD_THRESHOLD:
                msg = f"🚨 СПРЕД! {name}: {spread1:.2f}%\nКупить на Binance ({bnb_ask}), продать на Bybit ({byb_bid})\n🔗 https://www.binance.com/en/trade/{symbol.replace('USDT','_USDT')}\n🔗 https://www.bybit.com/trade/usdt/{name.split('/')[0].lower()}"
                bot.send_message(chat_id=CHAT_ID, text=msg)

            if spread2 > SPREAD_THRESHOLD:
                msg = f"🚨 СПРЕД! {name}: {spread2:.2f}%\nКупить на Bybit ({byb_ask}), продать на Binance ({bnb_bid})\n🔗 https://www.bybit.com/trade/usdt/{name.split('/')[0].lower()}\n🔗 https://www.binance.com/en/trade/{symbol.replace('USDT','_USDT')}"
                bot.send_message(chat_id=CHAT_ID, text=msg)

        except Exception as e:
            print(f"[ERROR] {symbol}: {e}")

@app.route('/')
def home():
    return 'Bot is running.'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

def start(update, context):
    update.message.reply_text("Привет! Я мониторю спреды между биржами. Напиши /check для ручной проверки.")

def check(update, context):
    update.message.reply_text("Проверяю спреды...")
    threading.Thread(target=check_spread).start()

# Настройка Telegram диспетчера
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("check", check))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
