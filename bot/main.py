import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from .config import settings
from .database import init_db
from .handlers import admin_router, order_router, supplier_router, message_router


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan():
    """Initialize database and other resources"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully!")
    yield


async def main():
    """Main bot function"""
    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    )
    
    # Initialize storage (Redis or Memory)
    try:
        import redis
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True
        )
        redis_client.ping()  # Test connection
        storage = RedisStorage(redis_client)
        logger.info("Using Redis storage")
    except Exception as e:
        logger.warning(f"Redis not available, using memory storage: {e}")
        storage = MemoryStorage()
    
    # Initialize dispatcher
    dp = Dispatcher(storage=storage)
    
    # Include routers
    dp.include_router(admin_router)
    dp.include_router(order_router)
    dp.include_router(supplier_router)
    dp.include_router(message_router)
    
    # Start bot
    logger.info("Starting bot...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise
