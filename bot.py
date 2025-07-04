import os
import asyncio
import httpx
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

# Пары для отслеживания
pairs = [
    ('BTC', 'USDT'),
    ('ETH', 'USDT'),
    ('DOGE', 'USDT'),
    ('LTC', 'USDT'),
]

# Биржи и их API (пока только Binance и Bybit)
async def get_price_binance(base, quote):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={base}{quote}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            return float(response.json()['price'])
        except:
            return None

async def get_price_bybit(base, quote):
    url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={base}{quote}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            result = response.json()
            price = result['result']['list'][0]['lastPrice']
            return float(price)
        except:
            return None

def get_trade_links(base, quote):
    binance_link = f"https://www.binance.com/en/trade/{base}_{quote}"
    bybit_link = f"https://www.bybit.com/trade/usdt/{base}-{quote}"
    return binance_link, bybit_link

async def check_and_notify():
    while True:
        for base, quote in pairs:
            price_binance = await get_price_binance(base, quote)
            price_bybit = await get_price_bybit(base, quote)

            if price_binance and price_bybit:
                spread = abs(price_binance - price_bybit) / ((price_binance + price_bybit) / 2) * 100
                if spread > 2:
                    binance_link, bybit_link = get_trade_links(base, quote)
                    message = (
                        f"💹 Спред между {base}/{quote} = {spread:.2f}%\n"
                        f"🔗 Binance: {binance_link}\n"
                        f"🔗 Bybit: {bybit_link}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(check_and_notify())
