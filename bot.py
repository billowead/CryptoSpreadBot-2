import os
import asyncio
import random
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

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

def check_spread(pair):
    spread = random.uniform(0, 5)
    return spread

async def main():
    while True:
        for base, quote in pairs:
            spread = check_spread((base, quote))
            if spread > 2:
                message = f"Спред между {base} и {quote} = {spread:.2f}%"
                await bot.send_message(chat_id=CHAT_ID, text=message)
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
