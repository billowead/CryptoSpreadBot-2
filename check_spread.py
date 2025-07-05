import os
import time
import logging
from flask import Flask

from telegram import Bot

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

def check_spread():
    logging.info("Запуск проверки спреда...")
    # Тут можно просто заглушку для теста
    spread = 0.05  # пример, 5%
    logging.info(f"Текущий спред: {spread}")
    if spread > 0.03:
        msg = f"Внимание! Спред большой: {spread*100:.2f}%"
        logging.info(f"Отправляем сообщение: {msg}")
        try:
            bot.send_message(chat_id=CHAT_ID, text=msg)
            logging.info("Сообщение успешно отправлено!")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения: {e}")

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    logging.info("Старт сервера и мониторинга...")

    # Запускаем сервер в отдельном потоке, а проверку в главном цикле
    from threading import Thread

    def run_flask():
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10001)))

    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Главный цикл с проверкой спреда каждую минуту
    while True:
        check_spread()
        time.sleep(60)
