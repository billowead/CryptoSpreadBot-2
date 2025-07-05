import time
import requests
from telegram import Bot

TELEGRAM_TOKEN = '7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY'
CHAT_ID = 593059857

bot = Bot(token=TELEGRAM_TOKEN)

def get_price_coingecko():
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        price = r.json()['bitcoin']['usd']
        print(f"Coingecko BTC price: {price}")
        return float(price)
    except requests.exceptions.HTTPError as e:
        print(f"CoinGecko HTTP error: {e}")
    except Exception as e:
        print(f"CoinGecko error: {e}")
    return None

def get_price_binance():
    url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        price = float(r.json()['price'])
        print(f"Binance BTC price: {price}")
        return price
    except requests.exceptions.HTTPError as e:
        print(f"Binance HTTP error: {e}")
    except Exception as e:
        print(f"Binance error: {e}")
    return None

def monitor_spread():
    THRESHOLD = 0.005  # 0.5%
    print("▶️ Запущен мониторинг спреда (с интервалом 60 секунд)...")
    while True:
        price1 = get_price_coingecko()
        price2 = get_price_binance()

        if price1 is None or price2 is None:
            print("❌ Ошибка получения цен, пропускаем цикл.")
            time.sleep(60)
            continue

        spread = abs(price1 - price2) / ((price1 + price2) / 2)
        spread_percent = spread * 100
        print(f"Текущий спред: {spread_percent:.3f}%")

        if spread >= THRESHOLD:
            msg = (
                f"🚨 СПРЕД! BTC:\n"
                f"{spread_percent:.2f}% между Coingecko и Binance\n"
                f"Цены:\nCoingecko: {price1}\nBinance: {price2}\n"
                f"<a href='https://www.binance.com/en/trade/BTC_USDT'>Binance</a>"
            )
            print("Отправляем уведомление в Telegram...")
            try:
                bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode='HTML')
            except Exception as e:
                print(f"Ошибка отправки сообщения: {e}")

        time.sleep(60)

if __name__ == "__main__":
    monitor_spread()
