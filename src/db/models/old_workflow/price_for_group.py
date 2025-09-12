from sqlalchemy import ForeignKey, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin
from db.models.price import BASE_PRICES


class PriceForGroup(Base, TimestampMixin):
    __tablename__ = "price_for_group"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_number: Mapped[int] = mapped_column(
        ForeignKey("ab_groups.group_number")
    )
    service_name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int]  # Цена для группы


async def set_group_price(
    group_number: int, service_name: str, amount: int
) -> None:
    async with AsyncSessionLocal() as session:
        # Проверяем существует ли уже цена для этой группы и сервиса
        stmt = select(PriceForGroup).where(
            PriceForGroup.group_number == group_number,
            PriceForGroup.service_name == service_name,
        )
        result = await session.execute(stmt)
        price = result.scalar_one_or_none()

        if price is None:
            price = PriceForGroup(
                group_number=group_number,
                service_name=service_name,
                amount=amount,
            )
            session.add(price)
        else:
            price.amount = amount

        await session.commit()


async def get_price_for_user(user_id: int, service_name: str) -> int:
    from db.models.user import get_user_group

    group_number = await get_user_group(user_id)
    return await get_price_for_group(group_number, service_name)


async def get_price_for_group(group_number: int, service_name: str) -> int:
    """Получает цену для конкретной группы и сервиса"""
    from db.models.price import get_price

    if group_number == 0:
        return await get_price(service_name)

    async with AsyncSessionLocal() as session:
        stmt = select(PriceForGroup).where(
            PriceForGroup.group_number == group_number,
            PriceForGroup.service_name == service_name,
        )
        result = await session.execute(stmt)
        price = result.scalar_one_or_none()

        # Если специальной цены нет, возвращаем базовую
        if price is None:
            return await get_price(service_name, session)

        return price.amount


async def init_group_prices(
    group_number: int, session: AsyncSession | None = None
) -> None:
    """Инициализирует базовые цены для новой группы"""
    from db.models.price import get_price

    if session is None:
        async with AsyncSessionLocal() as session:
            for service_name, base_price in BASE_PRICES.items():
                # print("SESSION")
                # print(await get_price(service_name, session))
                price = PriceForGroup(
                    group_number=group_number,
                    service_name=service_name,
                    # amount=base_price,
                    amount=await get_price(service_name, session),
                )
                session.add(price)
            await session.commit()
    else:
        for service_name, base_price in BASE_PRICES.items():
            # print(f"ELSEEEEEE = {service_name}")
            # print(await get_price(service_name, session))
            price = PriceForGroup(
                group_number=group_number,
                service_name=service_name,
                amount=await get_price(service_name, session),
            )
            session.add(price)
        await session.commit()


async def delete_all_group_prices(session=None) -> int:
    """Удаляет все записи о группах. Возвращает количество удаленных записей"""
    if session is None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PriceForGroup))
            prices = result.scalars().all()
            count = len(prices)
            for price in prices:
                await session.delete(price)
            await session.commit()
            return count
    else:
        result = await session.execute(select(PriceForGroup))
        prices = result.scalars().all()
        count = len(prices)
        for price in prices:
            await session.delete(price)
        await session.commit()
        return count
