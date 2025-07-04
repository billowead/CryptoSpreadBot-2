import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))  # Убедись, что в .env это число

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и работает!")

async def spread_job(context: ContextTypes.DEFAULT_TYPE):
    # Тут должна быть логика проверки спреда
    # Для примера просто отправим сообщение
    message = "Спред между BTC и USDT = 3.62% (пример)"
    await context.bot.send_message(chat_id=CHAT_ID, text=message)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Запускаем задачу с интервалом 60 секунд
    job_queue = app.job_queue
    job_queue.run_repeating(spread_job, interval=60, first=0)

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
