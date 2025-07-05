import os
import asyncio
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и работает!")

async def spread_job(context: ContextTypes.DEFAULT_TYPE):
    message = "Пример спреда: BTC/USDT = 3.62%"
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.job_queue.run_repeating(spread_job, interval=60, first=0)

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
