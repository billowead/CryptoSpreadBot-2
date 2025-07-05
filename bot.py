import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
from telegram.constants import ParseMode
from telegram.error import Conflict

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация (ВСТАВЬТЕ СВОИ ЗНАЧЕНИЯ!)
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"  # Обязательно в одной строке!
CHAT_ID = "593059857"

class SafeBot:
    def __init__(self):
        self.app = None
        self.should_stop = False

    async def initialize(self):
        """Инициализация с защитой от конфликтов"""
        try:
            self.app = Application.builder().token(TOKEN).build()
            self.app.add_handler(CommandHandler("start", self.start))
            self.app.add_handler(CommandHandler("check", self.check_prices))
            return True
        except Conflict:
            logger.error("Обнаружен запущенный экземпляр бота. Остановите другие процессы.")
            return False

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /start"""
        await update.message.reply_text(
            "🤖 Бот мониторинга спреда активен!\n"
            "Используйте /check для проверки цен"
        )

    async def check_prices(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка /check"""
        try:
            # Получаем цены с KuCoin
            async with httpx.AsyncClient() as client:
                kucoin_resp = await client.get(
                    "https://api.kucoin.com/api/v1/market/orderbook/level1",
                    params={"symbol": "BTC-USDT"},
                    timeout=10
                )
                kucoin_price = float(kucoin_resp.json()["data"]["price"])

                # Получаем цены с MEXC
                mexc_resp = await client.get(
                    "https://api.mexc.com/api/v3/ticker/price",
                    params={"symbol": "BTCUSDT"},
                    timeout=10
                )
                mexc_price = float(mexc_resp.json()["price"])

            # Расчет спреда
            spread = abs(kucoin_price - mexc_price)
            spread_percent = (spread / ((kucoin_price + mexc_price)/2)) * 100

            await update.message.reply_text(
                f"📊 BTC/USDT:\n"
                f"KuCoin: {kucoin_price:.2f}\n"
                f"MEXC: {mexc_price:.2f}\n"
                f"🔹 Спред: {spread_percent:.2f}%",
                parse_mode=ParseMode.MARKDOWN
            )

        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
            await update.message.reply_text("⚠️ Ошибка при получении данных")

    async def run(self):
        """Запуск бота с защитой от конфликтов"""
        try:
            if not await self.initialize():
                return

            logger.info("Бот успешно запущен")
            await self.app.run_polling(
                close_loop=False,
                stop_signals=None
            )
        except Exception as e:
            logger.error(f"Фатальная ошибка: {str(e)}")
        finally:
            logger.info("Бот остановлен")

def main():
    bot = SafeBot()
    
    # Создаем новую event loop для Render
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(bot.run())
    finally:
        loop.close()

if __name__ == "__main__":
    main()
