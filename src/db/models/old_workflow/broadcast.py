from sqlalchemy import Column, Integer, text

from db.db import AsyncSessionLocal, Base, get_engine
from db.models.base import TimestampMixin


class Broadcast(Base, TimestampMixin):
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)


async def create_broadcast(broadcast_name: str):
    async with get_engine().begin() as conn:
        await conn.execute(
            text(f"ALTER TABLE broadcasts ADD COLUMN {broadcast_name} BOOLEAN")
        )


async def mark_broadcast_delivered(user_id: int, broadcast_name: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                f"""
            INSERT INTO broadcasts (user_id, {broadcast_name}, created_at, updated_at)
            VALUES (:user_id, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET {broadcast_name} = TRUE, updated_at = CURRENT_TIMESTAMP
            """
            ),
            {"user_id": user_id},
        )
        await session.commit()


async def mark_broadcast_failed(user_id: int, broadcast_name: str):
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                f"""
            INSERT INTO broadcasts (user_id, {broadcast_name}, created_at, updated_at)
            VALUES (:user_id, FALSE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET {broadcast_name} = FALSE, updated_at = CURRENT_TIMESTAMP
            """
            ),
            {"user_id": user_id},
        )
        await session.commit()


async def get_broadcast_statistics(
    start_date: str = None, end_date: str = None
):
    async with AsyncSessionLocal() as session:
        columns_query = """
            SELECT name FROM pragma_table_info('broadcasts')
            WHERE name NOT IN ('id', 'user_id', 'created_at', 'updated_at')
        """
        result = await session.execute(text(columns_query))
        broadcast_columns = [row[0] for row in result.fetchall()]

        statistics = []
        for broadcast_name in broadcast_columns:
            try:
                # Извлекаем дату из конца названия бродкаста
                # Ищем последнее вхождение '_' и берем всё после него
                date_str = (
                    broadcast_name.split("_")[-2]
                    + "_"
                    + broadcast_name.split("_")[-1]
                )

                # Фильтруем по датам если они указаны
                if start_date and end_date:
                    if not (start_date <= date_str <= end_date):
                        continue

                stats_query = f"""
                    SELECT 
                        '{broadcast_name}' as broadcast_name,
                        SUM(CASE WHEN {broadcast_name} = TRUE THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN {broadcast_name} = FALSE OR {broadcast_name} IS NULL THEN 1 ELSE 0 END) as failed,
                        COUNT(*) as total
                    FROM broadcasts 
                """
                result = await session.execute(text(stats_query))
                stats = result.fetchone()

                if stats:
                    statistics.append(
                        {
                            "date": date_str,
                            "broadcast_type": "_".join(
                                broadcast_name.split("_")[:-2]
                            ),  # Добавляем тип бродкаста
                            "successful": int(stats.successful or 0),
                            "failed": int(stats.failed or 0),
                            "total": int(stats.total or 0),
                        }
                    )
            except (IndexError, ValueError):
                continue

        return sorted(statistics, key=lambda x: x["date"])
