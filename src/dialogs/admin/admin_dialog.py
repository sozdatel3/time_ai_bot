import datetime
from typing import Any

from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram_dialog import Dialog, DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row, Select
from aiogram_dialog.widgets.text import Const, Format

from config.config import ADMIN_IDS
from db.models.old_workflow.big_mes import get_pay_photo_attachment
from db.models.old_workflow.useful_material import (
    add_useful_material,
    delete_useful_material,
    get_useful_material,
    get_useful_materials,
)
from db.models.user import get_all_user_ids
from dialogs.admin.admin_ai_promo import ai_promo_windows
from dialogs.admin.admin_broadcast_easy import broadcast_easy_windows
from dialogs.admin.admin_certificates import admin_certificates_windows
from dialogs.admin.admin_links import links_windows
from dialogs.admin.admin_payment_link import payment_links_windows
from dialogs.admin.admin_prices import prices_windows
from dialogs.states import AdminStates, StatisticStates, YogaClubStates


def generate_unique_column_name():
    return f"broadcast_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"


async def switch_to_prices(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.PRICES)


async def admin_access_middleware(event, data):
    user_id = event.from_user.id
    return user_id in ADMIN_IDS


async def get_materials_list(dialog_manager: DialogManager, **_):
    materials = await get_useful_materials()
    materials_photo = await get_pay_photo_attachment(
        dialog_manager.event.bot, "misk/navigation/usefull_admin.png"
    )
    return {
        "materials": materials,
        "materials_list": "\n".join(
            [f"<b><i>•</i></b> «{m.name}»" for m in materials]
        ),
        "materials_photo": materials_photo,
    }


async def admin_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(AdminStates.MAIN)


async def process_material_message(
    message: Message, dialog: Dialog, manager: DialogManager
):
    manager.dialog_data["message_id"] = message.message_id
    manager.dialog_data["chat_id"] = message.chat.id
    await message.delete()
    await manager.switch_to(
        AdminStates.ADD_MATERIAL_NAME, show_mode=ShowMode.EDIT
    )


async def process_material_name(
    message: Message, dialog: Dialog, manager: DialogManager
):
    manager.dialog_data["is_free"] = True
    manager.dialog_data["material_name"] = message.text
    await message.delete()
    await manager.switch_to(
        AdminStates.NOTIFICATION_CHOICE, show_mode=ShowMode.EDIT
    )


