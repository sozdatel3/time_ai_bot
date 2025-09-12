from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Select
from aiogram_dialog.widgets.text import Const, Format

from config.config import get_config
from db.models.old_workflow.links import create_bot_link, get_all_links
from dialogs.states import AdminStates


async def get_links_list(**kwargs):
    links = await get_all_links()
    links_text = "\n".join(
        [
            f"<b><i>•</i></b> {link.name}: {link.clicks} переходов"
            for link in links
        ]
    )
    return {
        "links_text": links_text or "<b><i>•</i></b> Нет активных ссылок",
        "links": links,
    }


async def get_link_info(dialog_manager: DialogManager, **kwargs):
    link_id = dialog_manager.dialog_data.get("selected_link_id")
    links = await get_all_links()
    link = next((link for link in links if link.id == link_id), None)

    if not link:
        return {"link_info": "Ссылка не найдена"}

    config = get_config()
    bot_username = config.bot.name

    full_link = f"t.me/{bot_username}?start=link_{link.link_code}"

    info = (
        f"📎 Название: {link.name}\n"
        f"🔗 Код: {link.link_code}\n"
        f"👥 Количество переходов: {link.clicks}\n"
        f"📅 Создана: {link.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"🌐 Полная ссылка:\n<code>{full_link}</code>"
    )

    if link.description:
        info = f"📝 Описание: {link.description}\n" + info

    return {"link_info": info}


# async def process_link_name(
#     message: Message, dialog: Dialog, manager: DialogManager
# ):
#     name = message.text
#     description = None  # Можно добавить отдельное состояние для описания
#     link = await create_bot_link(name=name, description=description)

#     # config = manager.middleware_data.get("config")
#     config = get_config()
#     bot_username = config.bot.name

#     await message.answer(
#         f"Ссылка создана!\n"
#         f"Название: {link.name}\n"
#         f"Код: {link.link_code}\n"
#         f"Полная ссылка: t.me/{bot_username}?start=link_{link.link_code}"
#     )
#     await manager.switch_to(AdminStates.LINKS)


async def process_link_name(
    message: Message, dialog: Dialog, manager: DialogManager
):
    name = message.text
    manager.dialog_data["link_name"] = name
    await message.delete()
    await manager.switch_to(
        AdminStates.ADD_LINK_DESCRIPTION, show_mode=ShowMode.EDIT
    )


async def process_link_description(
    message: Message, dialog: Dialog, manager: DialogManager
):
    try:
        description = message.text
        name = manager.dialog_data.get("link_name")

        link = await create_bot_link(name=name, description=description)

        config = get_config()
        bot_username = config.bot.name

        await message.answer(
            f"✅ Ссылка успешно создана!\n\n"
            f"📎 Название: {link.name}\n"
            f"📝 Описание: {description}\n"
            f"🔗 Код: {link.link_code}\n"
            f"🌐 Полная ссылка:\n<code>t.me/{bot_username}?start=link_{link.link_code}</code>"
        )
        await message.delete()
        await manager.switch_to(
            AdminStates.LINKS, show_mode=ShowMode.DELETE_AND_SEND
        )
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


async def skip_description(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    name = manager.dialog_data.get("link_name")
    link = await create_bot_link(name=name)

    config = get_config()
    bot_username = config.bot.name

    await c.message.answer(
        f"✅ Ссылка успешно создана!\n\n"
        f"📎 Название: {link.name}\n"
        f"🔗 Код: {link.link_code}\n"
        f"🌐 Полная ссылка:\n<code>t.me/{bot_username}?start=link_{link.link_code}</code>"
    )
    await manager.switch_to(
        AdminStates.LINKS, show_mode=ShowMode.DELETE_AND_SEND
    )


async def send_all_links(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    links = await get_all_links()
    config = get_config()
    bot_username = config.bot.name

    links_text = "Список всех реферальных ссылок:\n\n"
    for link in links:
        full_link = f"t.me/{bot_username}?start=link_{link.link_code}"
        links_text += f"<b><i>•</i></b> {link.name}\n{full_link}\n\n"

    await c.message.answer(links_text)
    await manager.switch_to(
        AdminStates.LINKS, show_mode=ShowMode.DELETE_AND_SEND
    )


async def on_link_selected(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    manager.dialog_data["selected_link_id"] = int(item_id)
    await manager.switch_to(
        AdminStates.EDIT_LINK, show_mode=ShowMode.DELETE_AND_SEND
    )


async def switch_to_add_link(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.ADD_LINK, show_mode=ShowMode.EDIT)


async def back_to_links(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.LINKS, show_mode=ShowMode.EDIT)


async def back_to_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        AdminStates.MAIN, show_mode=ShowMode.DELETE_AND_SEND
    )


links_windows = [
    Window(
        Const("Управление реферальными ссылками:\n"),
        Format("{links_text}"),
        Button(
            Const("➕ Добавить ссылку"),
            id="add_link",
            on_click=switch_to_add_link,
        ),
        Button(
            Const("🔗 Отправить все ссылки"),
            id="send_all_links",
            on_click=send_all_links,
        ),
        Group(
            Select(
                Format("{item.name}: {item.clicks} переходов"),
                id="link_select",
                item_id_getter=lambda x: x.id,
                items="links",
                on_click=on_link_selected,
            ),
            width=1,
        ),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_main),
        state=AdminStates.LINKS,
        getter=get_links_list,
    ),
    Window(
        Const("<i>Введите название для новой ссылки:</i>"),
        MessageInput(process_link_name),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_links),
        state=AdminStates.ADD_LINK,
    ),
    Window(
        Const(
            "<i>Введите описание для ссылки (или нажмите «Пропустить»):</i>"
        ),
        MessageInput(process_link_description),
        Button(Const("⏩ Пропустить"), id="skip", on_click=skip_description),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_links),
        state=AdminStates.ADD_LINK_DESCRIPTION,
    ),
    Window(
        Const("Информация о ссылке:\n"),
        Format("{link_info}"),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=back_to_links,
        ),
        state=AdminStates.EDIT_LINK,
        getter=get_link_info,
    ),
]
