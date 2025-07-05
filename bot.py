import logging
import asyncio
from telegram import Bot
import httpx
from telegram.constants import ParseMode

# Конфигурация
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
CHECK_INTERVAL = 60
SPREAD_THRESHOLD = 2.0
REQUEST_DELAY = 1
PORT = 8000  # Явно указываем порт для Render

# Настройка торговых пар
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

# Настройка API бирж
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "price_key": ["data", "price"],
        "param_format": lambda p: {"symbol": p}
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "price_key": ["price"],
        "param_format": lambda p: {"symbol": p.replace("-", "_")}
    },
    "bybit": {
        "url": "https://api.bybit.com/v2/public/tickers",
        "price_key": ["result", 0, "last_price"],
        "param_format": lambda p: {"symbol": p.replace("-", "")},
        "headers": {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bybit.com"
        }
    }
}

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)

async def get_price(exchange: str, pair: str) -> float:
    """Получает цену для пары на бирже"""
    try:
        config = EXCHANGES[exchange]
        params = config["param_format"](pair)
        headers = config.get("headers", {})
        
        async with httpx.AsyncClient() as client:
            await asyncio.sleep(REQUEST_DELAY)
            
            resp = await client.get(
                config["url"],
                params=params,
                headers=headers,
                timeout=15
            )
            
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

async def health_check(request):
    """Endpoint для health check"""
    return web.Response(text="OK")

async def monitor_spread():
    """Мониторинг спреда между биржами"""
    while True:
        try:
            for pair, urls in PAIRS.items():
                prices = {}
                
                for exchange in EXCHANGES:
                    price = await get_price(exchange, pair)
                    if price is not None:
                        prices[exchange] = price
                
                if len(prices) >= 2:
                    max_spread = 0
                    best_pair = None
                    
                    exchanges = list(prices.keys())
                    for i in range(len(exchanges)):
                        for j in range(i+1, len(exchanges)):
                            spread = abs(prices[exchanges[i]] - prices[exchanges[j]])
                            spread_percent = (spread / ((prices[exchanges[i]] + prices[exchanges[j]])/2)) * 100
                            
                            if spread_percent > max_spread:
                                max_spread = spread_percent
                                best_pair = (exchanges[i], exchanges[j])
                    
                    if max_spread >= SPREAD_THRESHOLD:
                        exch1, exch2 = best_pair
                        spread_abs = abs(prices[exch1] - prices[exch2])
                        
                        message = (
                            f"🚨 *Обнаружен спред {max_spread:.2f}%*\n\n"
                            f"📊 *Пара*: {pair}\n"
                            f"🔹 *{exch1.upper()}*: [Торговать]({urls[exch1]}) - {prices[exch1]:.2f}\n"
                            f"🔸 *{exch2.upper()}*: [Торговать]({urls[exch2]}) - {prices[exch2]:.2f}\n\n"
                            f"💵 *Разница*: {spread_abs:.2f} USDT"
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

async def create_app():
    """Создаем приложение aiohttp"""
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    return app

async def main():
    """Запуск бота"""
    logger.info("🟢 Бот мониторинга спреда запущен")
    app = await create_app()
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    
    await monitor_spread()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🔴 Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {str(e)}")
