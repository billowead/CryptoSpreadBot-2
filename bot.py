import logging
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import httpx
from telegram.constants import ParseMode

# Конфигурация
TELEGRAM_TOKEN = "7829142639:AAHNhPm0H1L4RTxNWXltrJ_xUZYozGZ6-jY"
CHAT_ID = "593059857"
CHECK_INTERVAL = 60
SPREAD_THRESHOLD = 2.0

# Торговые пары
PAIRS = ["BTC-USDT", "ETH-USDT"]

# API бирж
EXCHANGES = {
    "kucoin": {
        "url": "https://api.kucoin.com/api/v1/market/orderbook/level1",
        "params": lambda p: {"symbol": p},
        "price_path": ["data", "price"]
    },
    "mexc": {
        "url": "https://api.mexc.com/api/v3/ticker/price",
        "params": lambda p: {"symbol": p.replace("-", "")},
        "price_path": ["price"]
    }
}

# Настройка логов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpreadMonitorBot:
    def __init__(self):
        self.app = Application.builder().token(TELEGRAM_TOKEN).build()
        self.active_chats = set()
        self.bot = self.app.bot
        
        # Регистрируем обработчики команд
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("check", self.manual_check))
        
        # Запускаем фоновую задачу
        self.app.job_queue.run_repeating(
            self.monitor_spread,
            interval=CHECK_INTERVAL,
            first=10
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        chat_id = update.effective_chat.id
        self.active_chats.add(chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text="🚀 Бот мониторинга спреда активирован!\n"
                 "Я буду присылать уведомления, когда спред между биржами превысит 2%.\n"
                 "Команда /check - проверить сейчас"
        )

    async def manual_check(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /check"""
        chat_id = update.effective_chat.id
        await context.bot.send_message(
            chat_id=chat_id,
            text="🔍 Проверяю текущие спреды..."
        )
        await self.check_and_notify(chat_id)

    async def fetch_price(self, exchange: str, pair: str) -> float:
        """Получение цены с биржи"""
        try:
            config = EXCHANGES[exchange]
            params = config["params"](pair)
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    config["url"],
                    params=params,
                    timeout=10
                )
                
                if resp.status_code != 200:
                    logger.warning(f"{exchange} status {resp.status_code} for {pair}")
                    return None
                    
                data = resp.json()
                
                # Извлекаем цену
                price = data
                for key in config["price_path"]:
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
            logger.error(f"Error fetching {pair} from {exchange}: {str(e)}")
            return None

    async def check_spread(self, pair: str):
        """Проверка спреда для одной пары"""
        prices = {}
        
        for exchange in EXCHANGES:
            price = await self.fetch_price(exchange, pair)
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

    async def send_notification(self, chat_id: int, result: dict):
        """Отправка уведомления о спреде"""
        exch1, exch2 = result["exchanges"]
        msg = (
            f"🚨 *Обнаружен спред {result['spread']:.2f}%*\n\n"
            f"📊 *Пара*: {result['pair']}\n"
            f"🔹 *{exch1.upper()}*: {result['prices'][exch1]:.2f}\n"
            f"🔸 *{exch2.upper()}*: {result['prices'][exch2]:.2f}\n\n"
            f"💵 Разница: {abs(result['prices'][exch1] - result['prices'][exch2]):.2f} USDT"
        )
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=msg,
                parse_mode=ParseMode.MARKDOWN
            )
            logger.info(f"Уведомление отправлено в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки в чат {chat_id}: {str(e)}")

    async def check_and_notify(self, chat_id: int = None):
        """Проверка всех пар и отправка уведомлений"""
        for pair in PAIRS:
            result = await self.check_spread(pair)
            if result:
                if chat_id:
                    await self.send_notification(chat_id, result)
                else:
                    for active_chat in self.active_chats:
                        await self.send_notification(active_chat, result)

    async def monitor_spread(self, context: ContextTypes.DEFAULT_TYPE):
        """Фоновая задача мониторинга"""
        await self.check_and_notify()

    def run(self):
        """Запуск бота"""
        logger.info("Starting spread monitor bot...")
        self.app.run_polling()

if __name__ == "__main__":
    try:
        bot = SpreadMonitorBot()
        bot.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
