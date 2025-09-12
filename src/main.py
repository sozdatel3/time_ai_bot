import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs

from config.config import load_config
from db.models.__init__ import init_db
from dialogs import register_dialogs
from handlers.payment_handler import PaymentHandler
from manager.spam_service import SpamManager
from sheduler.sheduler import setup_scheduler
from utils.api import init_api
from utils.astro_manager import AstroManager
from utils.midlwares import get_error_handler


async def set_commands(bot: Bot):
    await bot.delete_my_commands()
    commands = [
        types.BotCommand(command="/start", description="Главное меню"),
        # types.BotCommand(command="/services", description=" 🪶 Мои услуги"),
    ]
    await bot.set_my_commands(commands)


async def main():
    config = load_config()
    bot = Bot(
        token=config.bot.token.get_secret_value(),
        default=DefaultBotProperties(parse_mode="HTML"),
    )
    # await run_migrations()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.errors.register(get_error_handler(dp, bot))
    # dp.chat_join_request.register(handle_join_request)

    bot_info = await bot.get_me()

    payment_handler = PaymentHandler(bot)
    config.set_bot_id(str(bot_info.id))
    config.set_bot_name(bot_info.username)
    print(bot_info.username)
    config.set_payment_handler(payment_handler)
    spam_manager = SpamManager(bot)
    config.set_spam_manager(spam_manager)
    astro_manager = AstroManager(bot)
    config.set_astro_manager(astro_manager)
    config.set_openai_client()

    # Инициализация API
    api = init_api(config)
    await api.initialize()
    api_token = await api.send_bot_info()
    config.set_bot_token(api_token["token"])

    # Инициализация базы данных
    await init_db()

    register_dialogs(dp)
    setup_dialogs(dp)

    # Устанавливаем команды бота
    await set_commands(bot)

    scheduler = setup_scheduler(bot)
    scheduler.start()
    # API_ID = config.bot.api_id
    # API_HASH = config.bot.api_hash
    # BOT_TOKEN = config.bot.token.get_secret_value()

    # telethon_client = TelegramClient("bot_playing", API_ID, API_HASH)
    # config.set_telethon_client(telethon_client)
    # await telethon_client.start(bot_token=BOT_TOKEN)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        # await telethon_client.disconnect()
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
