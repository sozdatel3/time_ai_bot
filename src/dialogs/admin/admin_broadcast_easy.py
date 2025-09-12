import asyncio
import datetime
from typing import Any, Dict

from aiogram.types import CallbackQuery, Message

# from aiogram.utils.markdown import Const
from aiogram_dialog import Dialog, DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Group, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format

from db.models.old_workflow.ab_group import get_ab_groups
from db.models.old_workflow.broadcast import (
    create_broadcast,
    mark_broadcast_delivered,
    mark_broadcast_failed,
)
from db.models.user import (
    get_all_user_ids,
    get_users_bought,
    get_users_by_ab_group,
    get_users_not_bought,
    get_users_not_bought_but,
    get_users_not_today,
    get_users_today,
)
from dialogs.states import AdminStates


async def whom_to_broadcast(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    try:
        button_id = button.widget_id
        manager.dialog_data["whom_to_broadcast"] = button_id
    except Exception as e:
        print(f"Error: {e}")
        await c.message.answer("Произошла ошибка при получении пользователей.")
        return
    await manager.switch_to(AdminStates.BROADCAST_SEND)


async def broadcast(
    message: Message, users, column_name: str
) -> Dict[str, int]:
    success_count = 0
    fail_count = 0

    for user in users:
        try:
            await message.copy_to(user)
            await mark_broadcast_delivered(user, column_name)
            success_count += 1
        except Exception:
            await mark_broadcast_failed(user, column_name)
            fail_count += 1

        await asyncio.sleep(0.01)  # Уменьшенная задержка для оптимизации

    return {"success": success_count, "fail": fail_count}


async def broadcast_for_everybody(message: Message, users, column_name: str):
    try:
        results = await broadcast(message, users, column_name)
    except Exception as e:
        print(f"Error: {e}")
        # await message.bot.send_message(
        #     message.chat.id, f"Произошла ошибка при отправке рассылки. {e}"
        # )

    await message.bot.send_message(
        message.chat.id,
        f"""
<b><i>Рассылка завершена </i></b>🚀 
<i>Успешно: {results['success']}
Не удалось: {results['fail']}</i>
        """,
        # f"Рассылка завершена.\nУспешно: \nНе удалось: ",
    )


async def process_broadcast_message(
    message: Message, dialog: Dialog, manager: DialogManager
):
    whom_to_broadcast = manager.dialog_data["whom_to_broadcast"]
    column_name = f"broadcast_{whom_to_broadcast}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    # column_name = generate_unique_column_name()
    await create_broadcast(column_name)
    # print("\n\ncolumn_name\n\n", column_name)
    try:
        if whom_to_broadcast.startswith("ab_group_"):
            group_number = int(whom_to_broadcast.split("_")[2])
            users = await get_users_by_ab_group(group_number)
        elif whom_to_broadcast == "broadcast_all":
            users = await get_all_user_ids()
        elif whom_to_broadcast == "broadcast_bought":
            users = await get_users_bought()
        elif whom_to_broadcast == "broadcast_not_bought":
            users = await get_users_not_bought()
        elif whom_to_broadcast == "broadcast_not_bought_but":
            users = await get_users_not_bought_but()
        elif whom_to_broadcast == "broadcast_today":
            users = await get_users_today()
        elif whom_to_broadcast == "broadcast_not_today":
            users = await get_users_not_today()

        # print("\n\nUSERS\n\n", users)
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("Произошла ошибка при получении пользователей.")
        # return

    # try:
    #     results = await broadcast(message, users, column_name)
    # except Exception as e:
    #     print(f"Error: {e}")
    #     await message.reply(f"Произошла ошибка при отправке рассылки. {e}")
    # return
    asyncio.create_task(broadcast_for_everybody(message, users, column_name))

    await message.reply(
        "<i>Рассылка запущена в фоновом режиме. Вам придет уведомление когда она будет завершена.</i>"
    )
    # await message.delete()
    await manager.switch_to(
        AdminStates.MAIN, show_mode=ShowMode.DELETE_AND_SEND
    )


async def switch_to_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.MAIN)


