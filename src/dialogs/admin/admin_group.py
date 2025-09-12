from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

# from aiogram_dialog.widgets.scrolling import ScrollingGroup
from db.models.user import (
    get_all_user_ids,
    get_users_bought,
    get_users_not_bought,
    get_users_not_bought_but,
    get_users_not_entered,
    get_users_not_today,
    get_users_today,
)
from db.special_function.ab_group_manager import (
    get_group_statistics,
    reset_all_groups,
    split_users_into_groups,
)
from dialogs.states import AdminStates


async def get_groups_info(**kwargs):
    try:
        stats = await get_group_statistics()
        groups_text = "\n\n".join(
            f"📊 {name}:\n"
            f"Количество пользователей: {info['count']}\n"
            f"Описание: {info['description'] or 'Нет описания'}"
            for name, info in stats.items()
        )
        return {"groups_info": groups_text or "Нет активных групп"}
    except Exception as e:
        print(e)
        return {"groups_info": "Ошибка при получении статистики групп"}


async def process_split_name(
    message: Message, dialog: Dialog, manager: DialogManager
):
    manager.dialog_data["split_name"] = message.text
    # await message.answer(
    #     "Введите описание разбиения (или отправьте '-' чтобы пропустить):"
    # )
    await manager.switch_to(AdminStates.AB_GROUPS_DESCRIPTION)


async def process_split_description(
    message: Message, dialog: Dialog, manager: DialogManager
):
    description = None if message.text == "-" else message.text
    manager.dialog_data["description"] = description
    # await message.answer("Введите количество групп для разбиения:")
    await manager.switch_to(AdminStates.AB_GROUPS_SPLIT)


async def process_split_number(
    message: Message, dialog: Dialog, manager: DialogManager
):
    try:
        num_groups = int(message.text)
        if num_groups < 2:
            await message.answer("Количество групп должно быть больше 1")
            return

        target_users = manager.dialog_data.get("target_users", [])
        split_name = manager.dialog_data.get("split_name", "Новое разбиение")
        description = manager.dialog_data.get("description")

        result = await split_users_into_groups(
            target_users, num_groups, split_name, description
        )

        response = "Разбиение выполнено:\n" + "\n".join(
            f"Группа {group}: {count} пользователей"
            for group, count in result.items()
        )
        await message.answer(response)

    except ValueError:
        await message.answer("<i>Пожалуйста, введите корректное число</i>")
    except Exception as e:
        print(e)
        await message.answer("Ошибка при разбиении пользователей")

    await manager.switch_to(AdminStates.AB_GROUPS_MAIN)


