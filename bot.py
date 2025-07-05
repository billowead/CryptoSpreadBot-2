import threading
import time
from flask import Flask, request
from telegram import Bot

# Твои данные:
TELEGRAM_TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857

bot = Bot(token=TELEGRAM_TOKEN)
app = Flask(__name__)

def check_spread():
    print("▶️ Фоновая проверка запущена")
    count = 0
    while True:
        print(f"Проверка #{count}")
        # Тут позже можно вставить свою логику мониторинга спреда
        count += 1
        time.sleep(10)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    print("Получено обновление:", update)
    if 'message' in update and 'text' in update['message']:
        chat_id = update['message']['chat']['id']
        text = update['message']['text']

        if text == '/start':
            bot.send_message(chat_id=chat_id, text="Привет! Я мониторю спреды между биржами. Как только спред будет выше порога, я пришлю уведомление.")
    return 'ok'

if __name__ == '__main__':
    threading.Thread(target=check_spread, daemon=True).start()
    app.run(host='0.0.0.0', port=10000, threaded=True)