async def setup_ab_group_buttons(dialog: Dialog):
    groups = await get_ab_groups()
    group_window = dialog.find_window(AdminStates.BROADCAST_AB_GROUPS)

    for group in groups:
        group_window.widgets.append(
            Button(
                Const(f"Группа {group.group_number}: {group.name}"),
                id=f"group_{group.group_number}",
                on_click=select_ab_group,
            )
        )


# async def get_ab_groups_for_window(**kwargs):
#     groups = await get_ab_groups()
#     return {
#         "groups": "\n".join(
#             f"Группа {g.group_number}: {g.name}" for g in groups
#         )
#     }


# async def select_ab_group(
#     c: CallbackQuery, button: Button, manager: DialogManager
# ):
#     group_number = int(button.widget_id.split("_")[1])
#     manager.dialog_data["whom_to_broadcast"] = f"ab_group_{group_number}"
#     await manager.switch_to(AdminStates.BROADCAST_SEND)


async def get_ab_groups_for_window(**kwargs):
    groups = await get_ab_groups()
    return {
        "groups": [
            {
                "id": group.group_number,
                "name": f"Группа {group.group_number}: {group.name}",
            }
            for group in groups
        ]
    }


async def select_ab_group(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    group_number = int(item_id)
    manager.dialog_data["whom_to_broadcast"] = f"ab_group_{group_number}"
    await manager.switch_to(AdminStates.BROADCAST_SEND)


async def show_ab_groups(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.BROADCAST_AB_GROUPS)


broadcast_easy_windows = [
    Window(
        Const("Кому отправить сообщение?"),
        # MessageInput(process_broadcast_message),
        # Button(
        #     Const("Отправить определенной A/B группе"),
        #     id="show_ab_groups",
        #     on_click=show_ab_groups,
        # ),
        Button(
            Const("Все пользователи"),
            id="broadcast_all",
            on_click=whom_to_broadcast,
        ),
        # Button(
        #     Const("Все, с покупкой"),
        #     id="broadcast_bought",
        #     on_click=whom_to_broadcast,
        # ),
        # Button(
        #     Const("Все, без покупки"),
        #     id="broadcast_not_bought",
        #     on_click=whom_to_broadcast,
        # ),
        # Button(
        #     Const("Все, кто дошел до покупки, но не купил"),
        #     id="broadcast_not_bought_but",
        #     on_click=whom_to_broadcast,
        # ),
        Button(
            Const("Все, кто добавился сегодня"),
            id="broadcast_today",
            on_click=whom_to_broadcast,
        ),
        Button(
            Const("Все, кто добавился не сегодня"),
            id="broadcast_not_today",
            on_click=whom_to_broadcast,
        ),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=switch_to_main),
        state=AdminStates.BROADCAST,
    ),
    # Window(
    #     Const("Выберите A/B группу для рассылки:"),
    #     Format("{groups}"),
    #     # Динамические кнопки для групп будут добавлены через getter
    #     Button(
    #         Const("◀️ Вернуться назад"),
    #         id="back",
    #         on_click=lambda c, b, m: m.switch_to(AdminStates.BROADCAST),
    #     ),
    #     state=AdminStates.BROADCAST_AB_GROUPS,
    #     getter=get_ab_groups_for_window,
    # ),
    Window(
        Const("Выберите A/B группу для рассылки:"),
        Group(
            Select(
                Format("{item[name]}"),
                id="group_select",
                item_id_getter=lambda x: x["id"],
                items="groups",
                on_click=select_ab_group,
            ),
            width=1,
        ),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=lambda c, b, m: m.switch_to(AdminStates.BROADCAST),
        ),
        state=AdminStates.BROADCAST_AB_GROUPS,
        getter=get_ab_groups_for_window,
    ),
    Window(
        Const("Отправьте сообщение для рассылки:"),
        MessageInput(process_broadcast_message),
        # SwitchTo(Const("◀️ Вернуться назад"), id="back", on_click=switch_to_main),
        SwitchTo(
            Const("◀️ Вернуться назад"), id="back", state=AdminStates.BROADCAST
        ),
        state=AdminStates.BROADCAST_SEND,
    ),
]
