import urllib.parse
from pathlib import Path

from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Format

from config.config import get_config
from db.models.old_workflow.big_mes import get_pay_photo_attachment
from db.models.user import get_user
from dialogs.states import (
    ReferProgramStates,
    YogaClubStates,
    format_price_and_balance,
)


async def referral_program_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    # await increment_tap("Реферальная программа")
    await manager.start(ReferProgramStates.main)


async def on_main_menu(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    # await manager.start(MainMenuStates.main, mode=StartMode.RESET_STACK)
    if manager.start_data:
        prev_state = manager.start_data.get("prev_state")
        if prev_state:
            await manager.start(prev_state, mode=StartMode.RESET_STACK)
    else:
        await manager.start(YogaClubStates.main, mode=StartMode.RESET_STACK)


async def get_refer_program_balance(dialog_manager: DialogManager, **kwargs):
    try:
        config = get_config()
        bot_link = config.bot.link
        user = await get_user(dialog_manager.event.from_user.id)
        referral_link = f"{config.bot.link}?start=refer_{user.user_id}"

        share_text = """Канал — источник трансформации и исполнения желаний через энергию и мышление!

Присоединяйтесь к нашему потоку возможностей⚡️"""
        encoded_text = urllib.parse.quote(share_text)
        share_url = (
            f"https://t.me/share/url?url={referral_link}&text={encoded_text}"
        )
        balance_str = format_price_and_balance(user.balance)
        result = {
            "balance": user.balance,
            "id": user.user_id,
            "bot_link": bot_link,
            "refer_link": referral_link,
            "share_url": share_url,
            "balance_str": balance_str,
            "have_balance": user.balance > 0,
        }
    except Exception as e:
        print("error in get_refer_program_balance", e)
        result = {
            "balance": 0,
            "id": 0,
            "bot_link": bot_link,
            "balance_str": "0",
            "have_balance": False,
        }

    try:
        refer_photo = await get_pay_photo_attachment(
            dialog_manager.event.bot,
            str(
                Path(__file__).resolve().parent.parent
                / "misk"
                / "navigation"
                / "refer.png"
            ),
        )
        result["ref_program_photo"] = refer_photo
    except Exception as e:
        print(e)
        result["ref_program_photo"] = None
    return result


referral_program_dialog = Dialog(
    Window(
        # NestedJinja("{ref_program_text}"),
        DynamicMedia("ref_program_photo", when="ref_program_photo"),
        Format(
            """
<b><i>Преобразите свою жизнь и делитесь возможностями 🪐</i></b>

<i><b>Приглашайте друзей в наше сообщество,</b> где через работу с мышлением и энергией мы раскрываем потенциал во всех сферах жизни! </i>

За каждого друга, оформившего подписку, <b><i>вы получите 10% бонусов на свой баланс.</i></b> Эти бонусы можно использовать для оплаты подписки — чем больше друзей присоединится, тем дольше вы учитесь бесплатно! 

<b><i>Почему это важно?</i></b>

<b><i><b><i>•</i></b></i></b> <i>Помогаете другим расти вместе с вами.
</i>
<b><i><b><i>•</i></b></i></b> <i>Укрепляете свои практики, делясь энергией развития.
</i>
<b><i><b><i>•</i></b></i></b> <i>Создаёте общее поле позитивных изменений!</i>

Не упустите шанс сделать свой путь ярче, а подписку — выгоднее. <i>Жмите </i><i><b>«Пригласить»</b> и начните зарабатывать бонусы уже сегодня</i> 🌪️

<u><i>Вместе мы меняем жизни</i></u> <i>к лучшему</i> 🫂 Вы — важная часть этого преображения!
"""
        ),
        Format(
            """<i><b><b><i>•</i></b></b> Баланс на вашем счёте —  {balance_str} 💫</i>""",
            when="have_balance",
        ),
        #    \nТвой баланс: ", ),
        # Row(
        Url(
            Format("> Пригласить <"),
            id="share_referral_link2",
            # on_click=share_referral_link_handler,
            url=Format(
                "{share_url}",
            ),
        ),
        Format(
            """<i>[</i> <i>Чтобы скопировать ссылку, достаточно нажать на неё: </i><code><i>{refer_link}</i></code><i> ]</i>"""
        ),
        # Format("<code></code>"),
        Button(
            Format("Вернуться назад"),
            id="back_to_main_menu",
            on_click=on_main_menu,
        ),
        # ),
        state=ReferProgramStates.main,
        getter=get_refer_program_balance,
        disable_web_page_preview=True,
    )
)

# /tanya