async def set_free_material(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["is_free"] = True
    await manager.switch_to(AdminStates.NOTIFICATION_CHOICE)


async def set_paid_material(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    manager.dialog_data["is_free"] = False
    await manager.switch_to(AdminStates.NOTIFICATION_CHOICE)


async def on_material_selected(
    c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str
):
    material_id = int(item_id)
    material = await get_useful_material(material_id)
    if material:
        await delete_useful_material(material_id)
        await c.message.answer(
            f"<i>Материал «{material.name}» успешно удален.</i>"
        )
    await manager.switch_to(
        AdminStates.MATERIALS, show_mode=ShowMode.DELETE_AND_SEND
    )


async def switch_to_broadcast(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.BROADCAST, show_mode=ShowMode.EDIT)


async def switch_to_materials(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.MATERIALS, show_mode=ShowMode.EDIT)


async def switch_to_main(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.MAIN, show_mode=ShowMode.EDIT)


async def switch_to_add_material(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.ADD_MATERIAL, show_mode=ShowMode.EDIT)


async def switch_to_delete_material(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        AdminStates.DELETE_MATERIAL, show_mode=ShowMode.EDIT
    )


async def notify_users_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    data = manager.dialog_data
    material = await add_useful_material(
        name=data["material_name"],
        message_id=data["message_id"],
        chat_id=data["chat_id"],
        created_by=c.from_user.id,
        is_free=data["is_free"],
    )

    user_ids = await get_all_user_ids()
    success_count = 0
    fail_count = 0

    for user_id in user_ids:
        try:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="> Полезные материалы <",
                            callback_data="useful_materials_callback",
                        )
                    ]
                ]
            )
            await c.bot.send_photo(
                user_id,
                FSInputFile("misk/spam/material.png"),
                # f"Новый полезный материал '{material.name}' доступен! Проверьте раздел 'Полезные материалы'.",
                caption="""
<i>🌪️ Сила мысли в действии! </i>
<i><b>Новый бесплатный материал ждёт вас в боте!</b> (Результаты, которые изменят жизнь).
</i>
<i>Привет!</i>

<b><i>Рады поделиться мощным обновлением:</i></b> <i>в нашем боте появился совершенно новый бесплатный материал,</i> который <u><i>станет вашим</i> </u><i><u>проводником</u></i> к реальным изменениям.

⚡️<b><i>О чём это?</i></b> <i>Мы углубимся в удивительный синтез:</i>

<i><b><b><i>•</i></b></b> Психологии энергии мышления — как ваши мысли буквально формируют реальность.
</i>
<i><b><b><i>•</i></b></b> Практической эзотерики — древние и современные инструменты для работы с внутренней силой.</i>

<i>И самое главное </i><i><b>— РЕЗУЛЬТАТ,</b> на котором мы фокусируемся:</i>

Это не просто теория, а концентрат знаний и практик, направленных на конкретный результат <b><i>— вашу новую, более счастливую и свободную реальность</i></b> 💫<b><i>
</i></b>
<i>Не упустите!</i> 
<i>Этот материал уже ждёт вас в боте </i><b><i>в разделе «Полезные материалы»</i></b> 🧠
                """,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            success_count += 1
        except Exception:
            fail_count += 1

        # f"Уведомление отправлено.\nУспешно: \nНе удалось: "
    await c.message.answer(
        f"""<b><i>Уведомление отправлено</i> 🚀</b><i>
Успешно: {success_count}
Не удалось: {fail_count}</i>"""
    )
    await manager.switch_to(
        AdminStates.MATERIALS, show_mode=ShowMode.DELETE_AND_SEND
    )


async def dont_notify_users_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    data = manager.dialog_data
    await add_useful_material(
        name=data["material_name"],
        message_id=data["message_id"],
        chat_id=data["chat_id"],
        created_by=c.from_user.id,
        is_free=data["is_free"],
    )
    await c.message.answer(
        f"<i>Материал «{data['material_name']}» успешно добавлен.</i>"
    )
    await manager.switch_to(
        AdminStates.MATERIALS, show_mode=ShowMode.DELETE_AND_SEND
    )


async def on_main_menu(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(
        YogaClubStates.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT,
    )


async def switch_to_statistics(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(StatisticStates.main, show_mode=ShowMode.EDIT)


async def switch_to_create_certificate(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        AdminStates.CREATE_CERTIFICATE, show_mode=ShowMode.EDIT
    )


async def switch_to_links(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.LINKS, show_mode=ShowMode.EDIT)


async def switch_to_payment_links(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.PAYMENT_LINKS, show_mode=ShowMode.EDIT)


async def switch_to_ai_promo(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.AIPROMO_MAIN, show_mode=ShowMode.EDIT)


async def switch_to_add_material_name(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        AdminStates.ADD_MATERIAL_NAME, show_mode=ShowMode.EDIT
    )


async def switch_to_settings(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.SETTINGS_MAIN, show_mode=ShowMode.EDIT)


async def switch_to_event_planning(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        AdminStates.EVENT_PLANNING, show_mode=ShowMode.EDIT
    )


async def stop_payment(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(AdminStates.STOP_PAYMENT, show_mode=ShowMode.EDIT)


async def get_rich(dialog_manager: DialogManager, **_):
    rich = await get_pay_photo_attachment(
        dialog_manager.event.bot, "misk/navigation/rich.png"
    )
    return {"rich": rich}


async def get_agutin(dialog_manager: DialogManager, **_):
    agutin = await get_pay_photo_attachment(
        dialog_manager.event.bot, "misk/navigation/agutin.jpg"
    )
    print(agutin)
    return {"agutin": agutin}


async def get_boss(dialog_manager: DialogManager, **_):
    boss = await get_pay_photo_attachment(
        dialog_manager.event.bot, "misk/navigation/boss.jpeg"
    )
    return {"boss": boss}


admin_dialog = Dialog(
    Window(
        # DynamicMedia("boss", when="boss"),
        Const("Панель администратора:"),
        Button(
            Const("📢 Создать рассылку"),
            id="broadcast",
            on_click=switch_to_broadcast,
        ),
        # Button(
        #     Const("📚 Управление материалами"),
        #     id="materials",
        #     on_click=switch_to_materials,
        # ),
        # Button(
        #     Const("💸 Ссылки на оплату"),
        #     id="payment_links",
        #     on_click=switch_to_payment_links,
        # ),
        Button(
            Const("🔗 Управление ссылками"),
            id="links",
            on_click=switch_to_links,
        ),
        # Button(
        #     Const("💰 Управление ценами"),
        #     id="prices",
        #     on_click=switch_to_prices,
        # ),
        # Button(
        #     Const("🎁 AI-промокоды"),
        #     id="ai_promo",
        #     on_click=switch_to_ai_promo,
        # ),
        # Button(
        #     Const("💸 Сгенерировать промокод на клуб"),
        #     id="generate_free_yoga_club_promo",
        #     on_click=generate_free_yoga_club_promo,
        # ),
        Button(
            Const("📊 Статистика"),
            id="statistics",
            on_click=switch_to_statistics,
        ),
        # Button(
        #     Const("🎫 Создать сертификат"),
        #     id="create_certificate",
        #     on_click=switch_to_create_certificate,
        # ),
        # Button(
        #     Const("📅 Планирование мероприятия"),
        #     id="event_planning",
        #     on_click=switch_to_event_planning,
        # ),
        Button(
            Const("Вернуться в главное меню"),
            id="main_menu",
            on_click=on_main_menu,
        ),
        state=AdminStates.MAIN,
        # getter=get_boss,
    ),
    Window(
        # DynamicMedia("materials_photo", when="materials_photo"),
        Const("Управление материалами:\n"),
        Format("{materials_list}"),
        Row(
            Button(
                Const("➕ Добавить"), id="add", on_click=switch_to_add_material
            ),
            Button(
                Const("🗑 Удалить"),
                id="delete",
                on_click=switch_to_delete_material,
            ),
        ),
        Button(Const("◀️ Вернуться назад"), id="back", on_click=switch_to_main),
        state=AdminStates.MATERIALS,
        getter=get_materials_list,
    ),
    Window(
        Const("Отправьте материал (аудио/текст/файл/видео):"),
        MessageInput(process_material_message),
        Button(
            Const("◀️ Вернуться назад"), id="back", on_click=switch_to_materials
        ),
        state=AdminStates.ADD_MATERIAL,
    ),
    Window(
        Const("Введите название для материала:"),
        MessageInput(process_material_name),
        Button(
            Const("◀️ Вернуться назад"),
            id="back",
            on_click=switch_to_add_material,
        ),
        state=AdminStates.ADD_MATERIAL_NAME,
    ),
    Window(
        Const("Выберите материал для удаления:"),
        Select(
            Format("{item.name}"),
            id="material_select",
            item_id_getter=lambda x: x.id,
            items="materials",
            on_click=on_material_selected,
        ),
        Button(
            Const("◀️ Вернуться назад"), id="back", on_click=switch_to_materials
        ),
        state=AdminStates.DELETE_MATERIAL,
        getter=get_materials_list,
    ),
    Window(
        Const("Отправить уведомление пользователям о новом материале?"),
        Row(
            Button(
                Const("Да"), id="notify_yes", on_click=notify_users_handler
            ),
            Button(
                Const("Нет"),
                id="notify_no",
                on_click=dont_notify_users_handler,
            ),
        ),
        state=AdminStates.NOTIFICATION_CHOICE,
    ),
    *admin_certificates_windows,
    *prices_windows,
    *links_windows,
    *broadcast_easy_windows,
    *ai_promo_windows,
    *payment_links_windows,
)
