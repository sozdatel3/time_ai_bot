import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_dialog import setup_dialogs
from fastapi import FastAPI
from fastapi.responses import Response

from config.config import get_config, load_config, logger
from db.models.__init__ import init_db
from db.models.old_workflow.big_mes import get_pay_photo_attachment
from dialogs import register_dialogs
from handlers.payment_handler import PaymentHandler
from manager.spam_service import SpamManager
from sheduler.sheduler import setup_scheduler
from utils.astro_manager import AstroManager
from utils.midlwares import get_error_handler

bot: Bot | None = None
dp: Dispatcher | None = None
scheduler = None


async def set_commands(bot: Bot):
    # Preload media to cache file_ids inside Telegram
    base_dir = Path(__file__).resolve().parent
    await get_pay_photo_attachment(
        bot, str(base_dir / "misk" / "navigation" / "main.png")
    )
    await get_pay_photo_attachment(
        bot, str(base_dir / "misk" / "publication" / "1.png")
    )
    await get_pay_photo_attachment(
        bot, str(base_dir / "misk" / "publication" / "2.png")
    )
    await get_pay_photo_attachment(
        bot, str(base_dir / "misk" / "publication" / "3.png")
    )
    await get_pay_photo_attachment(
        bot, str(base_dir / "misk" / "publication" / "4.png")
    )

    try:
        await bot.delete_my_commands()
    except Exception as e:
        logger.info(f"Error deleting commands: {e}")

    # You can add commands here if needed
    # commands = [types.BotCommand(command="/start", description="Главное меню")]
    # await bot.set_my_commands(commands)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup()
    yield
    await shutdown()


async def startup():
    global bot, dp, scheduler

    try:
        # Init DB
        await init_db()

        # Init config and clients
        config = load_config()
        config.set_openai_client()

        # Init bot/dispatcher
        bot = Bot(
            token=config.bot.token.get_secret_value(),
            default=DefaultBotProperties(parse_mode="HTML"),
        )
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        dp.errors.register(get_error_handler(dp, bot))

        # Bot info and services
        bot_info = await bot.get_me()
        payment_handler = PaymentHandler(bot)
        config.set_bot_id(str(bot_info.id))
        config.set_bot_name(bot_info.username)
        config.set_payment_handler(payment_handler)
        spam_manager = SpamManager(bot)
        config.set_spam_manager(spam_manager)
        astro_manager = AstroManager(bot)
        config.set_astro_manager(astro_manager)

        # Dialogs
        register_dialogs(dp)
        setup_dialogs(dp)

        # Commands / preload media
        await set_commands(bot)

        # Scheduler
        scheduler = setup_scheduler(bot)
        scheduler.start()

        # Set webhook if provided
        webhook_url = os.getenv("WEBHOOK_URL", "").strip()
        if webhook_url:
            await bot.set_webhook(
                url=webhook_url,
                allowed_updates=dp.resolve_used_update_types(),
                drop_pending_updates=True,
            )
            logger.info(f"Webhook set to: {webhook_url}")
        else:
            logger.warning("WEBHOOK_URL is not set; skipping webhook setup.")
            logger.info(f"Bot @{bot_info.username} started without webhook")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise


async def shutdown():
    global bot, scheduler
    try:
        if bot:
            try:
                await bot.delete_webhook(drop_pending_updates=True)
            except Exception:
                pass
            await bot.session.close()
        if scheduler:
            scheduler.shutdown()
    except Exception as e:
        logging.error(f"Shutdown error: {e}")


app = FastAPI(
    title="TimeAI Bot Server",
    description="Telegram bot webhook server",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"status": "ok", "service": "timeai_bot"}


@app.post("/webhook")
async def telegram_webhook(update: dict):
    global bot, dp
    try:
        if bot is None or dp is None:
            return Response(status_code=503)
        telegram_update = types.Update(**update)
        # Process in background to respond fast
        asyncio.create_task(dp.feed_update(bot=bot, update=telegram_update))
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/new_registration")
async def new_registration(payload: dict):
    try:
        if bot is None:
            return Response(status_code=503)
        email = payload.get("email")
        language = payload.get("language")
        created_at = payload.get("created_at")
        total_users = payload.get("total")
        # Parse and format the created_at timestamp
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            created_at = dt.strftime("%d.%m.%Y - %H:%M")
        except Exception:
            pass  # Keep original format if parsing fails
        if not email or not language or not created_at:
            return Response(status_code=400)
        message = f"""<b><i>🎉 Новая регистрация в лист ожидания!</i></b>

<b>Email:</b> <code>{email}</code>
<b>Язык:</b> {language}
<b>Дата регистрации:</b> {created_at}

<i>Всего пользователей в ожидании запуска:</i> <b>{total_users}</b> 🚀"""
        config = get_config()
        await config.get_admin_notifier(bot)._send_to_admins(message)
        return {"status": "ok"}
    except Exception as e:
        logging.error(f"new_registration error: {e}")
        return {"status": "error", "message": str(e)}


async def run_server(host: str = "0.0.0.0", port: int = 8000):
    config_obj = uvicorn.Config(
        app=app, host=host, port=port, log_level="info"
    )
    server = uvicorn.Server(config_obj)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_server())
