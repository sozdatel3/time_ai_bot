import secrets

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    select,
    update,
)
from sqlalchemy.sql import func

from config.config import load_config
from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class AiPromo(Base, TimestampMixin):
    __tablename__ = "ai_promos"

    id = Column(Integer, primary_key=True)
    hash = Column(String, unique=True, nullable=False)
    count_of_predict = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, nullable=False)  # admin user_id who created


async def generate_promo_url(promo_hash: str) -> str:
    """Генерирует URL для промокода"""
    config = load_config()
    bot_username = config.bot.name
    return f"https://t.me/{bot_username}?start=aipromo_{promo_hash}"


async def create_ai_promo(
    created_by: int, count_of_predict: int
) -> tuple[AiPromo, str]:
    """Создает новый промокод и возвращает его вместе с URL"""
    async with AsyncSessionLocal() as session:
        # Генерируем уникальный хэш
        promo_hash = secrets.token_urlsafe(12)

        promo = AiPromo(
            hash=promo_hash,
            count_of_predict=count_of_predict,
            created_by=created_by,
        )
        session.add(promo)
        await session.commit()
        await session.refresh(promo)

        url = await generate_promo_url(promo_hash)
        return promo, url


async def get_ai_promo_by_hash(promo_hash: str, session=None) -> AiPromo:
    """Получает промокод по хэшу"""
    if session is None:
        async with AsyncSessionLocal() as session:
            stmt = select(AiPromo).where(AiPromo.hash == promo_hash)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    else:
        stmt = select(AiPromo).where(AiPromo.hash == promo_hash)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def use_ai_promo(promo_hash: str) -> tuple[bool, int]:
    """
    Использует промокод
    Возвращает (успешно ли использован, количество прогнозов)
    """
    async with AsyncSessionLocal() as session:
        promo = await get_ai_promo_by_hash(promo_hash, session)

        if promo and promo.is_active:
            # Отмечаем промокод как использованный
            stmt = (
                update(AiPromo)
                .where(AiPromo.hash == promo_hash)
                .values(is_active=False, used_at=func.now())
            )
            await session.execute(stmt)
            await session.commit()

            return True, promo.count_of_predict

        return False, 0


async def get_all_ai_promos():
    """Получает все промокоды для админки"""
    async with AsyncSessionLocal() as session:
        stmt = select(AiPromo).order_by(AiPromo.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()


async def deactivate_ai_promo(promo_id: int) -> bool:
    """Деактивирует промокод"""
    async with AsyncSessionLocal() as session:
        stmt = (
            update(AiPromo)
            .where(AiPromo.id == promo_id)
            .values(is_active=False)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
