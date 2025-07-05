import logging
import asyncio
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

# Конфигурация
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"

# Создаем Application
app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🔄 Бот работает!\n"
        "Я буду присылать уведомления о спредах между биржами.\n"
        "Проверить сейчас: /check"
    )

async def check_prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка цен по команде /check"""
    try:
        # Получаем цены BTC-USDT с KuCoin и MEXC
        async with httpx.AsyncClient() as client:
            # KuCoin
            kucoin_resp = await client.get(
                "https://api.kucoin.com/api/v1/market/orderbook/level1",
                params={"symbol": "BTC-USDT"},
                timeout=10
            )
            kucoin_price = float(kucoin_resp.json()["data"]["price"])
            
            # MEXC
            mexc_resp = await client.get(
                "https://api.mexc.com/api/v3/ticker/price",
                params={"symbol": "BTCUSDT"},
                timeout=10
            )
            mexc_price = float(mexc_resp.json()["price"])
            
        # Рассчитываем спред
        spread = abs(kucoin_price - mexc_price)
        spread_percent = (spread / ((kucoin_price + mexc_price)/2)) * 100
        
        # Отправляем результат
        message = (
            f"📊 BTC-USDT:\n"
            f"KuCoin: {kucoin_price:.2f}\n"
            f"MEXC: {mexc_price:.2f}\n"
            f"Спред: {spread_percent:.2f}%"
        )
        
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        await update.message.reply_text("⚠️ Ошибка при получении данных")

# Регистрируем обработчики команд
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check_prices))

def main():
    """Запуск бота"""
    logger.info("Starting bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