async def on_split_all_users(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    users = await get_all_user_ids()
    manager.dialog_data["target_users"] = users
    await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def on_split_not_bought(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    users = await get_users_not_bought()
    manager.dialog_data["target_users"] = users
    await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def on_split_bought(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    users = await get_users_bought()
    manager.dialog_data["target_users"] = users
    await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def on_split_not_bought_but(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    users = await get_users_not_bought_but()
    manager.dialog_data["target_users"] = users
    await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def on_split_today(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    users = await get_users_today()
    manager.dialog_data["target_users"] = users
    await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def on_split_not_today(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    users = await get_users_not_today()
    manager.dialog_data["target_users"] = users
    await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def on_split_not_entered(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    users = await get_users_not_entered()
    manager.dialog_data["target_users"] = users
    await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def on_reset_groups(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    try:
        result = await reset_all_groups()
        await c.message.answer(
            f"Сброшены группы у {result['users_reset']} пользователей\n"
            f"Удалено {result['groups_deleted']} записей о группах"
        )
        await manager.switch_to(AdminStates.AB_GROUPS_MAIN)
    except Exception as e:
        print(e)
        await c.message.answer("Ошибка при сбросе групп")


async def on_split_by_buttons(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """
    Обработчик для кнопки 'Разбить по кнопкам'. Переходит в состояние выбора кнопки.
    """
    await manager.switch_to(AdminStates.AB_GROUPS_BUTTONS)


async def yes_more(c: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["and_more"] = True
    await proc_all_about_buttons(c, button, manager, True)
    # await manager.switch_to(AdminStates.AB_GROUPS_NAME)


async def no_more(c: CallbackQuery, button: Button, manager: DialogManager):
    manager.dialog_data["and_more"] = False
    await proc_all_about_buttons(c, button, manager, False)


async def proc_all_about_buttons(
    c: CallbackQuery, button: Button, manager: DialogManager, and_more: bool
):
    try:
        taps = manager.dialog_data.get("taps")
        button_name = manager.dialog_data.get("button_name")
        if not button_name:
            await c.message.answer(
                "Название кнопки не найдено. Попробуйте снова."
            )
            return

        from db.models.old_workflow.person_button import (
            get_users_by_button_taps,
        )

        target_users = await get_users_by_button_taps(
            button_name, taps, and_more
        )

        if not target_users:
            await c.message.answer(
                "Пользователи не найдены по заданным критериям."
            )
        manager.dialog_data["target_users"] = target_users
        await manager.switch_to(AdminStates.AB_GROUPS_NAME)
        # await manager.switch_to(AdminStates.AB_GROUPS_ANDMORE)

    except ValueError:
        await c.message.answer("<i>Пожалуйста, введите корректное число.</i>")
    except Exception as e:
        print(e)
        await c.message.answer("Ошибка при получении пользователей по кнопке.")
        await manager.switch_to(AdminStates.AB_GROUPS_BUTTONS)


ids = {
    "Аркан": "arcan",
    "Йога клуб": "yoga",
    "Лила | Код судьбы онлайн": "lila",
    "Мак карты": "mac",
    "Обучение на проводника Новой Лилы": "train",
    "Подарки": "gift",
    "Полезные материалы": "usefull",
    "Путь к цели": "way",
    "С сопровождением": "with_help",
    "Самостоятельно": "alone",
    "Сертификаты": "cert",
    "Чакроанализ": "chakr",
}

back_ids = {
    "arcan": "Аркан",
    "yoga": "Йога клуб",
    "lila": "Лила | Код судьбы онлайн",
    "mac": "Мак карты",
    "train": "Обучение на проводника Новой Лилы",
    "gift": "Подарки",
    "usefull": "Полезные материалы",
    "way": "Путь к цели",
    "with_help": "С сопровождением",
    "alone": "Самостоятельно",
    "cert": "Сертификаты",
    "chakr": "Чакроанализ",
}


async def get_buttons_info(**kwargs) -> dict:
    """
    Получает информацию о доступных кнопках из PersonButton и возвращает список кнопок.
    """
    # print("get_buttons_info")
    try:
        from sqlalchemy import select

        from db.db import AsyncSessionLocal
        from db.models.old_workflow.person_button import PersonButton

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(PersonButton.button_name).group_by(
                    PersonButton.button_name
                )
            )
            buttons = [row[0] for row in result]

            short_buttons = []
            for button in buttons:
                if len(button) > 10:
                    short_button = {
                        "name": button,
                        "id": ids.get(button) or button,
                        "short_name": button[:15].replace("|", ""),
                    }
                else:
                    short_button = {
                        "name": button,
                        "id": ids.get(button) or button,
                        "short_name": button.replace("|", ""),
                    }
                short_buttons.append(short_button)
        # print("buttons", buttons)
        # print("short_buttons", short_buttons)
        return {"buttons": buttons, "short_buttons": short_buttons}
    except Exception as e:
        print(e)
        return {"buttons": [], "short_buttons": []}


async def process_button_name(
    message: Message, dialog: Dialog, manager: DialogManager
):
    """
    Обрабатывает ввод названия кнопки для разбиения.
    Сохраняет введённое название в dialog_data и переключает состояние на ввод количества нажатий.
    """
    manager.dialog_data["button_name"] = message.text.strip()
    await manager.switch_to(AdminStates.AB_GROUPS_BUTTONS_COUNT)


async def process_button_count(
    message: Message, dialog: Dialog, manager: DialogManager
):
    """
    Обрабатывает ввод количества нажатий для фильтрации пользователей.
    Извлекает из БД список пользователей по заданной кнопке и количеству нажатий, затем сохраняет их
    в dialog_data['target_users'] для дальнейшего разбиения на A/B группы.
    """

    taps = int(message.text)
    manager.dialog_data["taps"] = taps

    await manager.switch_to(AdminStates.AB_GROUPS_ANDMORE)


async def on_select_button(
    c: CallbackQuery, widget: Button, manager: DialogManager, item_data: str
):
    """
    Обработчик нажатия на кнопку с названием для разбиения по кнопкам.
    Сохраняет выбранное название в dialog_data и переводит диалог в состояние ввода количества нажатий.
    """
    manager.dialog_data["button_name"] = back_ids.get(item_data) or item_data
    await manager.switch_to(AdminStates.AB_GROUPS_BUTTONS_COUNT)


ab_groups_windows = [
    Window(
        Const("Управление A/B группами"),
        Format("{groups_info}"),
        Button(
            Const("Разбить всех"),
            id="split_all",
            on_click=on_split_all_users,
        ),
        Button(
            Const("Разбить по кнопкам"),
            id="split_by_buttons",
            on_click=on_split_by_buttons,
        ),
        Button(
            Const("Разбить ничего не купивших"),
            id="split_not_bought",
            on_click=on_split_not_bought,
        ),
        Button(
            Const("Разбить хоть что-то купивших"),
            id="split_bought",
            on_click=on_split_bought,
        ),
        Button(
            Const("Разбить дошел до покупки, но не купил"),
            id="split_not_bought_but",
            on_click=on_split_not_bought_but,
        ),
        Button(
            Const("Разбить добавившихся сегодня"),
            id="split_today",
            on_click=on_split_today,
        ),
        Button(
            Const("Разбить добавившихся не сегодня"),
            id="split_not_today",
            on_click=on_split_not_today,
        ),
        Button(
            Const("Разбить не прошедших вход"),
            id="split_not_entered",
            on_click=on_split_not_entered,
        ),
        Button(
            Const("Сбросить все группы"),
            id="reset_groups",
            on_click=on_reset_groups,
        ),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(AdminStates.MAIN),
        ),
        state=AdminStates.AB_GROUPS_MAIN,
        getter=get_groups_info,
    ),
    Window(
        Const("Выберите кнопку для разбиения:"),
        ScrollingGroup(
            Select(
                Format("{item[short_name]}"),
                # Format("XXXX"),
                item_id_getter=lambda x: x["id"],
                id="select_button_1",
                # items="buttons",
                items="short_buttons",
                on_click=on_select_button,
                # width=2,  # Можно настроить количество кнопок в ряду
            ),
            width=1,
            height=5,
            id="select_scroll_group_id",
        ),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(AdminStates.AB_GROUPS_MAIN),
        ),
        state=AdminStates.AB_GROUPS_BUTTONS,
        getter=get_buttons_info,
    ),
    Window(
        Const("<i>Введите количество нажатий для фильтрации:</i>"),
        MessageInput(process_button_count),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(
                AdminStates.AB_GROUPS_BUTTONS
            ),
        ),
        state=AdminStates.AB_GROUPS_BUTTONS_COUNT,
    ),
    Window(
        Const("И больше?"),
        # MessageInput(process_button_count),
        Button(
            Const("Да"),
            id="yes_more",
            on_click=yes_more,
        ),
        Button(
            Const("Нет"),
            id="no_more",
            on_click=no_more,
        ),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(
                AdminStates.AB_GROUPS_BUTTONS_COUNT
            ),
        ),
        state=AdminStates.AB_GROUPS_ANDMORE,
    ),
    Window(
        Const("<i>Введите название для разбиения:</i>"),
        MessageInput(process_split_name),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(AdminStates.AB_GROUPS_MAIN),
        ),
        state=AdminStates.AB_GROUPS_NAME,
    ),
    Window(
        Const(
            "<i>Введите описание разбиения (или отправьте '-' чтобы пропустить):</i>"
        ),
        MessageInput(process_split_description),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(AdminStates.AB_GROUPS_NAME),
        ),
        state=AdminStates.AB_GROUPS_DESCRIPTION,
    ),
    Window(
        Const("<i>Введите количество групп для разбиения:</i>"),
        MessageInput(process_split_number),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(
                AdminStates.AB_GROUPS_DESCRIPTION
            ),
        ),
        state=AdminStates.AB_GROUPS_SPLIT,
    ),
]
