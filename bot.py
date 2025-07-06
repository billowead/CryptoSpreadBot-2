import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHECK_URL = "https://cryptospreadbot-2.onrender.com/check"  # твой URL с Flask

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот готов. Напиши /check, чтобы получить текущие спреды.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = requests.get(CHECK_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "no_spreads":
                await update.message.reply_text("Сейчас нет спредов выше порога.")
            else:
                await update.message.reply_text(f"Отправлено {data.get('count')} сообщений.")
        else:
            await update.message.reply_text("Ошибка при обращении к серверу.")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check))

app.run_polling()
