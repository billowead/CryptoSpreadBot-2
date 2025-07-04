import asyncio
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))  # обязательно числом

async def spread_job(app):
    # Здесь будет логика проверки спреда
    # Для примера просто отправим тестовое сообщение
    spread = 3.14  # пример значения спреда
    message = f"Спред между BTC и USDT = {spread:.2f}%\nhttps://www.binance.com/en/trade/BTC_USDT\nhttps://www.bybit.com/trade/BTCUSDT"
    try:
        await app.bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Ошибка при отправке сообщения: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен!")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Запускаем периодическую задачу — каждую минуту
    app.job_queue.run_repeating(lambda context: asyncio.create_task(spread_job(app)), interval=60, first=0)

    print("Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()
