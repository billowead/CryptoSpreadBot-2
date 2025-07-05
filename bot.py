from flask import Flask, request
import requests

app = Flask(__name__)

# 🔐 Твой токен и chat_id
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"

# 👉 Функция отправки сообщений
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=payload)

# ✅ Проверка, что бот жив
@app.route("/", methods=["GET"])
def index():
    return "✅ Бот жив. Всё работает!"

# 🔁 Основной webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    spread = 3.25  # Тестовое значение
    message = f"🚨 СПРЕД! BTC/USDT: {spread:.2f}% между Binance и Bybit"
    send_telegram_message(message)
    return "✅ Spread отправлен!"

# 🔃 Чтобы Render знал, что надо запускать
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
