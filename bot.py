import os
import logging
import asyncio
from telegram import Bot
import httpx

# Конфигурация
TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = 593059857
PORT = int(os.environ.get('PORT', 10000))
WEBHOOK_URL = f"https://cryptospreadbot-2-2.onrender.com/{TOKEN}"
CHECK_INTERVAL = 60  # секунды

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Конфигурация API (основные + резервные)
API_CONFIG = {
    "binance": {
        "url": "https://api1.binance.com/api/v3/ticker/price",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["price"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    },
    "bybit": {
        "url": "https://api.bytick.com/v2/public/tickers",
        "params": {"symbol": "BTCUSDT"},
        "price_key": ["result", 0, "last_price"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    },
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": {"symbol": "BTC-USDT"},
        "price_key": ["data", "price"],
        "headers": {"Accept": "application/json"}
    },
    "huobi": {
        "url": "https://api.huobi.pro/market/detail/merged",
        "params": {"symbol": "btcusdt"},
        "price_key": ["tick", "close"],
        "headers": {"User-Agent": "Mozilla/5.0"}
    }
}

bot = Bot(token=TOKEN)

async def get_price(exchange: str):
    """Получаем цену с указанной биржи"""
    try:
        config = API_CONFIG[exchange]
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                config["url"],
                params=config["params"],
                headers=config.get("headers", {})
            )
            
            if response.status_code != 200:
                logger.warning(f"{exchange} вернул статус {response.status_code}")
                return None
                
            data = response.json()
            
            # Достаем цену по указанному пути
            price = data
            for key in config["price_key"]:
                if isinstance(price, (list, tuple)) and isinstance(key, int):
                    if len(price) <= key:
                        return None
                elif isinstance(price, dict) and key not in price:
                    return None
                price = price[key]
                
            return float(price)
            
    except httpx.RequestError as e:
        logger.error(f"Ошибка подключения к {exchange}: {str(e)}")
    except (ValueError, KeyError, IndexError) as e:
        logger.error(f"Ошибка парсинга ответа от {exchange}: {str(e)}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка при запросе к {exchange}: {str(e)}")
    
    return None

async def check_spread():
    """Проверяем спред между биржами"""
    prices = {}
    priority_exchanges = ["binance", "bybit"]  # Сначала проверяем основные
    
    # Получаем цены с приоритетных бирж
    for exchange in priority_exchanges:
        price = await get_price(exchange)
        if price is not None:
            prices[exchange] = price
            if len(prices) >= 2:  # Нашли две цены - можно сравнивать
                break
    
    # Если не получили достаточно данных, пробуем резервные биржи
    if len(prices) < 2:
        for exchange in [e for e in API_CONFIG.keys() if e not in priority_exchanges]:
            price = await get_price(exchange)
            if price is not None:
                prices[exchange] = price
                if len(prices) >= 2:
                    break
    
    # Если нашли хотя бы две цены
    if len(prices) >= 2:
        exchanges = list(prices.keys())
        spread = abs(prices[exchanges[0]] - prices[exchanges[1]])
        spread_percent = (spread / ((prices[exchanges[0]] + prices[exchanges[1]]) / 2)) * 100

        if spread_percent >= 2:  # Порог 2%
            msg = (
                f"🚨 Обнаружен спред BTC/USDT > 2%\n\n"
                f"📊 {exchanges[0]}: {prices[exchanges[0]]:.2f} USDT\n"
                f"📊 {exchanges[1]}: {prices[exchanges[1]]:.2f} USDT\n"
                f"💰 Разница: {spread:.2f} USDT ({spread_percent:.2f}%)\n\n"
                f"
