import threading
import time
import requests
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler

TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857
SPREAD_THRESHOLD = 0.1  # Порог спреда для уведомления

bot = Bot(token=TOKEN)
app = Flask(__name__)
dispatcher = Dispatcher(bot=bot, update_queue=None, use_context=True)

# Список бирж и их API
EXCHANGES = {
    "Binance": "https://api.binance.com/api/v3/ticker/price?symbol={pair}",
    "Bybit": "https://api.bybit.com/v2/public/tickers?symbol={pair}",
}

# Преобразование названий валют в API формат
PAIR_MAP = {
    "BTC/USDT": {"Binance": "BTCUSDT", "Bybit": "BTCUSDT"},
    "ETH/USDT": {"Binance": "ETHUSDT", "Bybit": "ETHUSDT"},
}

def get_price(exchange, pair):
    try:
        if exchange == "Binance":
            url = EXCHANGES[exchange].format(pair=PAIR_MAP[pair][exchange])
            r = requests.get(url, timeout=5)
            return float(r.json()["price"])
        elif exchange == "Bybit":
            url = EXCHANGES[exchange].format(pair=PAIR_MAP[pair][exchange])
            r = requests.get(url, timeout=5)
            data = r.json()["result"]
            for item in data:
                if item["symbol"] == PAIR_MAP[pair][exchange]:
                    return float(item["last_price"])
    except Exception as e:
        print(f"Error getting price from {exchange}: {e}")
        return None

def monitor_spreads():
    print("▶️ Запущен фоновый мониторинг спредов...")
    while True:
        for pair in PAIR_MAP:
            prices = {}
            for exchange in EXCHANGES:
                price = get_price(exchange, pair)
                if price:
                    prices[exchange] = price
            if len(prices) >= 2:
                min_ex = min(prices, key=prices.get)
                max_ex = max(prices, key=prices.get)
                spread = ((prices[max_ex] - prices[min_ex]) / prices[min_ex]) * 100
                if spread >= SPREAD_THRESHOLD:
                    msg = f"🚨 СПРЕД! {pair}: {spread:.2f}% между {min_ex} и {max_ex}\n"
                    msg += f"{min_ex}: {prices[min_ex]} → [ссылка](https://www.google.com/search?q={min_ex}+{pair.replace('/', '')})\n"
                    msg += f"{max_ex}: {prices[max_ex]} → [ссылка](https://www.google.com/search?q={max_ex}+{pair.replace('/', '')})"
                    bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
        time.sleep(10)  # Проверять каждые 10 секунд

def start(update, context):
    update.message.reply_text("Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление.")

dispatcher.add_handler(CommandHandler("start", start))

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return 'ok'

@app.route('/')
def index():
    return "Crypto Spread Bot is running."

if __name__ == '__main__':
    # Запускаем фоновый поток
    thread = threading.Thread(target=monitor_spreads)
    thread.daemon = True
    thread.start()

    # Запускаем Flask
    app.run(host="0.0.0.0", port=10000)
