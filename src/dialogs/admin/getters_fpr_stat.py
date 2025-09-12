import logging
from datetime import datetime, timedelta

from aiogram_dialog import DialogManager
from sqlalchemy import (
    Integer,  # добавляем Integer в импорты
    func,
    select,
)

from db.db import AsyncSessionLocal
from db.models.old_workflow.yoga_tap import YogaTap, get_all_buttons_statistics
from db.models.order import Order
from db.models.price import BASE_PRICES_RU_SHORT
from db.models.user import User


async def get_user_statistics(dialog_manager: DialogManager, **kwargs):
    start_date, end_date = await get_period_dates(dialog_manager)

    async with AsyncSessionLocal() as session:
        # Статистика за все время
        total_users_all = await session.scalar(select(func.count(User.id)))

        # Статистика за период
        new_users_period = await session.scalar(
            select(func.count(User.id)).where(
                User.created_at.between(start_date, end_date)
            )
        )

        return {
            # Общая статистика
            "total_users_all": total_users_all,
            # Статистика за период
            "new_users_period": new_users_period,
            "period_start": start_date.strftime("%d.%m.%Y"),
            "period_end": end_date.strftime("%d.%m.%Y"),
        }


async def get_sales_statistics(dialog_manager: DialogManager, **kwargs):
    start_date, end_date = await get_period_dates(dialog_manager)

    async with AsyncSessionLocal() as session:
        # Статистика за все время
        total_sales_all = await session.scalar(
            select(func.sum(Order.amount)).where(Order.status == "completed")
        )

        successful_orders_all = await session.scalar(
            select(func.count(Order.id)).where(Order.status == "completed")
        )

        avg_order_all = await session.scalar(
            select(func.avg(Order.amount)).where(Order.status == "completed")
        )

        potential_sales_all = await session.scalar(
            select(func.sum(Order.amount)).where(Order.status != "completed")
        )

        pending_orders_all = await session.scalar(
            select(func.count(Order.id)).where(Order.status != "completed")
        )

        # Добавляем статистику за период
        total_sales_period = await session.scalar(
            select(func.sum(Order.amount)).where(
                Order.status == "completed",
                Order.created_at.between(start_date, end_date),
            )
        )

        successful_orders_period = await session.scalar(
            select(func.count(Order.id)).where(
                Order.status == "completed",
                Order.created_at.between(start_date, end_date),
            )
        )

        avg_order_period = await session.scalar(
            select(func.avg(Order.amount)).where(
                Order.status == "completed",
                Order.created_at.between(start_date, end_date),
            )
        )

        potential_sales_period = await session.scalar(
            select(func.sum(Order.amount)).where(
                Order.status != "completed",
                Order.created_at.between(start_date, end_date),
            )
        )

        pending_orders_period = await session.scalar(
            select(func.count(Order.id)).where(
                Order.status != "completed",
                Order.created_at.between(start_date, end_date),
            )
        )

        # Статистика по продуктам за все время
        products_all = await session.execute(
            select(
                Order.product,
                func.count(Order.id).label("count"),
                func.sum(Order.amount).label("total"),
            )
            .where(Order.status == "completed")
            .group_by(Order.product)
            .order_by(
                func.sum(Order.amount).desc()
            )  # Сортируем по сумме продаж
        )
        products_all = products_all.all()

        # Статистика по продуктам за период
        products_period = await session.execute(
            select(
                Order.product,
                func.count(Order.id).label("count"),
                func.sum(Order.amount).label("total"),
            )
            .where(
                Order.status == "completed",
                Order.created_at.between(start_date, end_date),
            )
            .group_by(Order.product)
            .order_by(func.sum(Order.amount).desc())
        )
        products_period = products_period.all()

        # Форматируем статистику по продуктам
        products_all_text = (
            "\n".join(
                f"<b><i>•</i></b> {BASE_PRICES_RU_SHORT.get(product, product)}: {count} шт. — {round(total, 2)} рублей"
                for product, count, total in products_all
            )
            or "<b><i>•</i></b> Нет данных"
        )

        products_period_text = (
            "\n".join(
                f"<b><i>•</i></b> {BASE_PRICES_RU_SHORT.get(product, product)}: {count} шт. — {round(total, 2)} рублей"
                for product, count, total in products_period
            )
            or "<b><i>•</i></b> Нет данных"
        )

        return {
            # Общая статистика
            "total_sales_all": round(
                total_sales_all if total_sales_all else 0, 2
            ),
            "successful_orders_all": successful_orders_all,
            "avg_order_all": round(avg_order_all if avg_order_all else 0, 2),
            "potential_sales_all": round(
                potential_sales_all if potential_sales_all else 0, 2
            ),
            "pending_orders_all": pending_orders_all,
            # Статистика за период
            "total_sales_period": round(
                total_sales_period if total_sales_period else 0, 2
            ),
            "successful_orders_period": successful_orders_period,
            "avg_order_period": round(
                avg_order_period if avg_order_period else 0, 2
            ),
            "potential_sales_period": round(
                potential_sales_period if potential_sales_period else 0, 2
            ),
            "pending_orders_period": pending_orders_period,
            "products_all_text": products_all_text,
            "products_period_text": products_period_text,
            "period_start": start_date.strftime("%d.%m.%Y"),
            "period_end": end_date.strftime("%d.%m.%Y"),
        }


