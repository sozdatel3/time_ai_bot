from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from db.models.old_workflow.links import get_all_links
from db.models.order import create_order
from dialogs.states import AdminStates
from utils.robokassa import do_robocassa


async def back_to_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        AdminStates.MAIN, show_mode=ShowMode.DELETE_AND_SEND
    )


async def get_links_list(dialog_manager: DialogManager, **_):
    links = await get_all_links()
    return {"links": links}


async def process_payment_link_sum(
    message: Message, dialog: Dialog, manager: DialogManager
):
    # pass
    # await m.start
    try:
        amount = int(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("<i>Пожалуйста, введите положительное число</i>")
        return

    order = await create_order(
        0,
        amount,
        "pending",
        f"custom_payment_link:{amount}",
        -1,
        balance_to_use=0,
    )
    # print("DIALOG_DATA\n\n", dialog_data)
    link = await do_robocassa(
        0,
        amount,
        order.id,
        f"custom_payment_link:{amount}",
        -1,
        is_recurring=False,
    )
    await message.answer(
        f"<a href='{link}'><i>[ Скрытая ссылка на оплату ]</i></a>"
    )
    try:
        await message.delete()
    except Exception as e:
        print(e)
    await manager.switch_to(
        AdminStates.PAYMENT_LINKS, show_mode=ShowMode.DELETE_AND_SEND
    )
    # await manager.switch_to(
    #     AdminStates.MAIN, show_mode=ShowMode.DELETE_AND_SEND
    # )


payment_links_windows = [
    Window(
        Format("<i>Введите сумму для создания платежной ссылки:</i>"),
        MessageInput(process_payment_link_sum),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=back_to_main),
        state=AdminStates.PAYMENT_LINKS,
    ),
]
