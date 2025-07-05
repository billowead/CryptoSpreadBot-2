import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")  # Возьми токен из переменных окружения Render

app = Flask(__name__)
bot = Bot(token=TOKEN)

# Создаем Application (замена Dispatcher)
application = ApplicationBuilder().token(TOKEN).build()

# Асинхронные обработчики в новой версии
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот на webhook.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    # Обработка update синхронно через asyncio
    import asyncio
    asyncio.run(application.process_update(update))
    return "OK"

@app.route("/")
def index():
    return "Hello, this is CryptoSpreadBot webhook server."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    bot.set_webhook(f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    app.run(host="0.0.0.0", port=port)
