import logging
import asyncio
from telegram import Bot
import httpx
from telegram.constants import ParseMode
from aiohttp import web

# Конфигурация
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
CHECK_INTERVAL = 60
SPREAD_THRESHOLD = 2.0
PORT = 8000

# Торговые пары
PAIRS = ["BTC-USDT", "ETH-USDT"]

# API бирж с исправленными параметрами
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": lambda p: {"symbol": p},
        "price_path": ["data", "price"]
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "params": lambda p: {"symbol": p.replace("-", "")},  # MEXC использует BTCUSDT без разделителя
        "price_path": ["price"]
    },
    "bybit": {
        "url": "https://api.bybit.com/v2/public/tickers",
        "params": lambda p: {"symbol": p.replace("-", "")},
        "price_path": ["result", 0, "last_price"],
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

async def fetch_price(exchange: str, pair: str) -> float:
    """Получение цены с биржи с улучшенной обработкой ошибок"""
    try:
        config = EXCHANGES[exchange]
        params = config["params"](pair)
        headers = config.get("headers", {})
        
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                config["url"],
                params=params,
                headers=headers,
                timeout=10
            )
            
            if resp.status_code != 200:
                logger.warning(f"{exchange} status {resp.status_code} for {pair}")
                return None
                
            data = resp.json()
            
            # Извлекаем цену по указанному пути
            price = data
            for key in config["price_path"]:
                try:
                    if isinstance(key, int):
                        price = price[key]
                    else:
                        price = price[key]
                except (IndexError, KeyError, TypeError):
                    logger.error(f"Invalid price path for {exchange} ({pair})")
                    return None
            
            return float(price) if price else None
            
    except Exception as e:
        logger.error(f"Error fetching {pair} from {exchange}: {str(e)}")
        return None

async def health_check(request):
    return web.Response(text="OK")

async def compare_prices(pair: str):
    """Сравнение цен между биржами"""
    prices = {}
    
    for exchange in EXCHANGES:
        price = await fetch_price(exchange, pair)
        if price is not None:
            prices[exchange] = price
            logger.info(f"{exchange} {pair}: {price:.2f}")
    
    if len(prices) < 2:
        return None
        
    # Находим максимальный спред
    exchanges = list(prices.keys())
    max_spread = 0
    best_pair = None
    
    for i in range(len(exchanges)):
        for j in range(i+1, len(exchanges)):
            spread = abs(prices[exchanges[i]] - prices[exchanges[j]])
            spread_percent = (spread / ((prices[exchanges[i]] + prices[exchanges[j]])/2)) * 100
            
            if spread_percent > max_spread:
                max_spread = spread_percent
                best_pair = (exchanges[i], exchanges[j])
    
    if max_spread >= SPREAD_THRESHOLD:
        return {
            "pair": pair,
            "spread": max_spread,
            "exchanges": best_pair,
            "prices": {
                best_pair[0]: prices[best_pair[0]],
                best_pair[1]: prices[best_pair[1]]
            }
        }
    return None

async def monitor_spread():
    """Основной цикл мониторинга"""
    while True:
        try:
            for pair in PAIRS:
                result = await compare_prices(pair)
                if result:
                    exch1, exch2 = result["exchanges"]
                    msg = (
                        f"🚨 *Spread Alert*: {result['spread']:.2f}%\n"
                        f"📊 *Pair*: {result['pair']}\n"
                        f"🔹 *{exch1.upper()}*: {result['prices'][exch1]:.2f}\n"
                        f"🔸 *{exch2.upper()}*: {result['prices'][exch2]:.2f}\n"
                        f"💵 Difference: {abs(result['prices'][exch1] - result['prices'][exch2]):.2f} USDT"
                    )
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=msg,
                        parse_mode=ParseMode.MARKDOWN
                    )
        
        except Exception as e:
            logger.error(f"Monitoring error: {str(e)}")
        
        await asyncio.sleep(CHECK_INTERVAL)

async def create_app():
    app = web.Application()
    app.add_routes([web.get('/', health_check)])
    return app

async def main():
    logger.info("Starting spread monitor bot...")
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
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
