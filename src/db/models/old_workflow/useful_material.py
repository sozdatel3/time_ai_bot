from typing import List, Optional

from sqlalchemy import Boolean, Column, Integer, String, select

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class UsefulMaterial(Base, TimestampMixin):
    __tablename__ = "useful_materials"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    message_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False)
    # created_at = Column(
    #     DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    # )
    created_by = Column(Integer)
    is_free = Column(Boolean, default=False)
    # creator = relationship("User", back_populates="created_materials")


async def add_useful_material(
    name: str,
    message_id: int,
    chat_id: int,
    created_by: int,
    is_free: bool = False,
) -> UsefulMaterial:
    async with AsyncSessionLocal() as session:
        material = UsefulMaterial(
            name=name,
            message_id=message_id,
            chat_id=chat_id,
            created_by=created_by,
            is_free=is_free,
        )
        session.add(material)
        await session.commit()
        await session.refresh(material)
    return material


async def get_useful_materials(
    offset: int = 0, limit: int = 16
) -> List[UsefulMaterial]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(UsefulMaterial)
            .order_by(UsefulMaterial.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_useful_material(material_id: int) -> Optional[UsefulMaterial]:
    async with AsyncSessionLocal() as session:
        return await session.get(UsefulMaterial, material_id)


async def delete_useful_material(material_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        material = await session.get(UsefulMaterial, material_id)
        if material:
            await session.delete(material)
            await session.commit()
            return True
        return False
