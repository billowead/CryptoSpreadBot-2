import os
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler
import asyncio
from aiohttp import web

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))

bot = Bot(token=TELEGRAM_TOKEN)

async def start(update: Update, context):
    await update.message.reply_text('Бот запущен и работает!')

async def run_bot():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()

async def handle_health(request):
    return web.Response(text="OK")

async def main():
    port = int(os.getenv('PORT', 8000))

    # Запускаем телеграм-бота в фоне
    asyncio.create_task(run_bot())

    # Запускаем HTTP-сервер для Render health check
    app = web.Application()
    app.router.add_get('/health', handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    print(f'Server started on port {port}')
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
