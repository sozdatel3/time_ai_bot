from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, select
from sqlalchemy.orm import relationship

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class Question(Base, TimestampMixin):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    question = Column(String)
    answer = Column(String, nullable=True)
    # created_at = Column(
    #     DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    # )
    answered_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="questions")


async def create_question(user_id: int, question: str) -> Question:
    async with AsyncSessionLocal() as session:
        new_question = Question(user_id=user_id, question=question)
        session.add(new_question)
        await session.commit()
        await session.refresh(new_question)
    return new_question


async def get_unanswered_questions() -> List[Question]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Question)
            .where(Question.answer is None)
            .order_by(Question.created_at)
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def answer_question(question_id: int, answer: str) -> Question:
    async with AsyncSessionLocal() as session:
        question = await session.get(Question, question_id)
        if question:
            question.answer = answer
            question.answered_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(question)
        return question


async def get_user_questions(user_id: int) -> List[Question]:
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Question)
            .where(Question.user_id == user_id)
            .order_by(Question.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().all()


async def get_question(question_id: int) -> Optional[Question]:
    async with AsyncSessionLocal() as session:
        return await session.get(Question, question_id)
