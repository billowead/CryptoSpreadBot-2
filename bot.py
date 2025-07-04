import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))  # Важно: числовой ID, а не username

async def spread_job(app):
    # Здесь должна быть реальная логика проверки спреда
    spread = 3.62  # пример спреда
    message = (
        f"Спред между BTC и USDT = {spread:.2f}%\n"
        "Binance: https://www.binance.com/en/trade/BTC_USDT\n"
        "Bybit: https://www.bybit.com/trade/BTCUSDT"
    )
    try:
        await app.bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот запущен и готов к работе!")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).jobs(True).build()

    # Обработчик команды /start
    app.add_handler(CommandHandler("start", start))

    # Запускаем задачу с интервалом 60 секунд
    app.job_queue.run_repeating(lambda ctx: asyncio.create_task(spread_job(app)), interval=60, first=0)

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
