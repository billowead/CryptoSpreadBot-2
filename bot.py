import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import asyncio

TOKEN = os.environ.get("TELEGRAM_TOKEN")

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот на webhook.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(update.message.text)

# Обработчики
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# Flask route для webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    asyncio.get_event_loop().create_task(application.process_update(update))
    return "OK"

@app.route("/")
def index():
    return "Hello, this is CryptoSpreadBot webhook server."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    asyncio.get_event_loop().run_until_complete(application.bot.set_webhook(url=webhook_url))
    app.run(host="0.0.0.0", port=port)
