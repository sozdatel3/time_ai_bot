from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Select
from aiogram_dialog.widgets.text import Const, Format

from db.models.old_workflow.ab_group import get_ab_groups
from db.models.old_workflow.price_for_group import (
    get_price_for_group,
    set_group_price,
)
from db.models.price import BASE_PRICES, BASE_PRICES_RU, get_price, set_price
from dialogs.states import AdminStates


async def get_prices_list(dialog_manager: DialogManager, **_):
    prices = {}
    for service_name in BASE_PRICES.keys():
        price = await get_price(service_name)
        prices[service_name] = price
    # print("PRICES")
    # print(prices)
    # — Подписка вход: 2 590₽
    # — Подписка продление: 2 000₽

    # Кнопки:

    # Подписка вход: 2 590₽
    # Подписка продление: 2 000₽
    prices_text = "\n".join(
        [
            f"<b><i>•</i></b> {BASE_PRICES_RU[name]}: {price} рублей"
            for name, price in prices.items()
        ]
    )
    prices_list = [
        {"id": k, "name": BASE_PRICES_RU[k], "price": v}
        for k, v in prices.items()
    ]
    # print("PRICES LIST")
    # print(prices_list)
    # rich = await get_pay_photo_attachment(
    #     dialog_manager.event.bot, "misk/navigation/rich1.png"
    # )
    return {
        "prices_text": prices_text,
        "prices": prices_list,
        # "rich": rich,
        # "prices": BASE_PRICES.keys(),
    }


async def get_price_types(**kwargs):
    return {
        "price_types": [
            {"id": "base", "name": "Базовые цены"},
            # {"id": "group", "name": "Цены для AB-групп"},
        ]
    }


async def get_ab_groups_list(**kwargs):
    groups = await get_ab_groups()
    return {
        "groups": [
            {"id": group.group_number, "name": group.name} for group in groups
        ]
    }


async def get_group_prices_list(dialog_manager: DialogManager, **kwargs):
    group_number = dialog_manager.dialog_data.get("selected_group")
    prices = {}
    for service_name in BASE_PRICES.keys():
        price = await get_price_for_group(group_number, service_name)
        prices[service_name] = price

    prices_text = "\n".join(
        [
            f"- {BASE_PRICES_RU[name]}: {price} рублей"
            for name, price in prices.items()
        ]
    )
    prices_list = [
        {"id": k, "name": BASE_PRICES_RU[k], "price": v}
        for k, v in prices.items()
    ]
    return {
        "prices_text": prices_text,
        "prices": prices_list,
    }


async def on_price_selected(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    manager.dialog_data["selected_service"] = item_id
    await manager.switch_to(
        AdminStates.EDIT_PRICE, show_mode=ShowMode.DELETE_AND_SEND
    )


async def on_group_price_selected(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    manager.dialog_data["selected_service"] = item_id
    await manager.switch_to(
        AdminStates.EDIT_GROUP_PRICE, show_mode=ShowMode.DELETE_AND_SEND
    )


async def on_price_type_selected(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    if item_id == "base":
        await manager.switch_to(
            AdminStates.PRICES, show_mode=ShowMode.DELETE_AND_SEND
        )
    else:
        await manager.switch_to(
            AdminStates.GROUP_SELECT, show_mode=ShowMode.DELETE_AND_SEND
        )


async def on_group_selected(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    manager.dialog_data["selected_group"] = int(item_id)
    await manager.switch_to(
        AdminStates.GROUP_PRICES, show_mode=ShowMode.DELETE_AND_SEND
    )


async def process_new_price(
    message: Message, dialog: Dialog, manager: DialogManager
):
    try:
        new_price = int(message.text)
        if new_price <= 0:
            await message.answer(
                "<i>Цена должна быть положительным числом!</i>"
            )
            return

        service_name = manager.dialog_data["selected_service"]
        rus_service_name = BASE_PRICES_RU[service_name]
        await set_price(service_name, new_price)
        if rus_service_name:
            service_name = rus_service_name
        await message.answer(
            f"<i>Стоимость для {service_name} обновлена до {new_price} рублей.</i>"
        )

        # <i>Стоимость для «Продление подписки» обновлена до 10 рублей.</i>
        await message.delete()
        await manager.switch_to(
            AdminStates.PRICES, show_mode=ShowMode.DELETE_AND_SEND
        )
    except ValueError:
        await message.answer("<i>Пожалуйста, введите корректное число!</i>")


async def process_new_group_price(
    message: Message, dialog: Dialog, manager: DialogManager
):
    try:
        new_price = int(message.text)
        if new_price <= 0:
            await message.answer(
                "<i>Цена должна быть положительным числом!</i>"
            )
            return

        service_name = manager.dialog_data["selected_service"]
        group_number = manager.dialog_data["selected_group"]
        await set_group_price(group_number, service_name, new_price)
        await message.answer(
            f"Цена для {BASE_PRICES_RU[service_name]} обновлена до {new_price} рублей"
        )
        await message.delete()
        await manager.switch_to(
            AdminStates.GROUP_PRICES, show_mode=ShowMode.DELETE_AND_SEND
        )
    except ValueError:
        await message.answer("<i>Пожалуйста, введите корректное число!</i>")


async def back_to_prices(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        AdminStates.PRICES, show_mode=ShowMode.DELETE_AND_SEND
    )


async def back_to_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.MAIN)


async def back_to_price_types(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.PRICE_TYPE_SELECT)


async def back_to_groups(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.GROUP_SELECT)


prices_windows = [
    Window(
        Const("Выберите тип цен для управления:"),
        Group(
            Select(
                Format("{item[name]}"),
                id="price_type_select",
                item_id_getter=lambda x: x["id"],
                items="price_types",
                on_click=on_price_type_selected,
            ),
            width=1,
        ),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_main),
        state=AdminStates.PRICE_TYPE_SELECT,
        getter=get_price_types,
    ),
    Window(
        # DynamicMedia("rich", when="rich"),
        Const("Управление ценами:\n"),
        Format("{prices_text}"),
        Group(
            Select(
                Format("{item[name]}"),
                # Format("X рублей"),
                id="price_select",
                item_id_getter=lambda x: x["id"],
                items="prices",
                on_click=on_price_selected,
            ),
            width=1,
        ),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_main),
        # Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_price_types),
        state=AdminStates.PRICES,
        getter=get_prices_list,
    ),
    Window(
        Const("Выберите группу для управления ценами:"),
        Group(
            Select(
                Format("{item[name]}"),
                id="group_select",
                item_id_getter=lambda x: x["id"],
                items="groups",
                on_click=on_group_selected,
            ),
            width=1,
        ),
        Button(
            Const("◀️ Вернуться назад"), id="back", on_click=back_to_price_types
        ),
        state=AdminStates.GROUP_SELECT,
        getter=get_ab_groups_list,
    ),
    Window(
        Const("Управление ценами для группы"),
        Format("{prices_text}"),
        Group(
            Select(
                Format("{item[name]}"),
                id="group_price_select",
                item_id_getter=lambda x: x["id"],
                items="prices",
                on_click=on_group_price_selected,
            ),
            width=1,
        ),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_groups),
        state=AdminStates.GROUP_PRICES,
        getter=get_group_prices_list,
    ),
    Window(
        Format("<i>Введите, пожалуйста, новую цену:</i>"),
        MessageInput(process_new_price),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_prices),
        state=AdminStates.EDIT_PRICE,
    ),
    Window(
        Format("<i>Введите новую цену:</i>"),
        MessageInput(process_new_group_price),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_groups),
        state=AdminStates.EDIT_GROUP_PRICE,
    ),
]
