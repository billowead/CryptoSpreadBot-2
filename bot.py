import logging
from flask import Flask, request, abort
from telegram import Bot, Update
from telegram.ext import Dispatcher, CommandHandler
import asyncio
import threading
import httpx

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857  # Твой chat_id

app = Flask(__name__)
bot = Bot(token=TOKEN)
dispatcher = Dispatcher(bot, None, workers=0, use_context=True)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Пример функции, которая отправляет спреды с бирж с ссылками
async def fetch_spreads_and_send():
    # Пример - замени реальным API и логикой
    spreads = [
        {"pair": "BTC/USDT", "spread": 2.5, "exchange1": "Binance", "exchange2": "Bybit",
         "url1": "https://www.binance.com/en/trade/BTC_USDT",
         "url2": "https://www.bybit.com/en-US/trade/spot/BTCUSDT"},
        {"pair": "ETH/USDT", "spread": 3.1, "exchange1": "Binance", "exchange2": "Bybit",
         "url1": "https://www.binance.com/en/trade/ETH_USDT",
         "url2": "https://www.bybit.com/en-US/trade/spot/ETHUSDT"},
    ]

    for s in spreads:
        text = (
            f"Спред {s['pair']}: {s['spread']}%\n"
            f"{s['exchange1']}: {s['url1']}\n"
            f"{s['exchange2']}: {s['url2']}\n"
        )
        await bot.send_message(chat_id=CHAT_ID, text=text)

# Запускаем периодическую задачу в отдельном потоке (пример: раз в 5 минут)
def schedule_spreads():
    import time
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    while True:
        loop.run_until_complete(fetch_spreads_and_send())
        time.sleep(300)  # 5 минут

# Запуск фонового потока с периодическими сообщениями
threading.Thread(target=schedule_spreads, daemon=True).start()

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        dispatcher.process_update(update)
        return "OK"
    else:
        abort(403)

@app.route('/')
def index():
    return "Bot is running"

if __name__ == '__main__':
    # Для Render нужно слушать 0.0.0.0 и порт из переменной окружения PORT
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
