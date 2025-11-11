from pathlib import Path
from typing import Any

from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram_dialog import DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const, Format

from db.models.old_workflow.certificate import create_certificate
from dialogs.states import AdminStates


async def on_amount_entered(
    message: Message, widget: Any, manager: DialogManager, amount: str
):
    try:
        amount = float(amount)
        if amount <= 0:
            await message.answer(
                "<i>Сумма должна быть положительным числом. Пожалуйста, введите корректную сумму.</i>"
            )
            return
        manager.dialog_data["amount"] = amount
        await manager.switch_to(AdminStates.CONFIRM_CERTIFICATE)
    except ValueError:
        await message.answer(
            "<i>Пожалуйста, введите корректную сумму без пробелов и символов, например 10000</i>"
        )


async def on_confirm_certificate(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    amount = manager.dialog_data["amount"]
    admin_id = c.from_user.id

    certificate = await create_certificate(admin_id, amount)
    try:
        # Отправляем изображение сертификата и ссылку для активации
        await c.message.answer_photo(
            photo=FSInputFile(
                str(
                    Path(__file__).resolve().parent.parent
                    / "misk"
                    / "sertificate.png"
                )
            ),
            caption=f"Сертификат на сумму {amount}рублей\n\n"
            f"Отправьте это сообщение получателю сертификата.\n"
            f"Ссылка для активации: {certificate.url}",
        )
    except Exception as e:
        print(e)

    await manager.switch_to(
        AdminStates.MAIN, show_mode=ShowMode.DELETE_AND_SEND
    )


async def on_cancel(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(AdminStates.MAIN)


async def get_confirm_data(dialog_manager: DialogManager, **kwargs):
    return {
        "amount": dialog_manager.dialog_data["amount"],
    }


# Окна для добавления в admin_dialog.py
admin_certificates_windows = [
    Window(
        Const("Введите сумму сертификата:"),
        TextInput(id="amount", on_success=on_amount_entered),
        Button(Const("Отмена"), id="cancel", on_click=on_cancel),
        state=AdminStates.CREATE_CERTIFICATE,
    ),
    Window(
        Format(
            "Создание сертификата на сумму {amount} рублей\n\n"
            "Подтверждаете создание?"
        ),
        Row(
            Button(
                Const("Подтвердить"),
                id="confirm",
                on_click=on_confirm_certificate,
            ),
            Button(Const("Отмена"), id="cancel", on_click=on_cancel),
        ),
        state=AdminStates.CONFIRM_CERTIFICATE,
        getter=get_confirm_data,
    ),
]