async def get_period_dates(
    dialog_manager: DialogManager,
) -> tuple[datetime, datetime]:
    """Получение выбранного периода из dialog_data"""
    dialog_data = dialog_manager.dialog_data

    if "START_DATE_KEY" in dialog_data and "END_DATE_KEY" in dialog_data:
        start_date = dialog_data["START_DATE_KEY"]
        end_date = dialog_data["END_DATE_KEY"]
    else:
        # По умолчанию показываем статистику за последний месяц
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

    return (
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time()),
    )


async def get_time_to_purchase_statistics(
    dialog_manager: DialogManager, **kwargs
):
    try:
        async with AsyncSessionLocal() as session:
            # Подзапрос для получения первой успешной покупки каждого пользователя
            first_purchases = (
                select(
                    Order.user_id,
                    func.min(Order.created_at).label("first_purchase_date"),
                )
                .where(Order.status == "completed")
                .group_by(Order.user_id)
                .subquery()
            )

            # Основной запрос, соединяем с таблицей пользователей и считаем разницу в днях
            query = (
                select(
                    func.cast(
                        (
                            func.strftime(
                                "%s", first_purchases.c.first_purchase_date
                            )
                            - func.strftime("%s", User.created_at)
                        )
                        / 86400,
                        Integer,
                    ).label("days_to_purchase"),
                    func.count().label("user_count"),
                )
                .select_from(
                    first_purchases
                )  # Явно указываем левую часть join
                .join(
                    User,
                    User.user_id
                    == first_purchases.c.user_id,  # Явно указываем условие join
                )
                .group_by("days_to_purchase")
                .order_by("days_to_purchase")
            )

            result = await session.execute(query)
            stats = result.all()

            # Форматируем результаты
            stats_text = ""
            total_users = sum(count for _, count in stats)

            if total_users == 0:
                return {
                    "time_to_purchase_stats": "Нет данных о покупках",
                    "total_users": 0,
                }

            for days, count in stats:
                if days is None:
                    continue

                days = int(days)
                percentage = (count / total_users) * 100

                if days == 0:
                    days_text = "в день регистрации"
                else:
                    days_text = f"через {days} {get_days_suffix(days)}"

                stats_text += f"<b><i>•</i></b> {count} пользователей ({percentage:.1f}%) — {days_text}\n"

            return {
                "time_to_purchase_stats": stats_text
                or "<b><i>•</i></b> Нет данных",
                "total_users": total_users or "<b><i>•</i></b> Нет данных",
            }

    except Exception as e:
        logging.error(
            f"Unexpected error in get_time_to_purchase_statistics: {str(e)}"
        )
        return {
            "time_to_purchase_stats": "Произошла ошибка при получении статистики",
            "total_users": 0,
        }


def get_days_suffix(days):
    if days % 10 == 1 and days % 100 != 11:
        return "день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return "дня"
    else:
        return "дней"


async def get_sales_by_weekday_statistics(
    dialog_manager: DialogManager, **kwargs
):
    try:
        async with AsyncSessionLocal() as session:
            # Получаем статистику по дням недели для каждого продукта
            query = (
                select(
                    Order.product,
                    func.strftime("%w", Order.created_at).label(
                        "weekday"
                    ),  # 0 = Sunday, ..., 6 = Saturday
                    func.count().label("count"),
                )
                .where(Order.status == "completed")
                .group_by(Order.product, "weekday")
                .order_by(Order.product, "weekday")
            )

            result = await session.execute(query)
            sales_by_day = result.all()

            # Словарь для преобразования номера дня в название
            weekdays = {
                "0": "воскресенье",
                "1": "понедельник",
                "2": "вторник",
                "3": "среда",
                "4": "четверг",
                "5": "пятница",
                "6": "суббота",
            }

            # Форматируем результаты
            stats_text = ""
            current_product = None

            for product, weekday, count in sales_by_day:
                if count == 0:  # Пропускаем дни с нулевыми продажами
                    continue

                if current_product != product:
                    if current_product is not None:
                        stats_text += "\n"
                    stats_text += (
                        f"\n{BASE_PRICES_RU_SHORT.get(product, product)}:"
                    )
                    current_product = BASE_PRICES_RU_SHORT.get(
                        product, product
                    )

                stats_text += (
                    f"\n<b><i>•</i></b> {count} — {weekdays[weekday]}"
                )

            if not stats_text:
                stats_text = "<b><i>•</i></b> Нет данных"

            return {"sales_by_weekday_stats": stats_text}

    except Exception as e:
        logging.error(
            f"Unexpected error in get_sales_by_weekday_statistics: {str(e)}"
        )
        return {
            "sales_by_weekday_stats": "Произошла ошибка при получении статистики"
        }


