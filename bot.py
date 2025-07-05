import logging
import os
import json
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Flask-приложение
app = Flask(__name__)

# Токен бота
TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'

# Telegram Application (бот)
application = Application.builder().token(TOKEN).build()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает!")

application.add_handler(CommandHandler("start", start))

# Вебхук
@app.route(f'/{TOKEN}', methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)

        # Создаем и запускаем асинхронную задачу в новом event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.process_update(update))
        return "ok"

# Главная страница
@app.route('/')
def home():
    return 'Crypto Spread Bot работает.'

# Запуск
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
