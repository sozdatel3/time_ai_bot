from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Group, Row, Url
from aiogram_dialog.widgets.text import Const, Format, Jinja

from config import config
from db.models.asto_info import get_astro_info
from db.models.order import create_order, update_order_status
from db.models.user import get_user, update_user_balance
from utils.robokassa import do_robocassa

from .states import PaymentStates, YogaClubStates, format_price_and_balance


async def get_payment_data(dialog_manager: DialogManager, **kwargs):
    try:
        # print("GET_PAYMENT_DATA")
        start_data = dialog_manager.start_data
        user_id = dialog_manager.event.from_user.id
        user = await get_user(user_id)
        total_amount = start_data["amount"]
        balance_to_use = min(user.balance, total_amount)
        # print("BALANCE_TO_USE\n\n", balance_to_use)
        if not dialog_manager.dialog_data.get("was_full"):
            amount_to_pay = total_amount - balance_to_use
        else:
            amount_to_pay = total_amount
        dialog_manager.dialog_data.update(
            {
                "total_amount": total_amount,
                "user_balance": user.balance,
                "balance_to_use": (
                    balance_to_use
                    if not dialog_manager.dialog_data.get("was_balance")
                    and not dialog_manager.dialog_data.get("was_full")
                    else dialog_manager.dialog_data.get("balance_to_use")
                ),
                "amount_to_pay": (
                    amount_to_pay
                    if not dialog_manager.dialog_data.get("was_balance")
                    else dialog_manager.dialog_data.get("amount_to_pay")
                ),
                "payment_link": dialog_manager.dialog_data.get(
                    "payment_link", ""
                ),
            }
        )
        if user.balance == 0 and not dialog_manager.dialog_data.get(
            "was_balance"
        ):
            await on_pay_full(None, None, dialog_manager)
    except Exception as e:
        print("ERROR IN GET_PAYMENT_DATA", e)

    data = dialog_manager.dialog_data
    return {
        "was_subscribe": dialog_manager.start_data.get("was_subscribe", None),
        "payment_link": data.get("payment_link", ""),
        "item_oficial_description": start_data.get(
            "item_oficial_description", ""
        ),
        "total_amount": data.get("total_amount"),
        "user_balance": data.get("user_balance"),
        "balance_to_use": data.get("balance_to_use"),
        "amount_to_pay": data.get("amount_to_pay"),
        "total_amount_str": format_price_and_balance(data.get("total_amount")),
        "user_balance_str": format_price_and_balance(data.get("user_balance")),
        "balance_to_use_str": format_price_and_balance(
            data.get("balance_to_use")
        ),
        "amount_to_pay_str": format_price_and_balance(
            data.get("amount_to_pay")
        ),
        "oferta_url": config.load_config().oferta_url,
        "item_description": start_data["description"],
        "previous_state": start_data["previous_state"],
        "item_id": start_data.get("item_id", -1),
        "extra_description": start_data.get("extra_description", "").format(
            price=format_price_and_balance(data.get("amount_to_pay"))
        ),
    }


async def on_use_balance(
    c: CallbackQuery, button: Button, manager: DialogManager
):

    dialog_data = manager.dialog_data
    # print("DIALOG_DATA\n\n", dialog_data)
    start_data = manager.start_data
    user_id = c.from_user.id

    dialog_data["was_balance"] = True

    order = await create_order(
        user_id,
        dialog_data["amount_to_pay"],
        "pending",
        start_data.get("description", "unknown"),
        start_data.get("item_id", -1),
        balance_to_use=dialog_data["balance_to_use"],
    )
    # print("DIALOG_DATA\n\n", dialog_data)
    if dialog_data["amount_to_pay"] > 0:
        link = await do_robocassa(
            user_id,
            dialog_data["amount_to_pay"],
            order.id,
            start_data.get("item_description", "unknown"),
            start_data.get("item_id", -1),
            is_recurring=start_data.get("was_subscribe", False),
        )
        dialog_data["payment_link"] = link
    else:
        # order.status = "paid_by_balance"
        # await order.save()
        await update_order_status(order.id, "paid_by_balance")
        await config.load_config().bot.payment_handler.handle_payment(order)
        # await on_back(None, None, manager)
        # return

    new_balance = dialog_data["user_balance"] - dialog_data["balance_to_use"]

    await update_user_balance(
        user_id,
        new_balance,
        froze=True,
        froze_value=dialog_data["balance_to_use"],
    )

    manager.dialog_data.update(dialog_data)
    if dialog_data["amount_to_pay"] > 0:
        await manager.switch_to(PaymentStates.payment)
    else:
        await manager.done()


