# import random
# from typing import List, Set

# from sqlalchemy import func, select, update

# from db.db import AsyncSessionLocal
# from db.models.user import User


# async def get_existing_groups() -> Set[int]:
#     """Получает список существующих групп"""
#     async with AsyncSessionLocal() as session:
#         result = await session.execute(select(User.ab_test_group).distinct())
#         return {group for (group,) in result.all() if group != 0}


# async def reset_all_groups() -> int:
#     """Сбрасывает все группы на 0. Возвращает количество обновленных пользователей"""
#     async with AsyncSessionLocal() as session:
#         result = await session.execute(
#             update(User).where(User.ab_test_group != 0).values(ab_test_group=0)
#         )
#         await session.commit()
#         return result.rowcount


# async def split_users_into_groups(
#     user_ids: List[int], num_groups: int, existing_groups: Set[int] = None
# ) -> dict:
#     """
#     Разбивает список пользователей на указанное количество групп

#     Args:
#         user_ids: Список ID пользователей для разбиения
#         num_groups: Количество групп
#         existing_groups: Существующие номера групп (если None, будут получены из БД)

#     Returns:
#         dict: {group_number: count_of_users}
#     """
#     if not user_ids:
#         return {}

#     if existing_groups is None:
#         existing_groups = await get_existing_groups()

#     # Находим доступные номера групп
#     available_groups = set(
#         range(1, max(existing_groups, default=0) + num_groups + 1)
#     )
#     available_groups -= existing_groups
#     new_groups = sorted(list(available_groups))[:num_groups]

#     # Перемешиваем пользователей
#     shuffled_users = user_ids.copy()
#     random.shuffle(shuffled_users)

#     # Распределяем по группам
#     users_per_group = len(shuffled_users) // num_groups
#     remainder = len(shuffled_users) % num_groups

#     group_distribution = {}
#     start_idx = 0

#     async with AsyncSessionLocal() as session:
#         for i, group_number in enumerate(new_groups):
#             # Определяем количество пользователей для текущей группы
#             group_size = users_per_group + (1 if i < remainder else 0)
#             group_users = shuffled_users[start_idx : start_idx + group_size]

#             if group_users:
#                 await session.execute(
#                     update(User)
#                     .where(User.user_id.in_(group_users))
#                     .values(ab_test_group=group_number)
#                 )
#                 group_distribution[group_number] = len(group_users)

#             start_idx += group_size

#         await session.commit()

#     return group_distribution


# async def get_group_statistics() -> dict:
#     """Получает статистику по количеству пользователей в каждой группе"""
#     async with AsyncSessionLocal() as session:
#         result = await session.execute(
#             select(User.ab_test_group, func.count(User.id)).group_by(
#                 User.ab_test_group
#             )
#         )
#         return {group: count for group, count in result.all()}

import random
from typing import Dict, List

from sqlalchemy import func, select, update

from db.db import AsyncSessionLocal
from db.models.old_workflow.ab_group import (
    ABGroup,
    create_ab_group,
    delete_all_ab_groups,
)
from db.models.old_workflow.price_for_group import (
    delete_all_group_prices,
    init_group_prices,
)
from db.models.user import User


async def reset_all_groups() -> Dict[str, int]:
    """Сбрасывает все группы и удаляет записи о них"""
    async with AsyncSessionLocal() as session:
        # Сбрасываем группы пользователей
        result = await session.execute(
            update(User).where(User.ab_test_group != 0).values(ab_test_group=0)
        )
        users_reset = result.rowcount

        # Удаляем записи о группах
        groups_deleted = await delete_all_ab_groups(session)
        await delete_all_group_prices(session)
        await session.commit()

        return {"users_reset": users_reset, "groups_deleted": groups_deleted}


async def split_users_into_groups(
    user_ids: List[int],
    num_groups: int,
    split_name: str,
    description: str = None,
) -> Dict[int, int]:
    """
    Разбивает пользователей на группы

    Args:
        user_ids: Список ID пользователей
        num_groups: Количество групп
        split_name: Название разбиения
        description: Описание разбиения

    Returns:
        dict: {group_number: count_of_users}
    """
    if not user_ids:
        return {}

    # Получаем максимальный номер существующей группы
    async with AsyncSessionLocal() as session:
        max_group_result = await session.execute(
            select(func.max(ABGroup.group_number))
        )
        max_group = max_group_result.scalar() or 0

    # Генерируем новые номера групп
    new_group_numbers = range(max_group + 1, max_group + num_groups + 1)

    # Перемешиваем пользователей
    shuffled_users = user_ids.copy()
    random.shuffle(shuffled_users)

    # Распределяем по группам
    users_per_group = len(shuffled_users) // num_groups
    remainder = len(shuffled_users) % num_groups

    group_distribution = {}
    start_idx = 0

    async with AsyncSessionLocal() as session:
        for i, group_number in enumerate(new_group_numbers):
            # Определяем количество пользователей для текущей группы
            group_size = users_per_group + (1 if i < remainder else 0)
            group_users = shuffled_users[start_idx : start_idx + group_size]

            if group_users:
                # Создаем запись о группе
                await create_ab_group(
                    session=session,
                    name=f"{split_name} (группа {group_number})",
                    group_number=group_number,
                    description=description,
                )

                # Обновляем пользователей
                await session.execute(
                    update(User)
                    .where(User.user_id.in_(group_users))
                    .values(ab_test_group=group_number)
                )
                # После создания группы инициализируем цены
                await init_group_prices(group_number, session)
                group_distribution[group_number] = len(group_users)

            start_idx += group_size

        await session.commit()

    return group_distribution


async def get_group_statistics() -> Dict[str, Dict]:
    """Получает статистику по группам с их названиями"""
    async with AsyncSessionLocal() as session:
        # Получаем информацию о группах
        groups = await session.execute(
            select(ABGroup.group_number, ABGroup.name, ABGroup.description)
        )
        groups_info = {
            group_number: {"name": name, "description": desc}
            for group_number, name, desc in groups
        }

        # Получаем количество пользователей в группах
        users_count = await session.execute(
            select(User.ab_test_group, func.count(User.id)).group_by(
                User.ab_test_group
            )
        )

        stats = {}
        for group_number, count in users_count:
            if group_number == 0:
                stats["Базовая группа"] = {
                    "count": count,
                    "description": "Пользователи без группы",
                }
            elif group_number in groups_info:
                stats[groups_info[group_number]["name"]] = {
                    "count": count,
                    "description": groups_info[group_number]["description"],
                }

        return stats
