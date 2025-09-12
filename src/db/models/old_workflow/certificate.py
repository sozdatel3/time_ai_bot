import hashlib

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    select,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from config.config import load_config
from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class Certificate(Base, TimestampMixin):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    is_activated = Column(Boolean, default=False)
    is_used = Column(Boolean, default=False)  # Добавляем новое поле
    activated_at = Column(DateTime(timezone=True), nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    url = Column(String, nullable=True)

    sender = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_certificates"
    )

    recipient = relationship(
        "User",
        foreign_keys=[recipient_id],
        back_populates="received_certificates",
    )


async def generate_certificate_url(certificate_id: int, sender_id: int):
    config = load_config()
    bot_username = config.bot.name
    unique_hash = hashlib.sha256(
        f"{certificate_id}{sender_id}".encode()
    ).hexdigest()[:10]
    return f"https://t.me/{bot_username}?start=cert_{certificate_id}_{unique_hash}"


async def create_certificate(
    sender_id: int, amount: float, recipient_id: int = None
) -> Certificate:
    async with AsyncSessionLocal() as session:
        certificate = Certificate(
            sender_id=sender_id, amount=amount, recipient_id=recipient_id
        )
        session.add(certificate)
        await session.commit()
        await session.refresh(certificate)

        # Генерируем URL после создания сертификата, используя sender_id
        certificate.url = await generate_certificate_url(
            certificate.id, sender_id
        )
        await session.commit()

    return certificate


async def activate_certificate(
    certificate_id: int, recipient_id: int
) -> Certificate:
    async with AsyncSessionLocal() as session:
        certificate = await session.get(Certificate, certificate_id)
        if certificate and not certificate.is_activated:
            certificate.is_activated = True
            certificate.recipient_id = recipient_id
            certificate.activated_at = func.now()
            await session.commit()
            await session.refresh(certificate)
        return certificate


async def use_certificate(
    certificate_id: int, user_id: int
) -> tuple[bool, float]:
    async with AsyncSessionLocal() as session:
        certificate = await session.get(Certificate, certificate_id)
        if certificate and not certificate.is_used:
            certificate.is_used = True
            certificate.recipient_id = user_id
            certificate.activated_at = func.now()
            await session.commit()
            return True, certificate.amount
        return False, 0


async def get_user_certificates(user_id: int, as_recipient: bool = True):
    async with AsyncSessionLocal() as session:
        if as_recipient:
            stmt = select(Certificate).where(
                Certificate.recipient_id == user_id
            )
        else:
            stmt = select(Certificate).where(Certificate.sender_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_certificate(certificate_id: int) -> Certificate:
    async with AsyncSessionLocal() as session:
        certificate = await session.get(Certificate, certificate_id)
        return certificate


async def get_certificate_with_sender(
    certificate_id: int, unique_hash: str
) -> Certificate:
    async with AsyncSessionLocal() as session:
        certificate = await session.get(Certificate, certificate_id)
        if certificate:
            expected_hash = hashlib.sha256(
                f"{certificate_id}{certificate.sender_id}".encode()
            ).hexdigest()[:10]
            if expected_hash == unique_hash:
                return certificate
        return None
