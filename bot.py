import os
import time
import requests
from telegram import Bot

# Получаем токен и chat_id из переменных окружения
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# Пары для отслеживания
pairs = [
    ('BTC', 'USDT'),
    ('ETH', 'USDT'),
    ('DOGE', 'USDT'),
    ('LTC', 'USDT')
]

# Получение цены с Binance
def get_binance_price(base, quote):
    try:
        symbol = f"{base}{quote}".upper()
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        res = requests.get(url).json()
        return float(res['price'])
    except:
        return None

# Получение цены с Bybit
def get_bybit_price(base, quote):
    try:
        symbol = f"{base}{quote}".upper()
        url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
        res = requests.get(url).json()
        return float(res['result'][0]['last_price'])
    except:
        return None

def main():
    while True:
        for base, quote in pairs:
            binance_price = get_binance_price(base, quote)
            bybit_price = get_bybit_price(base, quote)

            if binance_price and bybit_price:
                spread = abs(binance_price - bybit_price) / ((binance_price + bybit_price) / 2) * 100
                if spread >= 2:  # порог можно изменить
                    message = (
                        f"🚨 Спред {base}/{quote} превышает 2%:\n\n"
                        f"Binance: {binance_price}\n"
                        f"Bybit: {bybit_price}\n"
                        f"Спред: {spread:.2f}%"
                    )
                    bot.send_message(chat_id=CHAT_ID, text=message)

        time.sleep(60)

if __name__ == "__main__":
    main()
