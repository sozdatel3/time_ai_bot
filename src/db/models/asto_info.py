from pathlib import Path

from sqlalchemy import (
    JSON,
    Column,
    Float,
    Integer,
    String,
    select,
    update,
)

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin

# class UserStatus(str, Enum):
#     NO_USE_TEST = "no_use_test"
#     USING_TEST_NOW = "use_test"
#     TEST_USED = "test_used"

#     USE_SUBSCRIPTION = "use_subscription"


class AstroInfo(Base, TimestampMixin):
    __tablename__ = "astro_info"

    user_id = Column(Integer, unique=True, primary_key=True)
    name = Column(String)
    birth_year = Column(Integer)
    birth_month = Column(Integer)
    birth_day = Column(Integer)
    birth_hour = Column(Integer)
    birth_minute = Column(Integer)
    lng = Column(Float)
    lat = Column(Float)
    city = Column(String)
    country = Column(String)
    natal_json = Column(JSON)
    natal_svg = Column(String)


async def set_astro_info(
    user_id: int,
    name: str,
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int,
    birth_minute: int,
    lng: float,
    lat: float,
    city: str,
    country: str,
) -> None:

    async with AsyncSessionLocal() as session:
        stmt = select(AstroInfo).where(AstroInfo.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Если пользователь существует, обновляем его данные
            stmt = (
                update(AstroInfo)
                .where(AstroInfo.user_id == user_id)
                .values(
                    name=name,
                    birth_year=birth_year,
                    birth_month=birth_month,
                    birth_day=birth_day,
                    birth_hour=birth_hour,
                    birth_minute=birth_minute,
                    lng=lng,
                    lat=lat,
                    city=city,
                    country=country,
                )
            )
            await session.execute(stmt)
        else:

            user = AstroInfo(
                user_id=user_id,
                name=name,
                birth_year=birth_year,
                birth_month=birth_month,
                birth_day=birth_day,
                birth_hour=birth_hour,
                birth_minute=birth_minute,
                lng=lng,
                lat=lat,
                city=city,
                country=country,
            )
            session.add(user)

        await session.commit()


async def get_astro_info(user_id: int) -> dict:
    async with AsyncSessionLocal() as session:
        stmt = select(AstroInfo).where(AstroInfo.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def set_natal_json(user_id: int, natal_json: dict) -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            update(AstroInfo)
            .where(AstroInfo.user_id == user_id)
            .values(natal_json=natal_json)
        )
        await session.execute(stmt)
        await session.commit()


async def get_natal_json(user_id: int) -> dict:
    async with AsyncSessionLocal() as session:
        stmt = select(AstroInfo.natal_json).where(AstroInfo.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def set_natal_svg(user_id: int, natal_svg) -> None:
    async with AsyncSessionLocal() as session:
        # Convert Path to string if needed
        svg_path = str(natal_svg) if isinstance(natal_svg, Path) else natal_svg

        stmt = (
            update(AstroInfo)
            .where(AstroInfo.user_id == user_id)
            .values(natal_svg=svg_path)
        )
        await session.execute(stmt)
        await session.commit()


async def get_natal_svg(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        stmt = select(AstroInfo.natal_svg).where(AstroInfo.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
