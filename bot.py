import os
import time
import requests
from telegram import Bot

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = Bot(token=TELEGRAM_TOKEN)

pairs = ["BTCUSDT", "ETHUSDT"]  # Добавляй нужные пары

def get_price_binance(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    r = requests.get(url)
    r.raise_for_status()
    return float(r.json()['price'])

def get_price_kucoin(symbol):
    symbol = symbol.lower()
    # KuCoin API использует дефис: btc-usdt
    symbol = symbol.replace("usdt", "usdt").replace("btc", "btc").replace("/", "-")
    url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol}"
    r = requests.get(url)
    r.raise_for_status()
    return float(r.json()['data']['price'])

def get_price_kraken(symbol):
    kraken_map = {
        "BTCUSDT": "XBTUSDT",
        "ETHUSDT": "ETHUSDT",
    }
    kraken_symbol = kraken_map.get(symbol, symbol)
    url = f"https://api.kraken.com/0/public/Ticker?pair={kraken_symbol}"
    r = requests.get(url)
    r.raise_for_status()
    result = r.json()['result']
    first_key = list(result.keys())[0]
    return float(result[first_key]['c'][0])

def get_price_bybit(symbol):
    # Bybit API требует маленькие буквы, и _USDT -> USDT
    # формат: BTCUSDT → BTCUSDT
    url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()
    if data['ret_code'] != 0:
        raise Exception("Bybit API error")
    price = float(data['result'][0]['last_price'])
    return price

def check_spread(symbol):
    prices = {}
    exch_funcs = {
        'Binance': get_price_binance,
        'KuCoin': get_price_kucoin,
        'Kraken': get_price_kraken,
        'Bybit': get_price_bybit
    }

    for name, func in exch_funcs.items():
        try:
            prices[name] = func(symbol)
        except Exception:
            # можно логировать ошибку, но для простоты пропускаем
            continue

    prices = {k: v for k, v in prices.items() if v is not None}

    if len(prices) < 2:
        return None

    max_exch = max(prices, key=prices.get)
    min_exch = min(prices, key=prices.get)

    max_price = prices[max_exch]
    min_price = prices[min_exch]

    spread = (max_price - min_price) / ((max_price + min_price) / 2) * 100

    if spread > 2:
        message = (
            f"Спред по {symbol}:\n"
            f"{max_exch}: {max_price}$\n"
            f"{min_exch}: {min_price}$\n"
            f"Спред: {spread:.2f}%\n"
            f"{max_exch}: https://www.{max_exch.lower()}.com/en/trade/{symbol}\n"
            f"{min_exch}: https://www.{min_exch.lower()}.com/en/trade/{symbol}"
        )
        return message

    return None

def main():
    while True:
        for symbol in pairs:
            msg = check_spread(symbol)
            if msg:
                bot.send_message(chat_id=CHAT_ID, text=msg)
        time.sleep(60)

if __name__ == '__main__':
    main()
