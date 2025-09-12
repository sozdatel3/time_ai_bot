from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    Integer,
    String,
    func,
    select,
    update,
)
from sqlalchemy.orm import relationship

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin
from db.models.order import Order

# class UserStatus(str, Enum):
#     NO_USE_TEST = "no_use_test"
#     USING_TEST_NOW = "use_test"
#     TEST_USED = "test_used"

#     USE_SUBSCRIPTION = "use_subscription"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    refer_id = Column(Integer, default=None)

    username = Column(String)
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    balance = Column(Float, default=0.0)
    frozen_balance = Column(Float, default=0.0)
    balance_to_use_this_month = Column(Float, default=0.0)
    questions = relationship("Question", back_populates="user")
    recived_inactive_spam = Column(Boolean, default=False)

    free_predictions_count = Column(Integer, default=1)

    ab_test_group = Column(Integer, default=0)

    received_certificates = relationship(
        "Certificate",
        foreign_keys="Certificate.recipient_id",
        back_populates="recipient",
    )
    sent_certificates = relationship(
        "Certificate",
        foreign_keys="Certificate.sender_id",
        back_populates="sender",
    )

    language = Column(String, nullable=True)


async def get_user_language(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.language).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def set_language(user_id: int, language: str):
    async with AsyncSessionLocal() as session:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(language=language)
        )
        await session.execute(stmt)
        await session.commit()


async def do_we_know_user_language(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.language).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none() is not None


async def get_all_users_ids():
    async with AsyncSessionLocal() as session:
        stmt = select(User.user_id)
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_all_users_ids_with_recived_inactive_spam():
    async with AsyncSessionLocal() as session:
        stmt = select(User.user_id).where()
        result = await session.execute(stmt)

        return result.scalars().all()


async def set_recived_inactive_spam(
    user_id: int, recived_inactive_spam: bool
) -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(recived_inactive_spam=recived_inactive_spam)
        )
        await session.execute(stmt)
        await session.commit()


async def set_name(user_id: int, name: str) -> None:
    async with AsyncSessionLocal() as session:
        stmt = update(User).where(User.user_id == user_id).values(name=name)
        await session.execute(stmt)
        await session.commit()


async def get_name(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        stmt = select(User.name).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_phone(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        stmt = select(User.phone).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def set_phone(user_id: int, phone: str) -> None:
    async with AsyncSessionLocal() as session:
        stmt = update(User).where(User.user_id == user_id).values(phone=phone)
        await session.execute(stmt)
        await session.commit()


async def create_user(user_id: int, username: str = "") -> User:
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.first()
        if user:
            user = user[0]
            user.username = username
        else:
            user = User(user_id=user_id, username=username)
            session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def get_user(user_id: int) -> User:
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
    return user


async def get_user_balance(user_id: int) -> float:
    async with AsyncSessionLocal() as session:
        stmt = select(User.balance).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_user_group(user_id: int) -> int:
    user = await get_user(user_id)
    return user.ab_test_group


async def update_user_balance(
    user_id: int,
    new_balance: float,
    froze: bool = False,
    froze_value: float = 0,
) -> None:

    async with AsyncSessionLocal() as session:
        if froze:
            stmt = (
                update(User)
                .where(User.user_id == user_id)
                .values(frozen_balance=froze_value, balance=new_balance)
            )
        else:
            stmt = (
                update(User)
                .where(User.user_id == user_id)
                .values(balance=new_balance)
            )

        await session.execute(stmt)
        await session.commit()


async def get_user_balance_to_use_this_month(user_id: int) -> float:

    async with AsyncSessionLocal() as session:
        stmt = select(User.balance_to_use_this_month).where(
            User.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def update_user_balance_to_use_this_month(
    user_id: int, new_balance_to_use_this_month: float
) -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(balance_to_use_this_month=new_balance_to_use_this_month)
        )
        await session.execute(stmt)
        await session.commit()


async def update_user_frozen_balance(user_id: int, sub_balance: float) -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(frozen_balance=User.frozen_balance - sub_balance)
        )
        await session.execute(stmt)
        await session.commit()


async def get_all_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        return [dict(row._mapping) for row in result.all()]


async def get_all_user_ids():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User.user_id))
        return result.scalars().all()


async def get_users_bought():
    async with AsyncSessionLocal() as session:
        #  Создаем запрос, который выбирает уникальных пользователей
        # у которых есть заказы со статусом "completed"
        stmt = (
            select(User.user_id)
            .distinct()
            .join(Order)
            .where(Order.status == "completed")
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_users_not_bought():
    async with AsyncSessionLocal() as session:
        # Подзапрос для получения user_id с completed заказами
        completed_users = (
            select(User.user_id)
            .distinct()
            .join(Order)
            .where(Order.status == "completed")
        ).scalar_subquery()

        # Основной запрос для получения пользователей, которых нет в подзапросе
        stmt = select(User.user_id).where(User.user_id.not_in(completed_users))
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_users_not_bought_but():
    async with AsyncSessionLocal() as session:
        # Подзапрос для получения user_id с completed заказами
        completed_users = (
            select(User.user_id)
            .distinct()
            .join(Order)
            .where(Order.status == "completed")
        ).scalar_subquery()

        # Основной запрос: пользователи с pending заказами, которых нет в completed
        stmt = (
            select(User.user_id)
            .distinct()
            .join(Order)
            .where(
                User.user_id.not_in(completed_users), Order.status == "pending"
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_users_today():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.user_id).where(
                func.date(User.created_at) == datetime.now().date()
            )
        )
        return result.scalars().all()


async def get_users_not_today():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User.user_id).where(
                func.date(User.created_at) != datetime.now().date()
            )
        )
        return result.scalars().all()


async def get_users_by_ab_group(group_number: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.user_id).where(User.ab_test_group == group_number)
        result = await session.execute(stmt)
        return result.scalars().all()


async def update_user_refer_id(user_id: int, refer_id: int) -> None:
    async with AsyncSessionLocal() as session:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(refer_id=refer_id)
        )
        await session.execute(stmt)
        await session.commit()


async def get_ab_group(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.ab_test_group).where(User.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def get_user_created_at(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.created_at).where(User.user_id == user_id)
        result = await session.execute(stmt)
        created_at = result.scalar_one_or_none()
        if created_at:
            return created_at.strftime("%d.%m.%y")
        return None


async def get_free_predictions_count(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.free_predictions_count).where(
            User.user_id == user_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


async def set_user_free_predictions_count(user_id: int, count: int):
    async with AsyncSessionLocal() as session:
        stmt = (
            update(User)
            .where(User.user_id == user_id)
            .values(free_predictions_count=count)
        )
        await session.execute(stmt)
        await session.commit()


async def increase_free_predictions_count(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.free_predictions_count).where(
            User.user_id == user_id
        )
        result = await session.execute(stmt)
        current_count = result.scalar_one_or_none()
        if current_count is not None:
            stmt = (
                update(User)
                .where(User.user_id == user_id)
                .values(free_predictions_count=current_count + 1)
            )
            await session.execute(stmt)
            await session.commit()


async def decrease_free_predictions_count(user_id: int):
    async with AsyncSessionLocal() as session:
        stmt = select(User.free_predictions_count).where(
            User.user_id == user_id
        )
        result = await session.execute(stmt)
        current_count = result.scalar_one_or_none()

        if current_count is not None and current_count > 0:
            stmt = (
                update(User)
                .where(User.user_id == user_id)
                .values(free_predictions_count=current_count - 1)
            )
            await session.execute(stmt)
            await session.commit()
