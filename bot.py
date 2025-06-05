import os

from dotenv import load_dotenv
from aiogram import Bot

load_dotenv()

bot = Bot(os.getenv('BOT_TOKEN'))