from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const, Format, Jinja

from db.models.old_workflow.certificate import create_certificate
from db.models.old_workflow.person_button import increment_tap_person_button
from db.models.old_workflow.yoga_tap import increment_tap
from db.models.user import get_user

from .states import (
    AskQuestionStates,
    CertificatesStates,
    PaymentStates,
    YogaClubStates,
)


async def certificates_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await increment_tap("Сертификаты")
    await increment_tap_person_button("Сертификаты", c.from_user.id)
    await manager.start(CertificatesStates.main)


async def on_amount_entered(
    message: Message, widget: Any, manager: DialogManager, amount: str
):
    try:
        amount = float(amount)
        if amount <= 0:
            await message.answer(
                "Сумма должна быть положительным числом. Пожалуйста, введите корректную сумму."
            )
            return
        manager.dialog_data["amount"] = amount
        await manager.switch_to(CertificatesStates.confirm_purchase)
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректную сумму без пробелов и символов, например 10000"
        )


async def on_confirm_purchase(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    user_id = c.from_user.id
    user = await get_user(user_id)
    amount = manager.dialog_data["amount"]
    certificate = await create_certificate(user_id, amount)

    await manager.start(
        (
            PaymentStates.payment_choice
            if user.balance > 0
            else PaymentStates.payment
        ),
        data={
            "amount": amount,
            "description": "certificate",
            "previous_state": CertificatesStates.main,
            "item_oficial_description": f"Подарочный сертификат на {amount}рублей",
            "item_id": certificate.id,
        },
    )


async def on_cancel(c: CallbackQuery, button: Button, manager: DialogManager):
    await manager.switch_to(CertificatesStates.main)


async def on_main_menu(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(YogaClubStates.main, mode=StartMode.RESET_STACK)


async def on_ask_question(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(AskQuestionStates.waiting_for_question)


async def get_confirm_purchase_data(dialog_manager: DialogManager, **kwargs):
    return {"amount": dialog_manager.dialog_data["amount"]}


async def on_buy_certificate(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(CertificatesStates.enter_amount)


certificates_text = Jinja(
    """
<b>Подарочный сертификат: Подарите возможность трансформации и развития</b>

Здесь вы можете приобрести подарочный сертификат на любую сумму.

Получатель сертификата сможет использовать его для оплаты подписки на женский клуб.
"""
)


certificates_dialog = Dialog(
    Window(
        certificates_text,
        # Row(
        Button(
            Const("Купить сертификат"),
            id="buy",
            on_click=on_buy_certificate,
        ),
        Button(
            Const("Вернуться в главное меню"),
            id="main_menu",
            on_click=on_main_menu,
        ),
        # Button(
        #     Const("Задать вопрос"),
        #     id="ask_question",
        #     on_click=on_ask_question,
        # ),
        # ),
        state=CertificatesStates.main,
    ),
    Window(
        Const("Введите сумму сертификата:"),
        TextInput(id="amount", on_success=on_amount_entered),
        Button(Const("Отмена"), id="cancel", on_click=on_cancel),
        state=CertificatesStates.enter_amount,
    ),
    Window(
        Format(
            "Вы собираетесь приобрести сертификат на сумму {amount} рублей.\n"
            "Подтверждаете покупку?"
        ),
        Row(
            Button(
                Const("Подтвердить"),
                id="confirm",
                on_click=on_confirm_purchase,
            ),
            Button(Const("Отмена"), id="cancel", on_click=on_cancel),
        ),
        state=CertificatesStates.confirm_purchase,
        getter=get_confirm_purchase_data,
    ),
)