async def get_sales_by_monthday_statistics(
    dialog_manager: DialogManager, **kwargs
):
    try:
        async with AsyncSessionLocal() as session:
            # Получаем статистику по числам месяца
            query = (
                select(
                    func.strftime("%d", Order.created_at).label(
                        "day"
                    ),  # День месяца
                    func.count().label("count"),
                    func.sum(Order.amount).label("total_amount"),
                )
                .where(Order.status == "completed")
                .group_by("day")
                .order_by("day")
            )

            result = await session.execute(query)
            sales_by_day = result.all()

            # Форматируем результаты
            # stats_text = "📅 Распределение продаж по числам месяца:\n\n"
            stats_text = ""

            for day, count, total_amount in sales_by_day:
                if count == 0:  # Пропускаем дни с нулевыми продажами
                    continue

                # Добавляем ведущий ноль к однозначным числам
                day = day.zfill(2)
                stats_text += f"<b><i>•</i></b> {day} число: {count} продаж на {round(total_amount, 2)} рублей\n"

            if stats_text == "":
                stats_text = "<b><i>•</i></b> Нет данных"

            return {"sales_by_monthday_stats": stats_text}

    except Exception as e:
        logging.error(
            f"Unexpected error in get_sales_by_monthday_statistics: {str(e)}"
        )
        return {
            "sales_by_monthday_stats": "Произошла ошибка при получении статистики"
        }


async def get_yoga_statistics(dialog_manager: DialogManager, **kwargs):
    start_date, end_date = await get_period_dates(dialog_manager)

    async with AsyncSessionLocal() as session:
        # Статистика за все время
        total_taps_all = await session.scalar(
            select(func.count()).select_from(YogaTap)
        )

        # Среднее количество нажатий в день за все время
        first_tap_date = await session.scalar(
            select(func.min(YogaTap.tap_datetime)).select_from(YogaTap)
        )

        if first_tap_date and total_taps_all:
            days_all = (datetime.utcnow() - first_tap_date).days or 1
            avg_taps_per_day_all = round(total_taps_all / days_all, 1)
        else:
            avg_taps_per_day_all = 0

        # Статистика за период
        total_taps_period = await session.scalar(
            select(func.count())
            .select_from(YogaTap)
            .where(YogaTap.tap_datetime.between(start_date, end_date))
        )

        # Среднее количество нажатий в день за период
        days_period = (end_date - start_date).days or 1
        avg_taps_per_day_period = (
            round(total_taps_period / days_period, 1)
            if total_taps_period
            else 0
        )

        return {
            # Общая статистика
            "total_taps_all": total_taps_all or 0,
            "avg_taps_per_day_all": avg_taps_per_day_all,
            # Статистика за период
            "total_taps_period": total_taps_period or 0,
            "avg_taps_per_day_period": avg_taps_per_day_period,
            # Даты периода
            "period_start": start_date.strftime("%d.%m.%Y"),
            "period_end": end_date.strftime("%d.%m.%Y"),
        }


async def get_buttons_statistics(dialog_manager: DialogManager, **kwargs):
    start_date, end_date = await get_period_dates(dialog_manager)

    async with AsyncSessionLocal() as session:
        stats = await get_all_buttons_statistics(session, start_date, end_date)

        # Формируем текст статистики
        stats_text = "📊 Статистика по кнопкам:\n\n"
        for button_name, button_stats in stats.items():
            stats_text += f"🔘 {button_name}:\n"
            stats_text += f"<b><i>•</i></b> Всего нажатий: {button_stats['total_taps']}\n"
            stats_text += f"<b><i>•</i></b> Среднее в день: {button_stats['avg_taps_per_day']}\n"
            if button_stats["period_taps"] is not None:
                stats_text += f"<b><i>•</i></b> За период: {button_stats['period_taps']}\n"
                stats_text += f"<b><i>•</i></b> Среднее в день за период: {button_stats['avg_taps_per_day_period']}\n"
            stats_text += "\n"

        return {
            "buttons_stats": stats_text,
            "period_start": start_date.strftime("%d.%m.%Y"),
            "period_end": end_date.strftime("%d.%m.%Y"),
        }
