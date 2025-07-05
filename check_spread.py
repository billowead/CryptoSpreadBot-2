import os
import requests
from telegram import Bot

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

def get_price_coingecko():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return float(r.json()['bitcoin']['usd'])
    except Exception as e:
        print(f"CoinGecko error: {e}")
        return None

def get_price_binance():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        return float(r.json()['price'])
    except Exception as e:
        print(f"Binance error: {e}")
        return None

def check_spread():
    price1 = get_price_coingecko()
    price2 = get_price_binance()
    if price1 is None or price2 is None:
        print("❌ Ошибка получения цен")
        return

    spread = abs(price1 - price2) / ((price1 + price2) / 2)
    spread_percent = spread * 100
    print(f"🔍 Спред: {spread_percent:.2f}%")

    if spread >= 0.005:
        msg = (
            f"🚨 СПРЕД!\n"
            f"{spread_percent:.2f}% между Coingecko и Binance\n"
            f"Coingecko: {price1}$\nBinance: {price2}$\n"
            f"<a href='https://www.binance.com/en/trade/BTC_USDT'>Binance</a>"
        )
        try:
            bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
        except Exception as e:
            print(f"Ошибка Telegram: {e}")

if __name__ == "__main__":
    check_spread()
