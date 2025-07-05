import logging
import asyncio
from telegram import Bot
import httpx
from telegram.constants import ParseMode

# Конфигурация
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
CHECK_INTERVAL = 60  # Проверка каждые 60 секунд
SPREAD_THRESHOLD = 2.0  # Порог спреда для уведомления (2%)
REQUEST_DELAY = 1  # Задержка между запросами (в секундах)

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
        "price_key": ["result", 0, "last_price"]
    }
}

bot = Bot(token=TELEGRAM_TOKEN)

async def get_price(exchange: str, pair: str) -> float:
    """Получает цену для пары на бирже"""
    try:
        config = EXCHANGES[exchange]
        params = {}
        
        # Формируем параметры запроса для каждой биржи
        if exchange == "mexc":
            params["symbol"] = pair.replace("-", "_")
        elif exchange == "bybit":
            params["symbol"] = pair.replace("-", "")
        else:  # KuCoin
            params["symbol"] = pair

        # Настраиваем заголовки
        headers = {"User-Agent": "Mozilla/5.0"}
        
        async with httpx.AsyncClient() as client:
            await asyncio.sleep(REQUEST_DELAY)  # Задержка между запросами
            
            resp = await client.get(
                config["url"],
                params=params,
                headers=headers,
                timeout=15
            )
            
            # Логируем сырой ответ для отладки
            logger.debug(f"{exchange} response: {resp.text}")
            
            if resp.status_code != 200:
                logger.warning(f"{exchange} вернул {resp.status_code} для {pair}")
                return None
                
            data = resp.json()
            
            # Извлекаем цену по указанному пути
            price = data
            for key in config["price_key"]:
                if isinstance(key, int):
                    if len(price) <= key:
                        return None
                    price = price[key]
                else:
                    price = price.get(key)
                    if price is None:
                        return None
            
            return float(price)
            
    except Exception as e:
        logger.error(f"Ошибка на {exchange} ({pair}): {str(e)}")
        return None

async def monitor_spread():
    """Мониторинг спреда между биржами"""
    while True:
        try:
            for pair, urls in PAIRS.items():
                prices = {}
                
                # Получаем цены со всех бирж
                for exchange in EXCHANGES:
                    price = await get_price(exchange, pair)
                    if price is not None:
                        prices[exchange] = price
                
                # Если есть хотя бы две цены
                if len(prices) >= 2:
                    max_spread = 0
                    best_pair = None
                    
                    # Находим максимальный спред
                    exchanges = list(prices.keys())
                    for i in range(len(exchanges)):
                        for j in range(i+1, len(exchanges)):
                            spread = abs(prices[exchanges[i]] - prices[exchanges[j]])
                            spread_percent = (spread / ((prices[exchanges[i]] + prices[exchanges[j]])/2)) * 100
                            
                            if spread_percent > max_spread:
                                max_spread = spread_percent
                                best_pair = (exchanges[i], exchanges[j])
                    
                    # Отправляем уведомление если спред превысил порог
                    if max_spread >= SPREAD_THRESHOLD:
                        exch1, exch2 = best_pair
                        spread_abs = abs(prices[exch1] - prices[exch2])
                        
                        message = (
                            f"🚨 *Обнаружен спред {max_spread:.2f}%*\n\n"
                            f"📊 *Пара*: {pair}\n"
                            f"🔹 *{exch1.upper()}*: [Купить]({urls[exch1]}) - {prices[exch1]:.2f}\n"
                            f"🔸 *{exch2.upper()}*: [Купить]({urls[exch2]}) - {prices[exch2]:.2f}\n\n"
                            f"💵 *Абсолютный спред*: {spread_abs:.2f} USDT"
                        )
                        
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message,
                            parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True
                        )
                        logger.info(f"Отправлено уведомление для {pair}: спред {max_spread:.2f}%")
        
        except Exception as e:
            logger.error(f"Ошибка в мониторинге: {str(e)}")
        
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    """Запуск бота"""
    logger.info("🟢 Бот мониторинга спреда запущен")
    try:
        await monitor_spread()
    except asyncio.CancelledError:
        logger.info("🔴 Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
