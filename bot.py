import requests
from flask import Flask, request
from telegram import Bot

TELEGRAM_TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

def get_price_coingecko():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        price = r.json()['bitcoin']['usd']
        print(f"[Coingecko] BTC price: {price}")
        return float(price)
    except Exception as e:
        print(f"CoinGecko API error: {e}")
        return None

def get_price_binance():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        price = float(r.json()['price'])
        print(f"[Binance] BTC price: {price}")
        return price
    except Exception as e:
        print(f"Binance API error: {e}")
        return None

def monitor_spread_once():
    THRESHOLD = 0.005  # 0.5%
    price1 = get_price_coingecko()
    price2 = get_price_binance()
    if price1 is None or price2 is None:
        print("❌ Ошибка получения цен, пропускаем.")
        return

    spread = abs(price1 - price2) / ((price1 + price2) / 2)
    spread_percent = spread * 100
    print(f"🔎 Спред: {spread_percent:.3f}%")

    if spread >= THRESHOLD:
        msg = (
            f"🚨 СПРЕД! BTC:\n"
            f"{spread_percent:.2f}% между Coingecko и Binance\n"
            f"Цены:\nCoingecko: {price1}\nBinance: {price2}\n"
            f"<a href='https://www.binance.com/en/trade/BTC_USDT'>Binance</a>"
        )
        try:
            bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
            print("✅ Уведомление отправлено.")
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
    else:
        print("📉 Спред ниже порога, уведомление не отправлено.")

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    print("📩 Обновление получено:", update)
    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        text = update['message']['text']
        if text == '/start':
            bot.send_message(chat_id=chat_id, text="Привет! Я мониторю спред между биржами. Жди сигналов!")
    return 'ok'

@app.route('/check', methods=['GET'])
def check():
    print("🔁 Ручная проверка /check вызвана")
    monitor_spread_once()
    return 'Checked', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
