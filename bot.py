import asyncio
from telegram import Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройки
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
SPREAD_THRESHOLD = 2.0  # в процентах

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Список бирж и криптопар (для примера)
EXCHANGES = ["binance", "bybit"]
PAIRS = ["BTC/USDT", "ETH/USDT"]

# Мнимые данные — заменить на реальный API запрос
async def get_mock_prices():
    return {
        "BTC/USDT": {"binance": 30000, "bybit": 30600},
        "ETH/USDT": {"binance": 1800, "bybit": 1836},
    }

async def check_spreads(context: ContextTypes.DEFAULT_TYPE):
    prices = await get_mock_prices()
    messages = []

    for pair, exchanges in prices.items():
        if len(exchanges) < 2:
            continue
        prices_list = list(exchanges.items())
        for i in range(len(prices_list)):
            for j in range(i + 1, len(prices_list)):
                ex1, price1 = prices_list[i]
                ex2, price2 = prices_list[j]
                spread = abs(price1 - price2) / ((price1 + price2) / 2) * 100
                if spread >= SPREAD_THRESHOLD:
                    msg = f"🚨 {pair}:\n{ex1}: {price1}$\n{ex2}: {price2}$\n📊 Spread: {spread:.2f}%"
                    messages.append(msg)

    if messages:
        for msg in messages:
            await context.bot.send_message(chat_id=CHAT_ID, text=msg)

async def start(update, context):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Бот запущен и отслеживает спреды!")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Команда /start
    app.add_handler(CommandHandler("start", start))

    # Планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_spreads, "interval", seconds=30, args=[ContextTypes.DEFAULT_TYPE(bot=Bot(TOKEN))])
    scheduler.start()

    app.run_polling()

if __name__ == "__main__":
    main()
