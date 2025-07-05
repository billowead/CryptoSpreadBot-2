import os
from flask import Flask, request
import requests
import telegram

app = Flask(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

bot = telegram.Bot(token=TOKEN)

def get_binance_price(symbol='BTCUSDT'):
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={symbol}'
    resp = requests.get(url).json()
    return float(resp['price'])

def get_bybit_price(symbol='BTCUSDT'):
    url = f'https://api.bybit.com/v2/public/tickers?symbol={symbol}'
    resp = requests.get(url).json()
    if resp['ret_code'] == 0:
        return float(resp['result'][0]['last_price'])
    else:
        return None

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        binance_price = get_binance_price()
        bybit_price = get_bybit_price()

        if not binance_price or not bybit_price:
            return 'Failed to get prices', 500

        average_price = (binance_price + bybit_price) / 2
        spread = abs(binance_price - bybit_price) / average_price * 100

        threshold = 0.5  # Порог в процентах

        if spread >= threshold:
            msg = (f"Выгодный спред!\n"
                   f"Пара: BTC/USDT\n"
                   f"Спред: {spread:.2f}%\n"
                   f"Биржи: Binance ({binance_price}), Bybit ({bybit_price})")
            bot.send_message(chat_id=CHAT_ID, text=msg)
            return 'Message sent', 200
        else:
            return 'No significant spread', 200

    except Exception as e:
        return f'Error: {str(e)}', 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
