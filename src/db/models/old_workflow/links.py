from uuid import uuid4

from sqlalchemy import Column, Integer, String, select, update

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class BotLink(Base, TimestampMixin):
    __tablename__ = "bot_links"

    id = Column(Integer, primary_key=True)
    name = Column(
        String, unique=True, nullable=False
    )  # Имя ссылки для администратора
    link_code = Column(
        String, unique=True, nullable=False
    )  # Уникальный код для ссылки
    clicks = Column(Integer, default=0)  # Счетчик переходов
    description = Column(String, nullable=True)  # Опциональное описание


async def create_bot_link(
    name: str, link_code: str | None = None, description: str | None = None
) -> BotLink:
    async with AsyncSessionLocal() as session:
        # Генерируем короткий уникальный код, если он не предоставлен
        if link_code is None:
            link_code = str(uuid4())[:8]

        link = BotLink(name=name, link_code=link_code, description=description)
        session.add(link)
        await session.commit()
        await session.refresh(link)
        return link


async def get_bot_link(link_code: str) -> BotLink | None:
    async with AsyncSessionLocal() as session:
        stmt = select(BotLink).where(BotLink.link_code == link_code)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def increment_link_clicks(link_code: str) -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            update(BotLink)
            .where(BotLink.link_code == link_code)
            .values(clicks=BotLink.clicks + 1)
        )
        await session.execute(stmt)
        await session.commit()


async def get_all_links() -> list[BotLink]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(BotLink))
        return result.scalars().all()