async def on_pay_full(
    c: CallbackQuery | None, button: Button | None, manager: DialogManager
):
    # data = await get_payment_data(manager)
    # Получаем user_id либо из callback, либо из dialog_manager
    user_id = c.from_user.id if c else manager.event.from_user.id
    total_amount = manager.start_data["amount"]
    # manager.dialog_data["was_full"] = True
    order = await create_order(
        user_id,
        total_amount,
        "pending",
        manager.start_data["description"],
        manager.start_data.get("item_id", -1),
    )

    link = await do_robocassa(
        user_id,
        total_amount,
        order.id,
        manager.start_data["description"],
        manager.start_data.get("item_id", -1),
        is_recurring=manager.start_data.get("was_subscribe", False),
    )

    manager.dialog_data.update(
        {
            "payment_link": link,
            "oferta_url": config.load_config().oferta_url,
            "total_amount": total_amount,
            "balance_to_use": 0,
            "was_full": True,
            "amount_to_pay": total_amount,
            "item_oficial_description": manager.start_data.get(
                "item_oficial_description", ""
            ),
        }
    )

    await manager.switch_to(PaymentStates.payment)


async def on_back(c: CallbackQuery, button: Button, manager: DialogManager):
    previous_state = manager.start_data.get(
        "previous_state", YogaClubStates.main
    )
    astro_info = await get_astro_info(c.from_user.id)
    astro_info_name = None
    if astro_info is None:
        astro_info_name = c.from_user.first_name
    await manager.start(
        previous_state,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.DELETE_AND_SEND,
        data={
            "not_first_time": True,
            "name": astro_info_name or astro_info.name,
        },
    )


# Ваш текущий баланс: рублей
# Стоимость: {{total_amount}}рублей
payment_choice_text = Jinja(
    """
<b><i>Участие в закрытом сообществе 🫂</i></b>

<i><b>Стоимость:</b> {{total_amount_str}} рублей
</i><i><b>Ваш текущий баланс:</b> {{user_balance_str}} рублей

{% if was_subscribe %}
🔗 Оплачивая, вы даёте согласие на регулярные списания, обработку персональных данных и принимаете условия публичной оферты.</i>

{% endif %}
Выберите способ оплаты:
"""
)

# Для оплаты {{item_oficial_description}} за рублей, пожалуйста, перейдите по ссылке:

payment_text = Jinja(
    """
{% if balance_to_use > 0 %}
<i><b>Общая стоимость:</b> {{balance_to_use_str}} рублей
</i><i><b>Использовано с баланса:</b> {{balance_to_use_str}} рублей
</i><i><b>К оплате:</b> {{amount_to_pay_str}} рублей</i>

{% endif %}
{% if amount_to_pay > 0 %}
<i>Чтобы оплатить услугу перейдите, пожалуйста, по ссылке</i> 🪶<i>
</i>
<i>[</i> <i>Платеж может занять от 30 секунд до 5 минут. </i><b><i>Спасибо за ваше терпение</i>.</b> <i>]</i> 
{% else %}
Оплата прошла успешно! Спасибо за покупку.
{% endif %}

{% if was_subscribe %}
<i>🔗 Оплачивая, вы даёте согласие на регулярные списания, обработку персональных данных и принимаете условия публичной оферты.</i>
{% endif %}
"""
)

payment_dialog = Dialog(
    Window(
        payment_choice_text,
        Group(
            Button(
                Const("Оплатить с баланса"),
                id="use_balance",
                on_click=on_use_balance,
            ),
            Button(
                Const("Оплатить полную сумму"),
                id="pay_full",
                on_click=on_pay_full,
            ),
            Button(Const("Вернуться назад"), id="back", on_click=on_back),
        ),
        state=PaymentStates.payment_choice,
        getter=get_payment_data,
    ),
    Window(
        Format("{extra_description}"),
        payment_text,
        Row(
            Url(
                Const("Приобрести"),
                id="pay",
                url=Format("{payment_link}"),
            ),
            Url(Const("ОФЕРТА"), id="oferta", url=Format("{oferta_url}")),
        ),
        Button(Const("<< Вернуться назад"), id="back", on_click=on_back),
        state=PaymentStates.payment,
        getter=get_payment_data,
    ),
)
