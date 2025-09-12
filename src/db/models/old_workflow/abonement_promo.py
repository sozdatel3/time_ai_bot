import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    select,
)
from sqlalchemy.orm import relationship

from db.db import AsyncSessionLocal, Base


class AbonementPromo(Base):
    __tablename__ = "abonement_promos"

    id = Column(Integer, primary_key=True)
    promo_code = Column(String, unique=True, nullable=False)
    games_count = Column(Integer, nullable=False)
    months = Column(Integer, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    used_by = Column(Integer, ForeignKey("users.user_id"), nullable=True)

    user = relationship("User")


async def create_abonement_promo(games_count: int, months: int) -> str:
    async with AsyncSessionLocal() as session:
        promo_code = str(uuid.uuid4())[:8]
        promo = AbonementPromo(
            promo_code=promo_code, games_count=games_count, months=months
        )
        session.add(promo)
        await session.commit()
        return promo_code


async def use_abonement_promo(
    user_id: int, promo_code: str
) -> tuple[bool, int, int]:
    async with AsyncSessionLocal() as session:
        stmt = select(AbonementPromo).where(
            AbonementPromo.promo_code == promo_code,
            AbonementPromo.is_used == False,
        )
        result = await session.execute(stmt)
        promo = result.scalar_one_or_none()

        if promo:
            promo.is_used = True
            promo.used_by = user_id
            await session.commit()
            return True, promo.games_count, promo.months
        return False, 0, 0
