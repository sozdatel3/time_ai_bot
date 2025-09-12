from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class YogaTap(Base, TimestampMixin):
    __tablename__ = "yoga_tap"

    id = Column(Integer, primary_key=True)
    button_name = Column(String, nullable=False)
    tap_datetime = Column(DateTime, default=datetime.utcnow, nullable=False)


async def increment_tap(button_name: str) -> None:
    """Увеличивает счетчик нажатий для кнопки"""
    async with AsyncSessionLocal() as session:
        tap = YogaTap(button_name=button_name)
        session.add(tap)
        await session.commit()


async def get_button_statistics(
    session: AsyncSession,
    button_name: str,
    start_date: datetime = None,
    end_date: datetime = None,
) -> dict:
    """Получает статистику для конкретной кнопки"""
    # Базовый запрос для подсчета всех нажатий
    total_query = (
        select(func.count())
        .select_from(YogaTap)
        .where(YogaTap.button_name == button_name)
    )

    # Получаем общее количество нажатий
    total_taps = await session.scalar(total_query)

    # Получаем дату первого нажатия
    first_tap_date = await session.scalar(
        select(func.min(YogaTap.tap_datetime)).where(
            YogaTap.button_name == button_name
        )
    )

    # Вычисляем среднее количество нажатий в день за все время
    if first_tap_date and total_taps:
        days_all = (datetime.utcnow() - first_tap_date).days or 1
        avg_taps_per_day = round(total_taps / days_all, 1)
    else:
        avg_taps_per_day = 0

    # Если указан период, получаем статистику за период
    period_taps = None
    avg_taps_per_day_period = None
    if start_date and end_date:
        period_query = total_query.where(
            YogaTap.tap_datetime.between(start_date, end_date)
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


async def get_all_buttons_statistics(
    session: AsyncSession,
    start_date: datetime = None,
    end_date: datetime = None,
) -> dict:
    """Получает статистику по всем кнопкам"""
    # Получаем список всех кнопок
    buttons = await session.execute(
        select(YogaTap.button_name)
        .group_by(YogaTap.button_name)
        .order_by(func.count().desc())  # Сортируем по популярности
    )
    buttons = [row[0] for row in buttons]

    # Собираем статистику по каждой кнопке
    stats = {}
    for button in buttons:
        stats[button] = await get_button_statistics(
            session, button, start_date, end_date
        )

    return stats
