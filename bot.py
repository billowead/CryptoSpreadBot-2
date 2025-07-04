import os
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))  # Убедись, что это число!

# Пример пар
pairs = [
    ('BTC', 'USDT'),
    ('ETH', 'USDT'),
]

# Заглушка спреда
import random
def check_spread(pair):
    return random.uniform(0, 5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Бот запущен!')

async def spread_job(app):
    while True:
        for base, quote in pairs:
            spread = check_spread((base, quote))
            if spread > 2:
                message = f"Спред между {base} и {quote} = {spread:.2f}%\n" \
                          f"https://www.binance.com/en/trade/{base}_{quote}\n" \
                          f"https://www.bybit.com/trade/{base}{quote}"
                await app.bot.send_message(chat_id=CHAT_ID, text=message)
        await asyncio.sleep(60)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler('start', start))

    # Запускаем задачу по рассылке спредов
    app.job_queue.run_repeating(lambda _: asyncio.create_task(spread_job(app)), interval=60, first=0)

    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
