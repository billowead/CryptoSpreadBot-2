import asyncio
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import httpx

BOT_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857

app = FastAPI()

# Инициализация бота и приложения python-telegram-bot
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Пример функции для получения спредов с бирж (замени на реальную логику)
async def get_spreads():
    # Пример - возвращаем фиктивные данные
    spreads = [
        {
            "pair": "BTC/USDT",
            "spread": "3.2%",
            "link_binance": "https://www.binance.com/en/trade/BTC_USDT",
            "link_bybit": "https://www.bybit.com/en-US/trade/spot/BTCUSDT"
        },
        {
            "pair": "ETH/USDT",
            "spread": "2.7%",
            "link_binance": "https://www.binance.com/en/trade/ETH_USDT",
            "link_bybit": "https://www.bybit.com/en-US/trade/spot/ETHUSDT"
        },
    ]
    return spreads

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, который шлёт спреды между биржами.")

application.add_handler(CommandHandler("start", start))

# Модель для входящего webhook
class UpdateModel(BaseModel):
    update_id: int
    message: dict = None
    # остальные поля можно добавить при необходимости

@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# Функция отправки спредов в чат
async def send_spreads():
    spreads = await get_spreads()
    bot = Bot(token=BOT_TOKEN)
    for spread in spreads:
        text = (
            f"Спред для {spread['pair']}: {spread['spread']}\n"
            f"Binance: {spread['link_binance']}\n"
            f"Bybit: {spread['link_bybit']}"
        )
        await bot.send_message(chat_id=CHAT_ID, text=text)

# Задача, которая будет запускать отправку спредов раз в N секунд
async def periodic_spread_sender():
    while True:
        try:
            await send_spreads()
        except Exception as e:
            print("Ошибка при отправке спредов:", e)
        await asyncio.sleep(60)  # интервал в секундах, например 60

# Запуск периодической задачи при старте сервера
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_spread_sender())
