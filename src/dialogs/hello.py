from typing import Any

from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    RequestContact,
)
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory
from aiogram_dialog.widgets.text import Const, Format

from db.models.user import set_name, set_phone

# from handlers.payment_handler import process_subscription_payment
from .states import (
    YogaClubStates,
)


async def name_getter(dialog_manager: DialogManager, **_):
    if dialog_manager.start_data:
        user_id = dialog_manager.start_data.get("user_id")
        full_name = dialog_manager.start_data.get("full_name")
        username = dialog_manager.start_data.get("username")
    else:
        user_id = dialog_manager.event.from_user.id
        full_name = dialog_manager.event.from_user.full_name
        username = dialog_manager.event.from_user.username
    # full_name = dialog_manager.event.from_user.full_name
    splited_full_name = full_name.split(" ")
    dialog_manager.dialog_data["first_name"] = splited_full_name[0]
    return {
        "first_name": splited_full_name[0],
        # "last_name": splited_full_name[1],
    }


async def on_name_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await set_name(c.from_user.id, manager.dialog_data["first_name"])
    await manager.switch_to(
        YogaClubStates.phone_input, show_mode=ShowMode.EDIT
    )


async def name_handler(
    message: Message, widget: Any, manager: DialogManager, name: str
):
    # print("on_save_name", name)
    try:
        await set_name(message.from_user.id, name)
    except Exception as e:
        print(e)
    try:
        await message.delete()
    except Exception as e:
        print(e)
    await manager.switch_to(
        YogaClubStates.phone_input, show_mode=ShowMode.DELETE_AND_SEND
    )


async def on_save_phone(message: Message, widget, manager: DialogManager):
    if message.contact:
        try:
            phone = message.contact.phone_number
        except Exception as e:
            print(e)
            phone = "Не указан"
    else:
        phone = message.text

    # Save the phone number to the database
    await set_phone(message.from_user.id, phone=phone)
    try:
        await message.delete()
    except Exception as e:
        print(e)

    await manager.switch_to(
        YogaClubStates.main, show_mode=ShowMode.DELETE_AND_SEND
    )


hello_windows = [
    Window(
        Format(
            """
<i>Добро пожаловать в бот </i><b><i>«Энергия Жизни»</i></b> 🪐<i> </i>

Мы хотим обращаться к вам по имени <b><i>— так приятнее и личнее!</i></b> Вас зовут {first_name}, верно?

<i>Если нет, напишите, пожалуйста, как вас зовут</i>⚡️
               """
        ),
        Button(
            Const("Да"),
            id="yes_name",
            on_click=on_name_handler,
        ),
        TextInput(id="name_input", on_success=name_handler),
        # SwitchTo(Const("Нет"), id="no_name", state=YogaClubStates.name_2),
        # TextInput(id = "name_input", on_success=name_handler),
        state=YogaClubStates.name,
        getter=name_getter,
    ),
    Window(
        Format("s"),
        state=YogaClubStates.name_2,
    ),
    Window(
        Format(
            """
Отправьте, пожалуйста, <i>свой номер телефона через кликабельную кнопку ниже</i>⚡️ 
<b><i>Обещаю не звонить!</i></b>

<i>[</i><i> Вся информация является конфиденциальной: она не передаётся и не продаётся третьим лицам, хранится исключительно у нас в соответствии с условиями </i><a href="https://drive.google.com/file/d/1B6T3sQcDebjOAEhTtM1Viekw8imdQ2zA/view?usp=sharing"><i>публичного договора оферты.</i></a><i> ]</i>
"""
        ),
        RequestContact(
            Format("Поделиться контактом"),
            # on_click=on_contact_received,
        ),
        MessageInput(
            on_save_phone,
            content_types=[ContentType.CONTACT, ContentType.TEXT],
        ),
        markup_factory=ReplyKeyboardFactory(
            input_field_placeholder=Format("{event.from_user.username}"),
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
        state=YogaClubStates.phone_input,
    ),
]
