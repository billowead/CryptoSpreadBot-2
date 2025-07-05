import logging
import asyncio
from telegram import Bot
import httpx
from telegram.constants import ParseMode

# Конфигурация (используем ваши названия переменных)
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"  # Ваш токен
CHAT_ID = "593059857"  # Ваш chat_id
CHECK_INTERVAL = 60  # Проверка каждые 60 секунд
SPREAD_THRESHOLD = 2.0  # Порог спреда 2%

# Торговые пары и ссылки
PAIRS = {
    "BTC-USDT": {
        "kucoin": "https://www.kucoin.com/trade/BTC-USDT",
        "mexc": "https://www.mexc.com/exchange/BTC_USDT",
        "bybit": "https://www.bybit.com/trade/usdt/BTCUSDT"
    },
    "ETH-USDT": {
        "kucoin": "https://www.kucoin.com/trade/ETH-USDT",
        "mexc": "https://www.mexc.com/exchange/ETH_USDT",
        "bybit": "https://www.bybit.com/trade/usdt/ETHUSDT"
    }
}

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API бирж
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "price_key": ["data", "price"]
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "price_key": ["price"]
    },
    "bybit": {
        "url": "https://api.bybit.com/v2/public/tickers",
        "price_key": ["result", 0, "last_price"],
        "param_key": "BTCUSDT"  # Автоподстановка для пары
    }
}

bot = Bot(token=TELEGRAM_TOKEN)

async def get_price(exchange: str, pair: str) -> float:
    """Получает цену для пары на бирже"""
    try:
        config = EXCHANGES[exchange].copy()
        
        # Особенность Bybit - подставляем символ пары
        if exchange == "bybit":
            config["param_key"] = pair.replace("-", "")
        
        async with httpx.AsyncClient() as client:
            params = {"symbol": pair} if exchange == "mexc" else None
            if exchange == "bybit":
                params = {"symbol": config["param_key"]}
            
            resp = await client.get(
                config["url"],
                params=params,
                timeout=10
            )
            data = resp.json()
            
            # Достаем цену по ключам
            price = data
            for key in config["price_key"]:
                if isinstance(key, int):
                    price = price[key]
                else:
                    price = price.get(key)
            
            return float(price) if price else None
            
    except Exception as e:
        logger.error(f"Ошибка на {exchange} ({pair}): {str(e)}")
        return None

async def monitor_spread():
    """Сравнивает цены и отправляет уведомления при спреде >2%"""
    while True:
        try:
            for pair, urls in PAIRS.items():
                prices = {}
                for exchange in EXCHANGES:
                    price = await get_price(exchange, pair)
                    if price:
                        prices[exchange] = price
                
                if len(prices) >= 2:
                    # Находим максимальный спред среди всех пар бирж
                    max_spread = 0
                    best_exchanges = ()
                    
                    for exch1 in prices:
                        for exch2 in prices:
                            if exch1 != exch2:
                                spread = abs(prices[exch1] - prices[exch2]])
                                spread_percent = (spread / ((prices[exch1] + prices[exch2]])/2)) * 100
                                
                                if spread_percent > max_spread:
                                    max_spread = spread_percent
                                    best_exchanges = (exch1, exch2)
                    
                    # Отправляем уведомление, если спред >2%
                    if max_spread >= SPREAD_THRESHOLD:
                        exch1, exch2 = best_exchanges
                        spread = abs(prices[exch1] - prices[exch2]])
                        
                        message = (
                            f"🚀 *{pair}* — спред `{max_spread:.2f}%`\n\n"
                            f"🔹 *{exch1.upper()}*: [Купить]({urls[exch1]}) — `{prices[exch1]:.2f}`\n"
                            f"🔸 *{exch2.upper()}*: [Купить]({urls[exch2]}) — `{prices[exch2]:.2f}`\n\n"
                            f"💵 Разница: `{spread:.2f} USDT`"
                        )
                        
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                        logger.info(f"Спред {pair}: {max_spread:.2f}%")
        
        except Exception as e:
            logger.error(f"Ошибка: {str(e)}")
        
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    """Запуск мониторинга"""
    logger.info("Бот запущен. Мониторинг спредов >2%...")
    await monitor_spread()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {str(e)}")
