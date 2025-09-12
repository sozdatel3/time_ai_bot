from sqlalchemy import (
    Column,
    Integer,
    select,
)

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class FirstMes(Base, TimestampMixin):
    __tablename__ = "first_mes"

    user_id = Column(Integer, primary_key=True)
    first_mes_id = Column(Integer)


async def create_black_first_mes(user_id: int, first_mes_id: int):
    async with AsyncSessionLocal() as session:
        existing_first_mes = (
            await session.execute(
                select(FirstMes).where(FirstMes.user_id == user_id)
            )
        ).scalar_one_or_none()
        if existing_first_mes:
            existing_first_mes.first_mes_id = first_mes_id
            await session.commit()
            return existing_first_mes
        first_mes = FirstMes(user_id=user_id, first_mes_id=first_mes_id)
        session.add(first_mes)
        await session.commit()
        return first_mes


async def get_black_first_mes(user_id: int) -> FirstMes:
    async with AsyncSessionLocal() as session:
        stmt = select(FirstMes).where(FirstMes.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def delete_black_first_mes(bot, user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(FirstMes).where(FirstMes.user_id == user_id)
        result = await session.execute(stmt)
        first_mes = result.scalar_one_or_none()
        if first_mes:
            try:
                await bot.delete_message(user_id, first_mes.first_mes_id)
            except Exception as e:
                print(e)
            await session.delete(first_mes)
            await session.commit()


async def try_to_del_and_add_new_first_mes(
    bot, user_id: int, first_mes_id: int
):
    try:
        await delete_black_first_mes(bot, user_id)
    except Exception as e:
        print(e)
    await create_black_first_mes(user_id, first_mes_id)
