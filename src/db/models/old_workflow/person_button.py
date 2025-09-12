from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class PersonButton(Base, TimestampMixin):
    __tablename__ = "person_button"

    id = Column(Integer, primary_key=True)
    button_name = Column(String, nullable=False)
    person_id = Column(Integer, nullable=False)
    count = Column(Integer, default=1)


async def increment_tap_person_button(
    button_name: str, person_id: int
) -> None:
    """Увеличивает счетчик нажатий для кнопки"""
    async with AsyncSessionLocal() as session:
        person_button = await session.execute(
            select(PersonButton).where(
                PersonButton.button_name == button_name,
                PersonButton.person_id == person_id,
            )
        )
        if person_button.scalar_one_or_none():
            await session.execute(
                update(PersonButton)
                .where(
                    PersonButton.button_name == button_name,
                    PersonButton.person_id == person_id,
                )
                .values(count=PersonButton.count + 1)
            )
        else:
            tap = PersonButton(button_name=button_name, person_id=person_id)
            session.add(tap)
        await session.commit()


async def get_button_statistics_person_button(
    session: AsyncSession,
    button_name: str,
    person_id: int,
    start_date: datetime = None,
    end_date: datetime = None,
) -> dict:
    """Получает статистику для конкретной кнопки"""
    # Базовый запрос для подсчета всех нажатий
    total_query = (
        select(func.count())
        .select_from(PersonButton)
        .where(
            PersonButton.button_name == button_name,
            PersonButton.person_id == person_id,
        )
    )

    # Получаем общее количество нажатий
    total_taps = await session.scalar(total_query)

    # Получаем дату первого нажатия
    first_tap_date = await session.scalar(
        select(func.min(PersonButton.created_at)).where(
            PersonButton.button_name == button_name,
            PersonButton.person_id == person_id,
        )
    )

    # Вычисляем среднее количество нажатий в день за все время
    if first_tap_date and total_taps:
        days_all = (datetime.now(timezone.utc) - first_tap_date).days or 1
        avg_taps_per_day = round(total_taps / days_all, 1)
    else:
        avg_taps_per_day = 0

    # Если указан период, получаем статистику за период
    period_taps = None
    avg_taps_per_day_period = None
    if start_date and end_date:
        period_query = total_query.where(
            PersonButton.created_at.between(start_date, end_date)
        )
        period_taps = await session.scalar(period_query)

        days_period = (end_date - start_date).days or 1
        avg_taps_per_day_period = (
            round(period_taps / days_period, 1) if period_taps else 0
        )

    return {
        "total_taps": total_taps or 0,
        "avg_taps_per_day": avg_taps_per_day,
        "period_taps": period_taps,
        "avg_taps_per_day_period": avg_taps_per_day_period,
    }


async def get_all_buttons_statistics_person_button(
    session: AsyncSession,
    start_date: datetime = None,
    end_date: datetime = None,
) -> dict:
    """Получает статистику по всем кнопкам"""
    # Получаем список всех кнопок
    buttons = await session.execute(
        select(PersonButton.button_name)
        .group_by(PersonButton.button_name)
        .order_by(func.count().desc())  # Сортируем по популярности
    )
    buttons = [row[0] for row in buttons]

    # Собираем статистику по каждой кнопке
    stats = {}
    for button in buttons:
        stats[button] = await get_button_statistics_person_button(
            session, button, start_date, end_date
        )

    return stats


async def get_users_by_button_taps(
    button_name: str, taps: int, and_more: bool = False
) -> list[int]:
    """Получает список пользователей, для которых количество нажатий по кнопке
    exactly равно заданному значению taps."""
    async with AsyncSessionLocal() as session:
        if not and_more:
            result = await session.execute(
                select(PersonButton.person_id).where(
                    PersonButton.button_name == button_name,
                    PersonButton.count == taps,
                )
            )
        else:
            result = await session.execute(
                select(PersonButton.person_id).where(
                    PersonButton.button_name == button_name,
                    PersonButton.count >= taps,
                )
            )
        users = [row[0] for row in result]
    return users
