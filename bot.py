import os
import asyncio
import httpx
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

# Список пар
PAIRS = ['BTC/USDT', 'ETH/USDT', 'LTC/USDT', 'DOGE/USDT']

async def fetch_price(client, url):
    try:
        r = await client.get(url, timeout=5)
        r.raise_for_status()
        return r.json()
    except:
        return None

async def check_spreads():
    async with httpx.AsyncClient() as client:
        for pair in PAIRS:
            base, quote = pair.split('/')
            symbol = base + quote

            binance_url = f'https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}'
            bybit_url = f'https://api.bybit.com/v2/public/tickers?symbol={symbol}'

            binance = await fetch_price(client, binance_url)
            bybit = await fetch_price(client, bybit_url)

            if not binance or not bybit or not bybit.get("result"):
                continue

            try:
                price_binance = float(binance["askPrice"])
                price_bybit = float(bybit["result"][0]["ask_price"])
                spread = abs(price_binance - price_bybit) / ((price_binance + price_bybit) / 2) * 100

                if spread > 2:
                    message = (
                        f"📊 Спред обнаружен для {pair}!\n\n"
                        f"💰 Binance: {price_binance:.2f}\n"
                        f"💰 Bybit: {price_bybit:.2f}\n"
                        f"📈 Спред: {spread:.2f}%\n\n"
                        f"🔗 Binance: https://www.binance.com/ru/trade/{base}_{quote}\n"
                        f"🔗 Bybit: https://www.bybit.com/trade/usdt/{base.lower()}"
                    )
                    await bot.send_message(chat_id=CHAT_ID, text=message)
            except Exception as e:
                print(f"Ошибка: {e}")

async def main_loop():
    while True:
        await check_spreads()
        await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main_loop())
