import asyncio
from aiogram import Bot, Dispatcher
from config import TG_TOKEN
from handlers import router

import logging
logging.basicConfig(level=logging.INFO)

### Main function to start bot pooling ###
async def main():
    bot = Bot(token=TG_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
