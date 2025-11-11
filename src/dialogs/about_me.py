from pathlib import Path

from aiogram import F
from aiogram.types import CallbackQuery
from aiogram_dialog import (
    Dialog,
    DialogManager,
    ShowMode,
    Window,
)
from aiogram_dialog.widgets.kbd import Button, Row, SwitchTo, Url
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from db.models.old_workflow.big_mes import get_pay_photo_attachment
from db.models.price import BASE_PRICES_RU_SHORT, EXTRA_DESCRIPTIONS
from db.models.user import get_user
from dialogs.main_menu import on_main_menu
from dialogs.states import AboutMeStates, PaymentStates, get_price_for_user

FULL_TEXT = [
    """
<i>Привет, привет 🫂

Хочу немного рассказать о себе </i><i><b>и погрузить вас в мою историю становления</b> — почему именно астрология стала моей профессией...</i><i><u>
</u>
В 2021 году, после сложного развода, я осталась одна с ребёнком на руках </i><i><b>и в бесконечном круговороте задавала себе вопросы:</b> «Почему так случилось?», «Могло ли быть иначе в моей жизни?» и «Что делать дальше?». Ответы на эти вопросы нашлись не сразу... 🪶

[ Не имея много свободного времени, но стремясь к развитию, </i><i><b>я начала точечно соприкасаться с эзотерикой</b> — она стала моим помощником и давала хоть какое-то понимание происходящего. ] 

Я перепробовала множество направлений: нумерологию, таро, но именно </i><i><b>в астрологии нашла ту самую точку опоры</b> 🌙</i>
""",
    """
<i>В январе 2023 года я прошла первое обучение по базовой западной астрологии по методу </i><i><b>«Формулы души».</b> 

К тому моменту у меня уже была растущая база клиентов, и я понимала </i><i><b>необходимость двигаться дальше</b> и не переставать вкладываться в себя. 

Поэтому в июле того же года приступила </i><i><b>ко второму обучению</b> — по натальной карте и прогностике 🪐

Углубившись в астрологию благодаря желанию изменить жизнь не только свою, но и своих клиентов, </i><i><b>я смогла:
</b>
<b><i>•</i></b> отточить профессионализм и найти свои «изюминки» в консультировании,
<b><i>•</i></b> начать браться за самые сложные жизненные ситуации и помогать людям решать их проблемы своими знаниями,
<b><i>•</i></b> расширить клиентскую базу свыше 250 человек и стать астрологом мирового уровня.

[ p.s. Мои клиенты находятся в России, Америке, ОАЭ, СНГ, Турции, странах Прибалтики и ещё в более чем десяти других государствах 🕊 ]</i>
""",
    """
<i>[ На сегодняшний день у меня несколько дипломов, подтверждающих квалификацию. ]

Особенно горжусь дипломом о профессиональной переподготовке и тем, </i><i><b>что являюсь выпускницей школы астрологии «Регул»</b> 🎓

Если вы, как когда-то я, </i><i><b>хотите:</b>

<b><i>•</i></b> понять себя и найти путь к своему «Я»,
<b><i>•</i></b> получить ответы на волнующие вас вопросы,
<b><i>•</i></b> узнать, в какой нише вы сможете реализоваться и стать финансово независимыми,
<b><i>•</i></b> разобраться в сферах отношений, карьеры и здоровья,

— то я с огромным удовольствием стану вашей </i><i><b>«верной»</b> путеводной звездой 💫</i>
""",
]


async def on_previous_page(c: CallbackQuery, b: Button, m: DialogManager):
    current = m.dialog_data.get("current_page", 0)
    m.dialog_data["current_page"] = current - 1
    await m.switch_to(AboutMeStates.main, show_mode=ShowMode.EDIT)


async def on_next_page(c: CallbackQuery, b: Button, m: DialogManager):
    current = m.dialog_data.get("current_page", 0)
    m.dialog_data["current_page"] = current + 1
    await m.switch_to(AboutMeStates.main, show_mode=ShowMode.EDIT)


async def about_me_getter(dialog_manager: DialogManager, **_):

    current_page = dialog_manager.dialog_data.get("current_page", 0)
    has_next_page = current_page < len(FULL_TEXT) - 1
    has_previous_page = current_page > 0
    if dialog_manager.dialog_data.get("about_me_photo") is None:
        about_me_photo = await get_pay_photo_attachment(
            dialog_manager.event.bot,
            str(
                Path(__file__).resolve().parent.parent
                / "misk"
                / "navigation"
                / "about.png"
            ),
        )
        dialog_manager.dialog_data["about_me_photo"] = about_me_photo
    else:
        about_me_photo = dialog_manager.dialog_data.get("about_me_photo")
    if dialog_manager.dialog_data.get("about_me_photo2") is None:
        about_me_photo2 = await get_pay_photo_attachment(
            dialog_manager.event.bot,
            str(
                Path(__file__).resolve().parent.parent
                / "misk"
                / "navigation"
                / "about2.png"
            ),
        )
        dialog_manager.dialog_data["about_me_photo2"] = about_me_photo2
    else:
        about_me_photo2 = dialog_manager.dialog_data.get("about_me_photo2")
    return {
        "full_text": FULL_TEXT[current_page],
        "has_next_page": has_next_page,
        "has_previous_page": has_previous_page,
        "about_me_photo": about_me_photo,
        "about_me_photo2": about_me_photo2,
    }


