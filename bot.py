import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))  # В .env должно быть число

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и работает!")

async def spread_job(app):
    while True:
        message = "Спред между BTC и USDT = 3.62% (пример)"
        try:
            await app.bot.send_message(chat_id=CHAT_ID, text=message)
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
        await asyncio.sleep(60)  # Ждём 60 секунд

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Запускаем задачу спреда в фоне
    asyncio.create_task(spread_job(app))

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
