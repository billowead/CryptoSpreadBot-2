import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Ваши данные
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"  # Ваш chat_id
CHECK_INTERVAL = 60  # Проверка каждые 60 секунд

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpreadMonitor:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.running = False
        self.task = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.running:
            await update.message.reply_text("Мониторинг уже запущен!")
            return

        self.running = True
        self.task = asyncio.create_task(self.monitor_spread())
        await update.message.reply_text(
            "🚀 Бот мониторинга спреда активирован!\n"
            "Я буду присылать уведомления, когда спред между биржами превысит 2%.\n"
            "Команды:\n"
            "/check - проверить сейчас\n"
            "/stop - остановить мониторинг"
        )

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.running:
            await update.message.reply_text("Мониторинг уже остановлен")
            return

        self.running = False
        self.task.cancel()
        await update.message.reply_text("🛑 Мониторинг остановлен")

    async def check_now(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Проверяю спред...")
        await self.check_spread()

    async def get_price(self, exchange):
        try:
            async with httpx.AsyncClient() as client:
                if exchange == "binance":
                    r = await client.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
                    return float(r.json()["price"])
                elif exchange == "bybit":
                    r = await client.get("https://api.bybit.com/v2/public/tickers?symbol=BTCUSD")
                    return float(r.json()["result"][0]["last_price"])
        except Exception as e:
            logger.error(f"Ошибка {exchange}: {str(e)}")
            return None

    async def check_spread(self):
        binance_price = await self.get_price("binance")
        bybit_price = await self.get_price("bybit")

        if binance_price and bybit_price:
            spread = abs(binance_price - bybit_price)
            spread_percent = (spread / ((binance_price + bybit_price)/2)) * 100

            if spread_percent >= 2:
                msg = (
                    f"🚨 Спред {spread_percent:.2f}%\n"
                    f"Binance: {binance_price:.2f} USD\n"
                    f"Bybit: {bybit_price:.2f} USD\n"
                    f"Разница: {spread:.2f} USD"
                )
                await self.bot.send_message(chat_id=CHAT_ID, text=msg)

    async def monitor_spread(self):
        while self.running:
            try:
                await self.check_spread()
                await asyncio.sleep(CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка мониторинга: {str(e)}")
                await asyncio.sleep(10)

async def main():
    monitor = SpreadMonitor()
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", monitor.start))
    app.add_handler(CommandHandler("stop", monitor.stop))
    app.add_handler(CommandHandler("check", monitor.check_now))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
