import logging
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Логирование
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'

application = Application.builder().token(TOKEN).build()

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает!")

application.add_handler(CommandHandler("start", start))

@app.route(f'/{TOKEN}', methods=["POST"])
def webhook():
    update_data = request.get_json(force=True)
    update = Update.de_json(update_data, application.bot)

    async def handle_update():
        await application.initialize()  # Важно!
        await application.process_update(update)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(handle_update())
    return "ok"

@app.route('/')
def home():
    return 'Crypto Spread Bot работает.'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
