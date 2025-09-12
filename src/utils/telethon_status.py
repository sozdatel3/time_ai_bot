# telethon_status.py


# async def set_playing_status(status_text: str = "🕹️ играет в расклады Таро"):
#     """Установить кастомный статус профиля бота (playing / любое)"""
#     # Изменяем about (bio) — это увидят в профиле
#     await telethon_client(functions.account.UpdateProfile(about=status_text))
#     print(f"✅ Статус обновлён: {status_text}")
# # Пример запуска
# if __name__ == "__main__":
#     asyncio.run(set_playing_status("🕹️ играет в расклады Таро"))
# telethon_status.py
from telethon import functions, types

from config.config import get_config


async def send_playing_action(user_id: int):
    telethon_client = get_config().bot.telethon_client

    await telethon_client(
        functions.messages.SetTypingRequest(
            peer=user_id,
            action=types.SendMessageGamePlayAction(),
            # peer=user_id, action=types.SendM
        )
    )

    print(f"✅ Отправил playing 🕹️ action в чат {user_id}")
