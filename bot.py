import threading
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Твой токен Telegram-бота
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"

def check_spreads():
    while True:
        print("Проверяем спреды...")  # Здесь должна быть твоя логика
        time.sleep(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и готов к работе!")

if __name__ == "__main__":
    threading.Thread(target=check_spreads, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Бот запущен")
    app.run_polling()
