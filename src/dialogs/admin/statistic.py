import asyncio
import os
from datetime import date, datetime

import pandas as pd
from aiogram.types import CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Calendar, Row
from aiogram_dialog.widgets.text import Const, Format
from matplotlib import pyplot as plt
from sqlalchemy import select

from db.db import AsyncSessionLocal
from db.models.old_workflow.broadcast import get_broadcast_statistics
from db.models.order import Order
from db.models.user import User
from dialogs.admin.admin_dialog import admin_handler
from dialogs.admin.getters_fpr_stat import (
    get_buttons_statistics,
    get_sales_by_monthday_statistics,
    get_sales_by_weekday_statistics,
    get_sales_statistics,
    get_user_statistics,
)
from dialogs.states import StatisticStates


async def switch_to_users(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.users)


async def switch_to_games(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.games)


async def switch_to_sales(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.sales)


async def switch_to_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.main)
    # await manager.back()


async def switch_to_main_from_select_period(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    if "prev_state" in manager.dialog_data:
        await manager.switch_to(manager.dialog_data["prev_state"])
    else:
        await manager.switch_to(StatisticStates.main)


async def on_date_selected(
    c: CallbackQuery,
    widget: Calendar,
    manager: DialogManager,
    selected_date: date,
):
    """Обработчик выбора даты в календаре"""
    dialog_data = manager.dialog_data

    if "START_DATE_KEY" not in dialog_data:
        # Если начальная дата еще не выбрана
        dialog_data["START_DATE_KEY"] = selected_date
        # await c.answer("Пожалуйста, выберите конечную дату")
    else:
        # Если начальная дата уже выбрана
        start_date = dialog_data["START_DATE_KEY"]
        if selected_date < start_date:
            # Меняем даты местами если конечная дата раньше ачальной
            dialog_data["END_DATE_KEY"] = start_date
            dialog_data["START_DATE_KEY"] = selected_date
        else:
            dialog_data["END_DATE_KEY"] = selected_date

        # Возвращаемся к предыдущему состоянию
        previous_state = dialog_data.get(
            "previous_state", StatisticStates.main
        )
        await manager.switch_to(previous_state)


async def select_period(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """Обработчик нажатия кнопки выбора периода"""
    # Очищаем предыдущий выбранный период
    id = button.widget_id
    if id == "select_period_subscriptions":
        manager.dialog_data["prev_state"] = StatisticStates.subscriptions
    elif id == "select_period_sales":
        manager.dialog_data["prev_state"] = StatisticStates.sales
    elif id == "select_period_users":
        manager.dialog_data["prev_state"] = StatisticStates.users
    else:
        manager.dialog_data["prev_state"] = StatisticStates.main

    manager.dialog_data.pop("START_DATE_KEY", None)
    manager.dialog_data.pop("END_DATE_KEY", None)

    # Сохраняем текущее состояние
    manager.dialog_data["previous_state"] = manager.current_context().state
    await manager.switch_to(StatisticStates.select_period)


async def generate_excel_report_orders_task(
    c: CallbackQuery, completed_only: bool = False
):
    async with AsyncSessionLocal() as session:
        CHUNK_SIZE = 500
        offset = 0

        report_type = "completed_orders" if completed_only else "all_orders"
        filename = (
            f"{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        writer = pd.ExcelWriter(filename, engine="xlsxwriter")

        first_chunk = True
        usernames_with_links = []
        total_rows = 0

        while True:
            query = select(Order, User.username).join(
                User, Order.user_id == User.user_id
            )

            if completed_only:
                query = query.where(Order.status == "completed")

            query = (
                query.order_by(Order.created_at.desc())
                .offset(offset)
                .limit(CHUNK_SIZE)
            )

            orders = await session.execute(query)
            chunk_data = orders.all()

            if not chunk_data:
                break

            data = []
            for order, username in chunk_data:
                if username:
                    usernames_with_links.append(
                        (total_rows + len(data), username)
                    )

                data.append(
                    {
                        "Пользователь": username or str(order.user_id),
                        "Сумма": order.amount,
                        "Статус": order.status,
                        "Продукт": order.product,
                        "ID игры": order.game_id,
                        "Использовано баланса": order.balance_to_use,
                        "Дата создания": (
                            order.created_at.strftime("%d.%m.%Y %H:%M:%S")
                            if order.created_at
                            else ""
                        ),
                        "Дата обновления": (
                            order.updated_at.strftime("%d.%m.%Y %H:%M:%S")
                            if order.updated_at
                            else ""
                        ),
                    }
                )

            df_chunk = pd.DataFrame(data)

            if first_chunk:
                df_chunk.to_excel(writer, sheet_name="Заказы", index=False)
                first_chunk = False
            else:
                df_chunk.to_excel(
                    writer,
                    sheet_name="Заказы",
                    startrow=total_rows + 1,
                    header=False,
                    index=False,
                )

            total_rows += len(data)
            offset += CHUNK_SIZE

        worksheet = writer.sheets["Заказы"]
        link_format = writer.book.add_format(
            {"font_color": "blue", "underline": True}
        )

        column_formats = {
            "A": 15,  # Пользователь
            "B": 10,  # Сумма
            "C": 15,  # Статус
            "D": 30,  # Продукт
            "E": 10,  # ID игры
            "F": 15,  # Использовано баланса
            "G": 20,  # Дата создания
            "H": 20,  # Дата обновления
        }

        for col, width in column_formats.items():
            worksheet.set_column(f"{col}:{col}", width)

        for row_idx, username in usernames_with_links:
            cell = f"A{row_idx + 2}"
            url = f"https://t.me/{username}"
            worksheet.write_url(cell, url, link_format, username)

        writer.close()

        await c.message.answer_document(
            FSInputFile(filename),
            caption=f"<i>Отчет по {'выполненным ' if completed_only else ''}заказам ✉️</i>",
        )


async def start_excel_report_orders_generation(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    completed_only = button.widget_id == "download_excel_completed_orders"
    await c.message.answer(
        f"""<i>Я начинаю формировать отчёт по {'выполненным ' if completed_only else ''}заказам в фоновом режиме. Вы получите уведомление, когда он будет готов.</i>
        """
    )
    asyncio.create_task(generate_excel_report_orders_task(c, completed_only))


async def switch_to_time_to_purchase(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.time_to_purchase)


async def switch_to_sales_by_weekday(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.sales_by_weekday)


async def switch_to_sales_by_monthday(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.sales_by_monthday)


async def switch_to_meta_cards(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.meta_cards)


# async def switch_to_meta_cards_analytics(
#     c: CallbackQuery, button: Button, manager: DialogManager
# ):
#     await manager.switch_to(StatisticStates.meta_cards_analytics)


async def switch_to_subscriptions(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.subscriptions)


async def switch_to_yoga(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.yoga)


async def switch_to_buttons(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(StatisticStates.buttons)


async def plot_broadcast_statistics(manager: DialogManager):
    dialog_data = manager.dialog_data
    start_date = dialog_data.get("START_DATE_KEY")
    end_date = dialog_data.get("END_DATE_KEY")

    start_date_str = start_date.strftime("%Y%m%d") if start_date else None
    end_date_str = end_date.strftime("%Y%m%d") if end_date else None

    stats = await get_broadcast_statistics(start_date_str, end_date_str)

    if not stats:
        return None

    # Группируем статистику по типам рассылок
    broadcast_groups = {}
    for stat in stats:
        broadcast_type = stat["broadcast_type"]
        if broadcast_type not in broadcast_groups:
            broadcast_groups[broadcast_type] = []
        broadcast_groups[broadcast_type].append(stat)

    # Создаем график для каждой группы
    file_paths = []
    os.makedirs("temp", exist_ok=True)

    for broadcast_type, group_stats in broadcast_groups.items():
        plt.figure(figsize=(12, 6))

        dates = [stat["date"] for stat in group_stats]
        successful = [stat["successful"] for stat in group_stats]
        failed = [stat["failed"] for stat in group_stats]

        plt.bar(dates, successful, label="Успешно", color="green")
        plt.bar(
            dates, failed, bottom=successful, label="Неуспешно", color="red"
        )

        if start_date and end_date:
            title = f"Статистика рассылок '{broadcast_type}'\nза период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        else:
            title = f"Общая статистика рассылок '{broadcast_type}'"

        plt.title(title)
        plt.xlabel("Дата")
        plt.ylabel("Количество пользователей")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        file_path = f"temp/broadcast_statistics_{broadcast_type}.png"
        plt.savefig(file_path, format="png")
        plt.close()

        file_paths.append(file_path)

    return file_paths


async def delete_file_background(file_path: str, delay: int = 1):
    """Асинхронное удаление файла с задержкой"""
    await asyncio.sleep(delay)
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Ошибка при удалении файла {file_path}: {e}")


async def show_broadcast_statistics(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await c.answer("Генерирую статистику...")

    try:
        file_paths = await plot_broadcast_statistics(manager)
        if not file_paths:
            await c.message.answer("Нет данных для построения графиков.")
            return

        # Формируем подпись в зависимости от наличия дат
        start_date = manager.dialog_data.get("START_DATE_KEY")
        end_date = manager.dialog_data.get("END_DATE_KEY")

        if start_date and end_date:
            period_text = f"за период {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        else:
            period_text = "(общая статистика)"

        # Создаем MediaGroup из графиков
        media_group = []
        for i, file_path in enumerate(file_paths):
            caption = f"Статистика рассылок {period_text}" if i == 0 else None
            media_group.append(
                InputMediaPhoto(media=FSInputFile(file_path), caption=caption)
            )

        # Отправляем группу изображений
        await c.message.answer_media_group(media=media_group)

        # Удаляем временные файлы
        for file_path in file_paths:
            asyncio.create_task(delete_file_background(file_path))

    except Exception as e:
        print(f"Ошибка при генерации/отправке статистики: {e}")
        await c.message.answer("Ошибка при создании или отправке графиков.")
        return

    await manager.switch_to(StatisticStates.main)


statistic_dialog = Dialog(
    Window(
        Const("📊 Статистика рассылок\n"),
        # Format("📅 Период: {period_start} - {period_end}"),
        Row(
            Button(
                Const("📅 Выбрать период"),
                id="select_period",
                on_click=select_period,
            ),
            Button(
                Const("◀️ Вернуться назад"), id="back", on_click=switch_to_main
            ),
        ),
        Button(
            Const("📊 Показать график"),
            id="show_broadcast_stats",
            on_click=show_broadcast_statistics,
        ),
        state=StatisticStates.broadcast,
        # getter=get_broadcast_statistics,
    ),
    Window(
        Const("📊 Статистика:"),
        Button(
            Const("👥 Пользователи"),
            id="users_stat",
            on_click=switch_to_users,
        ),
        # Button(
        #     Const("💰 Продажи"),
        #     id="sales_stat",
        #     on_click=switch_to_sales,
        # ),
        # Button(
        #     Const("📊 Рассылки"),
        #     id="broadcast_statistics",
        #     on_click=lambda c, b, m: m.switch_to(StatisticStates.broadcast),
        # ),
        # Button(
        #     Const("🧘🏻 Подписки"),
        #     id="subscriptions_stat",
        #     on_click=switch_to_subscriptions,
        # ),
        # Button(
        #     Const("🔘 Статистика кнопок"),
        #     id="buttons_stat",
        #     on_click=switch_to_buttons,
        # ),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=admin_handler),
        state=StatisticStates.main,
    ),
    Window(
        Const(
            "📅 Выберите период: сначала укажите начальную дату — затем конечную."
        ),
        Calendar(id="calendar", on_click=on_date_selected),
        Button(
            Const("◀️ Вернуться назад"),
            id="back_from_select_period",
            on_click=switch_to_main_from_select_period,
        ),
        state=StatisticStates.select_period,
    ),
    Window(
        Const("Статистика по пользователям:\n"),
        Format(
            "📊 Общая статистика:\n"
            "<b><i>•</i></b> Всего пользователей: {total_users_all}\n\n"
            # "<b><i>•</i></b> Всего пользователей: 103 573\n"
            # "<b><i>•</i></b> Пользователей с рефералами: {users_with_referrals_all}\n"
            # "<b><i>•</i></b> Пользователей с рефералами: 42 324\n"
            # "<b><i>•</i></b> Активных пользователей: {active_users_all}\n\n"
            "📅 Статистика за период {period_start} — {period_end}:\n"
            "<b><i>•</i></b> Новых пользователей: {new_users_period}\n"
            # "<b><i>•</i></b> Новых пользователей: 3670\n"
            # "<b><i>•</i></b> Пользователей с рефералами: {users_with_referrals_period}\n"
            # "<b><i>•</i></b> Пользователей с рефералами: 1465\n"
            # "<b><i>•</i></b> Активных пользователей: {active_users_period}"
        ),
        Row(
            Button(
                Const("📅 Выбрать период"),
                id="select_period_users",
                on_click=select_period,
            ),
            Button(
                Const("◀️ Вернуться назад"), id="back", on_click=switch_to_main
            ),
        ),
        state=StatisticStates.users,
        getter=get_user_statistics,
    ),
    Window(
        Const("Статистика по продажам:\n"),
        Format(
            "📊 Общая статистика:\n"
            "<b><i>•</i></b> Общая сумма продаж: {total_sales_all} рублей\n"
            "<b><i>•</i></b> Успешных заказов: {successful_orders_all}\n"
            "<b><i>•</i></b> Средний чек: {avg_order_all} рублей\n"
            "<b><i>•</i></b> Потенциальные продажи: {potential_sales_all} рублей\n"
            "<b><i>•</i></b> Незавершенных заказов: {pending_orders_all}\n\n"
            "📦 Продажи по продуктам:\n"
            "{products_all_text}\n\n"
            "📅 Статистика за период {period_start} — {period_end}:\n"
            "<b><i>•</i></b> Сумма продаж: {total_sales_period} рублей\n"
            "<b><i>•</i></b> Успешных заказов: {successful_orders_period}\n"
            "<b><i>•</i></b> Средний чек: {avg_order_period} рублей\n"
            "<b><i>•</i></b> Потенциальные продажи: {potential_sales_period} рублей\n"
            "<b><i>•</i></b> Незавершенных заказов: {pending_orders_period}\n\n"
            "📦 Продажи по продуктам за период:\n"
            "{products_period_text}"
        ),
        Row(
            Button(
                Const("📅 Выбрать период"),
                id="select_period_sales",
                on_click=select_period,
            ),
            Button(
                Const("◀️ Вернуться назад"), id="back", on_click=switch_to_main
            ),
        ),
        # Button(
        #     Const("⏱ Статистика времени до первой покупки\n"),
        #     id="time_to_purchase_stat",
        #     on_click=switch_to_time_to_purchase,
        # ),
        Button(
            Const("📊 Статистика продаж по дням недели"),
            id="sales_by_weekday_stat",
            on_click=switch_to_sales_by_weekday,
        ),
        Button(
            Const("📅 Статистика продаж по числам месяца"),
            id="sales_by_monthday_stat",
            on_click=switch_to_sales_by_monthday,
        ),
        Button(
            Const("📥 Выгрузить все заказы"),
            id="download_excel_orders",
            on_click=start_excel_report_orders_generation,
        ),
        Button(
            Const("📥 Выгрузить выполненные заказы"),
            id="download_excel_completed_orders",
            on_click=start_excel_report_orders_generation,
        ),
        state=StatisticStates.sales,
        getter=get_sales_statistics,
    ),
    # Window(
    #     Const("Статистика времени до первой покупки:\n"),
    #     Format(
    #         "📊 Всего пользователей с покупками: {total_users}\n"
    #         "Распределение по времени:\n"
    #         "{time_to_purchase_stats}"
    #     ),
    #     Button(
    #         Const("◀️ Вернуться назад"), id="back", on_click=switch_to_sales
    #     ),
    #     state=StatisticStates.time_to_purchase,
    #     getter=get_time_to_purchase_statistics,
    # ),
    Window(
        Const("Статистика продаж по дням недели:"),
        Format("{sales_by_weekday_stats}"),
        Button(
            Const("◀️ Вернуться назад"), id="back", on_click=switch_to_sales
        ),
        state=StatisticStates.sales_by_weekday,
        getter=get_sales_by_weekday_statistics,
    ),
    Window(
        Const("Статистика продаж по числам месяца:\n"),
        Format("{sales_by_monthday_stats}"),
        Button(
            Const("◀️ Вернуться назад"), id="back", on_click=switch_to_sales
        ),
        state=StatisticStates.sales_by_monthday,
        getter=get_sales_by_monthday_statistics,
    ),
    Window(
        Const("🔘 Статистика нажатий кнопок\n"),
        Format("{buttons_stats}\n" "📅 Период: {period_start} — {period_end}"),
        Row(
            Button(
                Const("📅 Выбрать период"),
                id="select_period",
                on_click=select_period,
            ),
            Button(
                Const("◀️ Вернуться назад"), id="back", on_click=switch_to_main
            ),
        ),
        state=StatisticStates.buttons,
        getter=get_buttons_statistics,
    ),
)
