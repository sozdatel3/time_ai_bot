from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    delete,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class Coupon(Base, TimestampMixin):
    __tablename__ = "coupons"

    coupon_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service_name = Column(String)
    amount = Column(Float, default=0.0)
    percent = Column(Float, default=0.0)
    used = Column(Boolean, default=False)


async def create_coupon(
    user_id: int, service_name: str, amount: float = 0.0, percent: float = 0.0
) -> Coupon:
    async with AsyncSessionLocal() as session:
        new_coupon = Coupon(
            user_id=user_id,
            service_name=service_name,
            amount=amount,
            percent=percent,
        )
        session.add(new_coupon)
        await session.commit()
        await session.refresh(new_coupon)
    return new_coupon


async def get_coupon(coupon_id: int) -> Coupon | None:
    async with AsyncSessionLocal() as session:
        stmt = select(Coupon).where(Coupon.coupon_id == coupon_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_user_coupons(user_id: int) -> list[Coupon]:
    async with AsyncSessionLocal() as session:
        stmt = select(Coupon).where(Coupon.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()


async def delete_coupon(coupon_id: int) -> None:
    async with AsyncSessionLocal() as session:
        stmt = delete(Coupon).where(Coupon.coupon_id == coupon_id)
        await session.execute(stmt)
        await session.commit()


async def use_coupon(
    coupon_id: int, session: AsyncSession
) -> tuple[float, float]:
    stmt = select(Coupon).where(Coupon.coupon_id == coupon_id)
    result = await session.execute(stmt)
    coupon = result.scalar_one_or_none()

    if coupon:
        amount = coupon.amount
        percent = coupon.percent
        await session.delete(coupon)
        return amount, percent
    else:
        return 0.0, 0.0
