import os
import time
import requests
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

# Список пар для отслеживания (пример)
pairs = [
    ('BTC', 'USDT'),
    ('ETH', 'USDT'),
    ('DOGE', 'USDT'),
    ('LTC', 'USDT'),
    ('BTC', 'DOGE'),
    ('ETH', 'DOGE'),
    ('LTC', 'BTC'),
    ('DOGE', 'ETH')
]

# Заглушка для проверки спреда (тут позже можно добавить логику с реальными API бирж)
def check_spread(pair):
    # Для примера случайное число
    import random
    spread = random.uniform(0, 5)
    return spread

def main():
    while True:
        for base, quote in pairs:
            spread = check_spread((base, quote))
            if spread > 2:  # если спред больше 2%
                message = f"Спред между {base} и {quote} = {spread:.2f}%"
                bot.send_message(chat_id=CHAT_ID, text=message)
        time.sleep(60)  # проверяем каждую минуту

if __name__ == '__main__':
    main()
