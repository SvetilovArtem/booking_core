import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from app.config import settings
from app.core.router import main_router

# Настраиваем логирование
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск бота...")
    
    # 1. Инициализация Бота
    bot = Bot(token=settings.BOT_TOKEN)
    
    # 2. Инициализация Redis для FSM (Машины состояний)
    redis = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
    storage = RedisStorage(redis=redis)
    
    # 3. Инициализация Диспетчера
    dp = Dispatcher(storage=storage)
    
    # 4. Подключаем главный роутер (все хендлеры будут внутри него)
    dp.include_router(main_router)
    
    # 5. Пропускаем накопившиеся обновления при старте
    await bot.delete_webhook(drop_pending_updates=True)
    
    logger.info("Бот успешно запущен и готов к работе!")
    
    # 6. Запуск поллинга
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await redis.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен.")