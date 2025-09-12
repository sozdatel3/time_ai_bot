from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const

from db.models.ai_promo import (
    create_ai_promo,
    get_all_ai_promos,
)
from dialogs.states import AdminStates


async def get_ai_promos_list(dialog_manager: DialogManager, **_):
    """Получаем список всех AI промокодов"""
    promos = await get_all_ai_promos()
    promo_list = []

    for promo in promos:
        status = "✅ Активен" if promo.is_active else "❌ Использован"
        promo_info = {
            "id": promo.id,
            "hash": promo.hash[:8]
            + "...",  # показываем только первые 8 символов
            "count": promo.count_of_predict,
            "status": status,
            "created_at": (
                promo.created_at.strftime("%d.%m.%Y %H:%M")
                if promo.created_at
                else "N/A"
            ),
            "display": f"🎁 {promo.count_of_predict} прогнозов | {status} | {promo.created_at.strftime('%d.%m.%Y') if promo.created_at else 'N/A'}",
        }
        promo_list.append(promo_info)

    return {"promos": promo_list, "promos_count": len(promo_list)}


async def switch_to_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """Возврат в главное меню админки"""
    await manager.switch_to(AdminStates.MAIN, show_mode=ShowMode.EDIT)


async def switch_to_create_promo(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """Переход к созданию промокода"""
    await manager.switch_to(
        AdminStates.AIPROMO_COUNT_INPUT, show_mode=ShowMode.EDIT
    )


async def switch_to_promo_list(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """Переход к списку промокодов"""
    await manager.switch_to(AdminStates.AIPROMO_MAIN, show_mode=ShowMode.EDIT)


async def back_to_promo_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """Возврат в главное меню промокодов"""
    await manager.switch_to(AdminStates.AIPROMO_MAIN, show_mode=ShowMode.EDIT)


async def process_promo_count(
    message: Message, dialog, manager: DialogManager
):
    """Обработка введенного количества прогнозов"""
    try:
        count = int(message.text)
        if count <= 0:
            await message.answer("Количество должно быть больше нуля.")
            return

        manager.dialog_data["promo_count"] = count
        admin_id = message.from_user.id

        # try:
        promo, url = await create_ai_promo(admin_id, count)

        # Отправляем промокод админу
        await message.delete()
        await message.answer(
            f"""
Промокод успешно создан!

<b><i>•</i></b> Количество прогнозов: {count}
<b><i>•</i></b> Ссылка:
<code>{url}</code>

Нажмите на ссылку, чтобы скопировать.
            """,
            parse_mode="HTML",
        )

        await manager.switch_to(
            AdminStates.AIPROMO_MAIN, show_mode=ShowMode.EDIT
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка при создании промокода: {str(e)}")


async def confirm_create_promo(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """Подтверждение создания промокода"""


async def cancel_create_promo(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    """Отмена создания промокода"""
    await manager.switch_to(AdminStates.AIPROMO_MAIN, show_mode=ShowMode.EDIT)


# async def on_promo_selected(
#     c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
# ):
#     """Обработка выбора промокода для деактивации"""
#     promo_id = int(item_id)

#     success = await deactivate_ai_promo(promo_id)
#     if success:
#         await c.message.answer("✅ Промокод деактивирован")
#     else:
#         await c.message.answer("❌ Ошибка при деактивации промокода")

#     await manager.switch_to(
#         AdminStates.AIPROMO_LIST, show_mode=ShowMode.DELETE_AND_SEND
#     )


ai_promo_windows = [
    Window(
        Const(
            """Управление AI-промокодами:

Создавайте ссылки с бесплатными AI-прогнозами для пользователей."""
        ),
        Row(
            Button(
                Const("➕ Создать промокод"),
                id="create_promo",
                on_click=switch_to_create_promo,
            ),
        ),
        Button(
            Const("◀️ Вернуться назад"),
            id="back_to_admin",
            on_click=switch_to_main,
        ),
        state=AdminStates.AIPROMO_MAIN,
        parse_mode="HTML",
    ),
    Window(
        Const(
            "<i>Введите количество бесплатных AI-прогнозов для промокода (от 1 до 100):</i>"
        ),
        MessageInput(process_promo_count),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=back_to_promo_main,
        ),
        state=AdminStates.AIPROMO_COUNT_INPUT,
        parse_mode="HTML",
    ),
    #     Window(
    #         Format(
    #             """
    # Количество прогнозов: {dialog_data[promo_count]}
    # Создать промокод?
    #             """
    #         ),
    #         Row(
    #             Button(
    #                 Const("✅ Создать"),
    #                 id="confirm",
    #                 on_click=,
    #             ),
    #             Button(
    #                 Const("❌ Отмена"),
    #                 id="cancel",
    #                 on_click=cancel_create_promo,
    #             ),
    #         ),
    #     state=AdminStates.AIPROMO_CONFIRM,
    #     parse_mode="HTML",
    # ),
    # Window(
    #     Const("📋 <b>Список промокодов</b>"),
    #     Format("\n📊 Всего промокодов: {promos_count}"),
    #     Select(
    #         Format("{item[display]}"),
    #         id="promo_select",
    #         item_id_getter=lambda x: x["id"],
    #         items="promos",
    #         on_click=on_promo_selected,
    #     ),
    #     Button(
    #         Const("◀️ Назад"),
    #         id="back",
    #         on_click=back_to_promo_main,
    #     ),
    #     state=AdminStates.AIPROMO_LIST,
    #     getter=get_ai_promos_list,
    #     parse_mode="HTML",
    # ),
]
