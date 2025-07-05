import os
import time
import threading
import requests
from flask import Flask, request

app = Flask(__name__)

# Telegram bot credentials
BOT_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
WEBHOOK_URL = "https://cryptospreadbot-2.onrender.com/webhook"

# Порог спреда для сигнала (в процентах)
SPREAD_THRESHOLD = 2.0

def get_mock_prices():
    # Здесь можно подключить реальные биржи, а пока — тестовые данные
    return {
        "BTC/USDT": {"binance": 30000, "bybit": 30800},
        "ETH/USDT": {"binance": 2000, "bybit": 2045},
        "SOL/USDT": {"binance": 140, "bybit": 139},
    }

def calculate_spread(price1, price2):
    if price1 == 0:
        return 0
    return abs(price1 - price2) / price1 * 100

def check_spreads():
    while True:
        prices = get_mock_prices()
        for pair, data in prices.items():
            binance_price = data.get("binance")
            bybit_price = data.get("bybit")
            spread = calculate_spread(binance_price, bybit_price)
            if spread >= SPREAD_THRESHOLD:
                message = f"📈 Спред по паре *{pair}* превысил {SPREAD_THRESHOLD}%\n"
                message += f"Binance: `{binance_price}`\nBybit: `{bybit_price}`\n"
                message += f"Спред: *{spread:.2f}%*"
                send_telegram_message(message)
        time.sleep(30)

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data and "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_telegram_message("🤖 Бот для отслеживания спреда между биржами запущен.")
    return "ok"

def set_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    requests.post(url, json={"url": WEBHOOK_URL})

if __name__ == "__main__":
    set_webhook()
    threading.Thread(target=check_spreads, daemon=True).start() за
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