async def on_services(c: CallbackQuery, b: Button, m: DialogManager):
    # await m.start(ServicesStates.main, mode=StartMode.RESET_STACK)
    await m.switch_to(
        AboutMeStates.all_services, show_mode=ShowMode.DELETE_AND_SEND
    )
    # pass


async def on_service(c: CallbackQuery, b: Button, manager: DialogManager):
    # await m.start
    user_id = c.from_user.id
    user = await get_user(user_id)

    await manager.start(
        (
            PaymentStates.payment_choice
            if user.balance > 0
            else PaymentStates.payment
        ),
        data={
            "amount": await get_price_for_user(c.from_user.id, b.widget_id),
            "description": b.widget_id,
            "previous_state": AboutMeStates.all_services,
            "item_oficial_description": BASE_PRICES_RU_SHORT[b.widget_id],
            "extra_description": EXTRA_DESCRIPTIONS[b.widget_id],
        },
        show_mode=ShowMode.EDIT,
    )


about_me_dialog = Dialog(
    Window(
        DynamicMedia("about_me_photo", when="about_me_photo"),
        Format("""{full_text}"""),
        Row(
            Button(
                Format("<<"),
                id="previous_page",
                on_click=on_previous_page,
                when=F["has_previous_page"],
            ),
            Button(
                Format(">>"),
                id="next_page",
                on_click=on_next_page,
                when=F["has_next_page"],
            ),
        ),
        Url(
            Const("[ Читать меня в канале ]"),
            Const("https://t.me/bulgarovalife"),
            id="channel2",
        ),
        Button(
            Format("Мои услуги"),
            id="services",
            on_click=on_services,
            # when=F["has_previous_page"],
        ),
        Button(
            Format("<< Вернуться назад"),
            id="back",
            on_click=on_main_menu,
        ),
        state=AboutMeStates.main,
        getter=about_me_getter,
    ),
    Window(
        # DynamicMedia("about_me_photo", when="about_me_photo"),
        DynamicMedia("about_me_photo2", when="about_me_photo2"),
        Format(
            """<b><i>Здесь вы можете 
познакомиться с моими услугами и условиями работы</i></b> 🪶<i>

Прежде чем выбрать услугу, немного расскажу, как обычно проходит наше взаимодействие:

<b><i>•</i></b> вы делитесь своей ситуацией — я всегда рядом, чтобы помочь. Вся информация остаётся конфиденциальной,

<b><i>•</i></b> в процессе общения я могу задавать уточняющие вопросы — это помогает сделать разбор более точным и полезным именно для вас,

<b><i>•</i></b> для подготовки разбора мне понадобятся ваши данные: дата, время и место рождения — эти сведения необходимы для построения Натальной карты,

<b><i>•</i></b> мы заранее согласуем дату, когда разбор будет готов,

<b><i>•</i></b> готовый разбор вы получите в формате голосовых сообщений (дополнительно скриншот Натальной карты),

<b><i>•</i></b> вы сможете прослушать разбор в удобное для себя время.

→ Ниже вы найдёте кликабельные кнопки с моими услугами — переходите, чтобы ознакомиться с наполнением, сроками и стоимостью.

→ В кнопке </i><i><b>«Канал с отзывами» </b>— вы сможете увидеть обратную связь моих клиентов.</i>"""
        ),
        Row(
            Button(
                Format("«Один вопрос»"),
                id="one_question",
                on_click=on_service,
            ),
            Button(
                Format("«Соляр»"),
                id="solar_analysis",
                on_click=on_service,
            ),
        ),
        Row(
            Button(
                Format("«Финансовый разбор»"),
                id="financial_analysis",
                on_click=on_service,
            ),
        ),
        Button(
            Format("«Разбор Натальной карты»"),
            id="natal_chart_analysis",
            on_click=on_service,
        ),
        Url(
            Const("[ Канал с отзывами ]"),
            Const("https://t.me/bulgarova_astrolog_channel"),
        ),
        SwitchTo(
            Format("<< Вернуться назад"),
            id="back3",
            state=AboutMeStates.main,
            # on_click=on_main_menu,
        ),
        # Row(
        #     Button(Format("Услуга_5"), id="service_5", on_click=on_service),
        #     Button(Format("Услуга_6"), id="service_6", on_click=on_service),
        # ),
        getter=about_me_getter,
        state=AboutMeStates.all_services,
    ),
)
