from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class ABGroup(Base, TimestampMixin):
    __tablename__ = "ab_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))  # Название разбиения
    group_number: Mapped[int]  # Номер группы
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


async def create_ab_group(
    name: str,
    group_number: int,
    description: str = None,
    session: AsyncSession | None = None,
) -> ABGroup:
    if session is None:
        async with AsyncSessionLocal() as session:
            group = ABGroup(
                name=name, group_number=group_number, description=description
            )
            session.add(group)
            await session.commit()
            await session.refresh(group)
            return group
    else:
        group = ABGroup(
            name=name, group_number=group_number, description=description
        )
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group


async def get_ab_groups() -> List[ABGroup]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ABGroup).order_by(ABGroup.created_at.desc())
        )
        return result.scalars().all()


async def delete_all_ab_groups(session=None) -> int:
    """Удаляет все записи о группах. Возвращает количество удаленных записей"""
    if session is None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(ABGroup))
            groups = result.scalars().all()
            count = len(groups)
            for group in groups:
                await session.delete(group)
            await session.commit()
            return count
    else:
        result = await session.execute(select(ABGroup))
        groups = result.scalars().all()
        count = len(groups)
        for group in groups:
            await session.delete(group)
        await session.commit()
        return count
