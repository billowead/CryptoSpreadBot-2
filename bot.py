import logging
import asyncio
from flask import Flask, request
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Настрой логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857  # твой чат ID

app = Flask(__name__)

application = ApplicationBuilder().token(TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает!")

application.add_handler(CommandHandler("start", start))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.create_task(application.process_update(update))
    return "ok"

# Функция для проверки спреда и отправки сообщений
async def check_spreads():
    while True:
        try:
            async with httpx.AsyncClient() as client:
                resp_binance = await client.get(
                    'https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT'
                )
                resp_bybit = await client.get(
                    'https://api.bybit.com/v2/public/tickers?symbol=BTCUSDT'
                )

            price_binance = float(resp_binance.json()['price'])
            price_bybit = float(resp_bybit.json()['result'][0]['last_price'])

            spread = abs(price_binance - price_bybit) / ((price_binance + price_bybit) / 2) * 100

            logging.info(f"Binance: {price_binance}, Bybit: {price_bybit}, Spread: {spread:.2f}%")

            if spread > 2:  # порог спреда в %
                text = (
                    f"⚠️ Спред BTCUSDT: {spread:.2f}% ⚠️\n\n"
                    f"Binance: https://www.binance.com/en/trade/BTC_USDT\n"
                    f"Bybit: https://www.bybit.com/trade/btcusdt\n"
                    f"Binance цена: {price_binance}\n"
                    f"Bybit цена: {price_bybit}"
                )
                await application.bot.send_message(chat_id=CHAT_ID, text=text)

        except Exception as e:
            logging.error(f"Ошибка при проверке спредов: {e}")

        await asyncio.sleep(60)  # проверять каждую минуту

if __name__ == "__main__":
    # Запускаем проверку спредов в фоне
    loop = asyncio.get_event_loop()
    loop.create_task(check_spreads())

    # Запускаем Flask сервер для вебхуков
    app.run(host="0.0.0.0", port=10000)
