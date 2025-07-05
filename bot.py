import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
from telegram.constants import ParseMode

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация (используем ваш токен в правильном формате)
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"  # Обратите внимание - токен должен быть в одной строке
CHAT_ID = "593059857"  # Ваш chat_id

# Создаем Application
app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "✅ Бот успешно запущен!\n"
        "Используйте /check для проверки текущего спреда"
    )

async def check_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка цен по команде /check"""
    try:
        # Получаем цены BTC-USDT с KuCoin
        async with httpx.AsyncClient() as client:
            kucoin_resp = await client.get(
                "https://api.kucoin.com/api/v1/market/orderbook/level1",
                params={"symbol": "BTC-USDT"},
                timeout=10
            )
            kucoin_price = float(kucoin_resp.json()["data"]["price"])
            
            # Получаем цены BTC-USDT с MEXC
            mexc_resp = await client.get(
                "https://api.mexc.com/api/v3/ticker/price",
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            mexc_price = float(mexc_resp.json()["price"])
        
        # Рассчитываем спред
        spread = abs(kucoin_price - mexc_price)
        spread_percent = (spread / ((kucoin_price + mexc_price)/2)) * 100
        
        # Формируем сообщение
        message = (
            f"📊 Текущие цены BTC-USDT:\n"
            f"• KuCoin: {kucoin_price:.2f} $\n"
            f"• MEXC: {mexc_price:.2f} $\n"
            f"🔹 Разница: {spread:.2f} $ ({spread_percent:.2f}%)"
        )
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Ошибка при проверке цен: {str(e)}")
        await update.message.reply_text("⚠️ Произошла ошибка при получении данных")

# Регистрируем обработчики команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check_prices))

def main():
    """Запуск бота"""
    logger.info("Бот запускается...")
    app.run_polling()

if __name__ == "__main__":
    main()
