import asyncio
from typing import Dict

from aiogram.types import Message
from sqlalchemy import Column, ForeignKey, Integer, String, delete, select
from sqlalchemy.orm import relationship

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class PermanentBroadcast(Base, TimestampMixin):
    __tablename__ = "permanent_broadcasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)  # Название рассылки для админа
    message_id = Column(Integer)  # ID сообщения для пересылки
    chat_id = Column(Integer)  # ID чата, откуда пересылать
    target_group = Column(String)  # Тип целевой аудитории

    # Связь с таблицей статусов
    delivery_statuses = relationship(
        "PermanentBroadcastStatus", back_populates="broadcast"
    )


class PermanentBroadcastStatus(Base, TimestampMixin):
    __tablename__ = "permanent_broadcast_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    broadcast_id = Column(Integer, ForeignKey("permanent_broadcasts.id"))
    user_id = Column(Integer)
    status = Column(String)  # delivered/failed

    # Связь с рассылкой
    broadcast = relationship(
        "PermanentBroadcast", back_populates="delivery_statuses"
    )


async def create_permanent_broadcast(
    name: str, message_id: int, chat_id: int, target_group: str
) -> PermanentBroadcast:
    async with AsyncSessionLocal() as session:
        broadcast = PermanentBroadcast(
            name=name,
            message_id=message_id,
            chat_id=chat_id,
            target_group=target_group,
        )
        session.add(broadcast)
        await session.commit()
        await session.refresh(broadcast)
        return broadcast


async def get_permanent_broadcasts():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PermanentBroadcast))
        return result.scalars().all()


async def get_permanent_broadcast(broadcast_id: int) -> PermanentBroadcast:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PermanentBroadcast).where(
                PermanentBroadcast.id == broadcast_id
            )
        )
        return result.scalar_one_or_none()


async def delete_permanent_broadcast(broadcast_id: int):
    async with AsyncSessionLocal() as session:
        # Удаляем сначала все статусы доставки
        await session.execute(
            delete(PermanentBroadcastStatus).where(
                PermanentBroadcastStatus.broadcast_id == broadcast_id
            )
        )
        # Затем удаляем саму рассылку
        await session.execute(
            delete(PermanentBroadcast).where(
                PermanentBroadcast.id == broadcast_id
            )
        )
        await session.commit()


async def mark_broadcast_delivered(user_id: int, broadcast_id: int):
    async with AsyncSessionLocal() as session:
        status = PermanentBroadcastStatus(
            broadcast_id=broadcast_id, user_id=user_id, status="delivered"
        )
        session.add(status)
        await session.commit()


async def mark_broadcast_failed(user_id: int, broadcast_id: int):
    async with AsyncSessionLocal() as session:
        status = PermanentBroadcastStatus(
            broadcast_id=broadcast_id, user_id=user_id, status="failed"
        )
        session.add(status)
        await session.commit()


async def get_broadcast_status(broadcast_id: int, user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PermanentBroadcastStatus).where(
                PermanentBroadcastStatus.broadcast_id == broadcast_id,
                PermanentBroadcastStatus.user_id == user_id,
            )
        )
        status = result.scalar_one_or_none()
        return status.status if status else None


async def get_users_with_status(broadcast_id: int, status: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PermanentBroadcastStatus.user_id).where(
                PermanentBroadcastStatus.broadcast_id == broadcast_id,
                PermanentBroadcastStatus.status == status,
            )
        )
        return result.scalars().all()


async def broadcast_permanent(
    message: Message, users, broadcast_id: int
) -> Dict[str, int]:
    success_count = 0
    fail_count = 0
    skipped_count = 0

    async with AsyncSessionLocal() as session:
        # Получаем список пользователей, которые уже получили это сообщение
        delivered_users = select(PermanentBroadcastStatus.user_id).where(
            PermanentBroadcastStatus.broadcast_id == broadcast_id,
            PermanentBroadcastStatus.status == "delivered",
        )
        result = await session.execute(delivered_users)
        already_received = {r[0] for r in result.all()}

        # Отправляем только тем, кто еще не получал
        for user in users:
            if user in already_received:
                skipped_count += 1
                continue

            try:
                await message.copy_to(user)
                await mark_broadcast_delivered(user, broadcast_id)
                success_count += 1
            except Exception:
                await mark_broadcast_failed(user, broadcast_id)
                fail_count += 1

            await asyncio.sleep(0.05)

    return {
        "success": success_count,
        "fail": fail_count,
        "skipped": skipped_count,
    }


async def permanent_broadcast_for_everybody(
    message: Message, users, broadcast_id: int
):
    try:
        results = await broadcast_permanent(message, users, broadcast_id)
    except Exception as e:
        print(f"Error: {e}")
        await message.bot.send_message(
            message.chat.id, f"Произошла ошибка при отправке рассылки. {e}"
        )

    await message.bot.send_message(
        message.chat.id,
        f"Рассылка завершена.\n"
        f"Успешно: {results['success']}\n"
        f"Не удалось: {results['fail']}\n"
        f"Пропущено (уже получили): {results['skipped']}",
    )
