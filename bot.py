import os
import asyncio
import httpx
from telegram import Bot

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
SPREAD_THRESHOLD = 2.0  # порог, выше которого отправляется сигнал

bot = Bot(token=TELEGRAM_TOKEN)

pairs = [
    ("BTC", "USDT"),
    ("ETH", "USDT"),
    ("DOGE", "USDT"),
    ("LTC", "USDT"),
]

async def get_price_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            return float(response.json()["price"])
        except:
            return None

async def get_price_bybit(symbol):
    url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            result = response.json()["result"]
            if result and isinstance(result, list):
                return float(result[0]["last_price"])
            elif result and isinstance(result, dict):
                return float(result["last_price"])
        except:
            return None

def get_links(symbol):
    return {
        "binance": f"https://www.binance.com/en/trade/{symbol}",
        "bybit": f"https://www.bybit.com/trade/usdt/{symbol.replace('USDT', '')}"
    }

async def check_spreads():
    for base, quote in pairs:
        symbol = base + quote

        binance_price = await get_price_binance(symbol)
        bybit_price = await get_price_bybit(symbol)

        if not binance_price or not bybit_price:
            continue

        spread = abs(binance_price - bybit_price) / ((binance_price + bybit_price) / 2) * 100

        if spread >= SPREAD_THRESHOLD:
            links = get_links(symbol)
            message = (
                f"💹 Спред на {symbol} превышает {SPREAD_THRESHOLD}%:\n\n"
                f"🔸 Binance: ${binance_price:.2f}\n"
                f"🔹 Bybit: ${bybit_price:.2f}\n"
                f"📈 Спред: {spread:.2f}%\n\n"
                f"🌐 [Binance]({links['binance']}) | [Bybit]({links['bybit']})"
            )

            await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")

async def main():
    while True:
        await check_spreads()
        await asyncio.sleep(60)  # каждые 60 секунд

if __name__ == "__main__":
    asyncio.run(main())
