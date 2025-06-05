import asyncio
import logging
import sys

from aiogram.filters import CommandStart
from aiogram.types import Message

from bot import bot
from bot_structure.bot_commands import commands
from bot_structure.setup_routers import setup_routers

dp = setup_routers()

@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        f'Добрый день, {message.from_user.full_name}! Эта секция бота предназначена только для специалистов'
        f', если вы хотите сделать запись то пожалуйста запросите ссылку у своего специалиста!\n\n'
        f'Если вы специалист то нажмите сюда /verify'
    )

async def main():
    await bot.set_my_commands(commands)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())