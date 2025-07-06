import time
import requests
from telegram import Bot

# Твои данные:
TELEGRAM_TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'  # твой токен Telegram-бота
CHAT_ID = '593059857'  # твой Telegram chat ID

RAPIDAPI_KEY = '6ce956ea3amsh45b17d8a9c691a4p1f4badjsnbc9d72aff450'  # твой RapidAPI ключ

PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT']

HEADERS_BINANCE = {
    'x-rapidapi-host': 'binance43.p.rapidapi.com',
    'x-rapidapi-key': RAPIDAPI_KEY
}

HEADERS_BYBIT = {
    'x-rapidapi-host': 'bybit4.p.rapidapi.com',
    'x-rapidapi-key': RAPIDAPI_KEY
}

BINANCE_URL = 'https://binance43.p.rapidapi.com/ticker/24hr'
BYBIT_URL = 'https://bybit4.p.rapidapi.com/perpetual/usdc/openapi/public/v1/tick'

bot = Bot(token=TELEGRAM_TOKEN)

def get_binance_price(symbol):
    try:
        response = requests.get(BINANCE_URL, headers=HEADERS_BINANCE, params={'symbol': symbol})
        data = response.json()
        if isinstance(data, list):
            for item in data:
                if item['symbol'] == symbol:
                    return float(item['lastPrice'])
        else:
            return float(data['lastPrice'])
    except Exception as e:
        print(f"Ошибка Binance {symbol}: {e}")
        return None

def get_bybit_price(symbol):
    try:
        response = requests.get(BYBIT_URL, headers=HEADERS_BYBIT)
        data = response.json()
        for item in data['result']['list']:
            if item['symbol'] == symbol:
                return float(item['lastPrice'])
    except Exception as e:
        print(f"Ошибка Bybit {symbol}: {e}")
    return None

def check_spreads():
    for pair in PAIRS:
        binance_price = get_binance_price(pair)
        bybit_price = get_bybit_price(pair)
        if binance_price is None or bybit_price is None:
            continue
        spread = abs(binance_price - bybit_price) / ((binance_price + bybit_price) / 2) * 100
        if spread > 2:
            message = (f"Спред для {pair} больше 2%!\n"
                       f"Binance: {binance_price}\n"
                       f"Bybit: {bybit_price}\n"
                       f"Спред: {spread:.2f}%")
            bot.send_message(chat_id=CHAT_ID, text=message)
            print(message)
        else:
            print(f"{pair}: спред {spread:.2f}% - ниже порога")

if __name__ == "__main__":
    while True:
        check_spreads()
        time.sleep(60)
