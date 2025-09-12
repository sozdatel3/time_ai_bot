from typing import List, Optional

from sqlalchemy import Column, Float, ForeignKey, Integer, Sequence, String

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin
from utils.api import get_api


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id = Column(
        Integer,
        Sequence("order_id_seq", start=200, increment=1),
        primary_key=True,
    )
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    product = Column(String, nullable=False)
    game_id = Column(Integer, nullable=True)
    balance_to_use = Column(Integer, default=0)


async def create_order(
    user_id: int,
    amount: float,
    status: str,
    product: str,
    game_id: int,
    balance_to_use: int = 0,
) -> Order:
    async with AsyncSessionLocal() as session:
        order = Order(
            user_id=user_id,
            amount=amount,
            status=status,
            product=product,
            game_id=game_id,
            balance_to_use=balance_to_use,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)

    try:
        custom_fields = {"product": product, "game_id": game_id}
        await get_api().send_payment_info(
            inv_id=str(order.id),
            user_id=str(user_id),
            amount=int(amount),
            custom_fields=custom_fields,
        )
    except Exception as e:
        print(f"Ошибка при отправке информации о заказе на сервер: {e}")

    return order


async def create_initial_order() -> None:
    async with AsyncSessionLocal() as session:
        # Проверяем, существует ли уже заказ с id 200
        order = await session.get(Order, 2222)
        if not order:
            initial_order = Order(
                id=2222,
                user_id=0,
                amount=0,
                status="test",
                product="test",
            )
            session.add(initial_order)

            await session.commit()


async def get_user_orders(user_id: int) -> List[Order]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            Order.__table__.select()
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()


async def update_order_status(
    order_id: int, new_status: str
) -> Optional[Order]:
    async with AsyncSessionLocal() as session:
        order = await session.get(Order, order_id)
        if order:
            order.status = new_status
            await session.commit()
    return order


async def get_order(order_id: int) -> Optional[Order]:
    async with AsyncSessionLocal() as session:
        return await session.get(Order, order_id)
