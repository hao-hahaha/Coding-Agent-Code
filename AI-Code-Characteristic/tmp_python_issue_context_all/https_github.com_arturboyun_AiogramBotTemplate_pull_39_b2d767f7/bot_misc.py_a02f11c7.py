# Dispatcher
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisStorage

from bot.config import get_config

config = get_config()

key_builder = DefaultKeyBuilder(with_destiny=True)
storage = RedisStorage.from_url(str(config.REDIS_DSN), key_builder=key_builder)
dp = Dispatcher(storage=storage)

# Bot
default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
bot = Bot(token=config.BOT_TOKEN, default=default_bot_properties)
