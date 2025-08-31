import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from handlers import register_handlers
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from dotenv import load_dotenv
load_dotenv()


async def main():
    logging.basicConfig(level=logging.INFO)

    redis = Redis(host="localhost", port=6379, db=0) 
    storage = RedisStorage(redis=redis)
    
    # import from .env file
    API_TOKEN = os.getenv("TELEGRAM_API_TOKEN") 
    
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=storage)

    register_handlers(dp, bot)

    await dp.start_polling(bot, polling_timeout=100)


if __name__ == "__main__":
    asyncio.run(main())