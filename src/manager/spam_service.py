from aiogram import Bot
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config.config import get_config
from dialogs.states import format_price_and_balance

spam_types = {
    "24_before_end_of_test_period": {
        "message": """
<b><i>ОСТАЛОСЬ 24 ЧАСА — ВАШ ВЫБОР ИЗМЕНИТ ВСЁ</i></b> 🚀

<i>{name}, ваш пробный период завершается: через 24 часа доступ к сообществу закроется. </i><b><i>Если вы не оформите подписку:</i></b>

<i><b><b><i>•</i></b></b> Исчезнут инструменты, которые уже начали менять ваше мышление и энергию.
</i>
<i><b><b><i>•</i></b></b> Вы потеряете связь с единомышленниками, идущими к своей мечте.
</i>
<i><b><b><i>•</i></b></b> Мечты останутся мечтами — без среды, где они превращаются в цели.</i>

<b><i>Не отдаляйте свою лучшую жизнь</i></b> 💜

Жмите <b><i>«Продолжить»</i></b> — ваше место в сообществе сохранено до завтра!
        """,
        "photo_path": "src/misk/spam/2444.png",
        # "photo_path": None,
        "keyboard": [
            {
                "text": "> Продолжить <",
                "link": None,
                "callback_data": "continue_to_subscription",
            },
            {
                "text": "> Продолжить на 3 мес. <",
                "link": None,
                "callback_data": "continue_to_subscription_3",
            },
        ],
    },
    "end_of_test_period": {
        "message": """
<b><i>Ваш пробный период завершён — время усилить прорыв 🚀</i></b>

🧬 Вы уже почувствовали, как работа с мышлением и энергией меняет жизнь. <b><i>Но это только начало!</i></b> 

<u><i>Не останавливайтесь на полпути</i></u> — оформите подписку и сохраните доступ:

<i><b><b><i>•</i></b></b> К эксклюзивным практикам для здоровья и энергии.
</i>
<i><b><b><i>•</i></b></b> К ежедневной поддержке сообщества единомышленников.
</i>
<i><b><b><i>•</i></b></b> К инструментам, которые превращают мечты в реальность.
</i>
<i><b><b><i>•</i></b></b> К личным разборам и ответам на вопросы от Владилены.</i>

<u>Не дайте своим мечтам угаснуть</u> <i>— они достойны быть реальностью!
</i>
Жмите <b><i>«Оформить подписку»</i></b> и увидимся в закрытом сообществе 🫂
        """,
        "photo_path": "src/misk/spam/end_of_period.png",
        "keyboard": [
            {
                "text": "> Оформить подписку <",
                "link": None,
                "callback_data": "subscribe_payment",
            },
            {
                "text": "> Оформить подписку на 3 мес. <",
                "link": None,
                "callback_data": "subscribe_payment_3",
            },
        ],
    },
    "subscription_is_active": {
        "message": """
<i><b>Ваша подписка активна</b> — вы среди избранных</i> 💫<i> </i>

<i><b><b><i>•</i></b></b> Вы получите доступ к закрытым практикам, которые превращают мечты в результаты.
</i>
<i><b><b><i>•</i></b></b> Вы окружены поддержкой единомышленников, где каждый шаг — прорыв.
</i>
<i><b><b><i>•</i></b></b> Вы особенный: ваше упорство и регулярность создают ту самую жизнь, о которой другие только мечтают.</i>

Успейте использовать все возможности <b><i>до {date} </i></b>🧠
<i><b>Продолжайте развиваться</b> — подписка гарантирует, что ни одна</i> <i><u>дверь не закроется</u> перед вашими целями.</i>

Вы уже на пути к лучшей версии себя. <i><b>Не сбавляйте обороты</b> — мир ждёт вашего света!</i>

<b><i>{name}, вы значимы для нашего сообщества.</i></b> Спасибо, что развиваетесь вместе со мной 🌒
        """,
        "photo_path": "src/misk/spam/subscription_is_active.png",
    },
    "reminder_about_3_days_before_end_of_subscription": {
        "message": """
<i><b>Напоминание:</b> ваш эксклюзивный доступ продлится через 3 дня</i> 💫

<i>{name}, </i><i><b>вы — часть особого круга,</b> где счастье и изобилие создаются осознанно.</i> Через 3 дня мы автоматически продлим вашу подписку, чтобы вы могли продолжить:

<i><b><b><i>•</i></b></b> Расти среди единомышленников, меняющих реальность.
</i>
<i><b><b><i>•</i></b></b> Получать закрытые практики, превращающие мечты в доход, здоровье и гармонию.
</i>
<i><b><b><i>•</i></b></b> Инвестировать в себя — единственный актив, который гарантирует пожизненные дивиденды.</i>

<b><i>Не останавливайтесь!</i></b> Ваша подписка <i>— это не плата, а </i><i><u>ваш билет</u> в жизнь, где вы — </i><i><u>автор</u> своей реальности, а не жертва обстоятельств.
</i>
<i><b>Оплата в {price} рублей спишется автоматически,</b> ваше место в сообществе сохранено</i> — вы этого достойны 🪐

<i>p.s. Вы уже на пути к лучшей версии себя.</i><i><b> Не сворачивайте с дороги,</b> где каждое вложение в себя приумножается!</i>        
        """,
        "photo_path": "src/misk/spam/reminder_about_3_days_before_end_of_subscription.png",
    },
    "lazy_user_after_registration": {
        "message": """<i>{name}, ваша мечта ждёт </i><b><i>— начните пробный период прямо сейчас</i></b> 🚀

Привет! Вы зарегистрировались в нашем боте, <b><i>но так и не попробовали бесплатные практики,</i></b> которые уже изменили сотни жизней.<b><i> Почему?
</i></b>
<b><i>Вы упускаете шанс:</i></b>

<i><b><b><i>•</i></b></b> Убрать тревогу, обиды и переживания через энергетические медитации.
</i>
<i><b><b><i>•</i></b></b> Перепрограммировать мышление, чтобы желания стали целями.
</i>
<i><b><b><i>•</i></b></b> Улучшить и гармонизировать отношения или привлечь достойного партнёра.
</i>
<i><b><b><i>•</i></b></b> Увеличить финансовый поток и прийти к стабильности через работу с энергией и мышлением.
</i>
<i><b><b><i>•</i></b></b> Достичь состояния, когда энергии хватит на десятерых.
</i>
<i><b><b><i>•</i></b></b> Увидеть первые результаты уже через неделю — как и участники нашего сообщества.</i>

<b><i>Это бесплатно. Без риска. Но не вечно.</i></b> 
<i>Чем дольше ждёте </i><i><b>— тем дальше мечты!</b> </i>

Жмите <b><i>«Начать пробный период»</i></b> → Пока вы читаете это, другие уже запускают свою трансформацию 🌪️

<b><i>Присоединяйтесь ✨</i></b>
        """,
        "photo_path": "src/misk/spam/lazy_user_after_registration.png",
        # "repl": "https://t.me/yoga_club_bot?start=free_yoga_club_1234567890"
        "keyboard": [
            {
                "text": "> Начать пробный период <",
                "link": "chanel",
                "callback_data": None,
            }
        ],
    },
    "u_go_home_by_yourself": {
        "message": """
<i>Нам грустно прощаться, {name}…</i> 🫂

Вы покидаете закрытое сообщество, <b><i>но мы верим, что это не навсегда.</i></b> Возможно, вы уже ощутили первые изменения:

<i><b><b><i>•</i></b></b> Ясность мыслей...
</i>
<i><b><b><i>•</i></b></b> Проблески уверенности...
</i>
<i><b><b><i>•</i></b></b> Энергию, притягивающую возможности...</i>

Вы попробовали ритуалы и техники, которые дали первые результаты, <b><i>или только заложили намерение</i></b> 👁️

Мы видели ваш прогресс и искренне жаль терять вас. <i>Но у вас ещё 24 часа, чтобы вернуться </i><b><i>— дверь обратно открыта!</i></b>

<i>p.s. Помните: даже героям иногда нужна пауза. </i><b><i>Но настоящие герои возвращаются</i></b>⚡️
        """,
        "photo_path": "src/misk/spam/u_go_home.png",
    },
    "u_go_home": {
        "message": """
<i>Нам грустно прощаться, {name}…</i> 🫂

<i><b>Мы вынуждены были отключить вас</b> от нашего закрытого канала, но это не конец.</i> Вы стали частью истории сообщества, и мы <i><u>искренне ценим каждый ваш шаг</u></i> в работе над мышлением и энергией 💫

<b><i>Вы</i></b> <b><i>уже начали:</i></b>

<i><b><b><i>•</i></b></b> Менять привычные шаблоны мышления.
</i>
<i><b><b><i>•</i></b></b> Притягивать первые возможности к своим целям.
</i>
<i><b><b><i>•</i></b></b> Делиться энергией с теми, кто верит в перемены.</i>

<b><i>Мы верим, что это только начало.</i></b> К сожалению, правила сообщества строги <i>— доступ открыт только для активных подписчиков.</i> 

Однако мы будем ждать вас в следующий период продаж <i>(уже скоро 🚀), </i><b><i>чтобы вы смогли продолжить свой путь.</i>
</b>
<b><i>Хотите вернуться?</i></b>

Нажмите кнопку <b><i>«Напомнить о старте продаж»</i></b> — мы оповестим, когда двери откроются вновь 💜

Спасибо, что были с нами. <b><i>Вы — важная часть нашего сообщества,</i></b> и мы верим, что <u><i>ваше возвращение</i></u> станет новым витком вашей трансформации!
        """,
        "photo_path": "src/misk/spam/u_go_home_by_yourself.png",
        "keyboard": [
            {
                "text": "> Напомнить о старте продаж <",
                "link": None,
                "callback_data": "remind_about_start_of_sales",
            }
        ],
    },
    "12_hours_before_end_of_sales": {
        "message": """
<b><i>До конца продаж осталось 12 часов!</i></b>
<i>Старт вашей мечты — через 12 часов дверь захлопнется</i> 🌪️

<b><i>Что внутри:</i></b>

<i><b><b><i>•</i></b></b> Прямые эфиры, ответы на ваши вопросы, подкасты, техники, практики и медитации в самых популярных областях: деньги, отношения, здоровье, энергия, сексуальность, уверенность.</i>

<i><b><b><i>•</i></b></b> </i><i><b>Богатство:</b> система, которая увеличит ваши доходы и поможет найти дело мечты.
</i>
<i><b><b><i>•</i></b></b> </i><i><b>Энергия:</b> техники и практики, чтобы стать счастливее и энергичнее.
</i>
<i><b><b><i>•</i></b></b> </i><i><b>Отношения:</b> методики, вернувшие любовь и страсть сотням пар.
</i>
<i><b><b><i>•</i></b></b> </i><i><b>Свобода от тревог:</b> практики, перезагрузившие сознание для спокойствия и уверенности в себе.</i>

<i>Успейте войти → </i><b><i>завтра будет поздно</i></b>⚡️
        """,
        "photo_path": "src/misk/spam/12_hours_before_end_of_sales.png",
        "keyboard": [
            {
                "text": "> Оформить подписку <",
                "link": None,
                "callback_data": "subscribe_payment",
            },
            {
                "text": "> Оформить подписку на 3 мес. <",
                "link": None,
                "callback_data": "subscribe_payment_3",
            },
        ],
    },
    "6_hours_before_end_of_sales": {
        "message": """
<i><b>Запустите свою трансформацию!</b> </i>
<i>До окончания продаж осталось всего 6 часов</i> 🚀
""",
        "photo_path": "src/misk/spam/6_hours_before_end_of_sales.png",
        "keyboard": [
            {
                "text": "> Оформить подписку <",
                "link": None,
                "callback_data": "subscribe_payment",
            },
            {
                "text": "> Оформить подписку на 3 мес. <",
                "link": None,
                "callback_data": "subscribe_payment_3",
            },
        ],
    },
    "3_hours_before_end_of_sales": {
        "message": """
<i><b>До конца продаж осталось 3 часа!</b>
3 ЧАСА — И ВСЁ ИЗМЕНИТСЯ</i> 🧬

<b><i>Если вы не с нами:</i></b>

<i><b><b><i>•</i></b></b> Тревога продолжит красть вашу энергию.
</i>
<i><b><b><i>•</i></b></b> Мечты так и останутся в Instagram-сторис.
</i>
<i><b><b><i>•</i></b></b> Отношения будут «как у всех» — со ссорами, недоговорённостями и разочарованиями.</i>

Жмите <b><i>«Оформить подписку»</i></b> — мечта не ждёт 💜

""",
        "photo_path": "src/misk/spam/feedback_from_admin.png",
        "keyboard": [
            {
                "text": "> Оформить подписку <",
                "link": None,
                "callback_data": "subscribe_payment",
            },
            {
                "text": "> Оформить подписку на 3 мес. <",
                "link": None,
                "callback_data": "subscribe_payment_3",
            },
        ],
    },
    "1_hour_before_end_of_sales": {
        "message": """
<i><b>До конца продаж остался 1 час!</b>
60 МИНУТ ДО ТОЧКИ НЕВОЗВРАТА</i>⚡️

<b><i>Через час:</i></b>

<i><b>Или вы — в сообществе, где:</b>
</i>
<i><b><b><i>•</i></b></b> деньги приходят через осознанность, а не «халяву»;
</i><i><b><b><i>•</i></b></b> работа заряжает, а не выжимает;
</i><i><b><b><i>•</i></b></b> в отношениях — страсть и глубина.</i>

<i><b>Или вы — там, где:</b>
</i>
<i><b><b><i>•</i></b></b> мечты годами пылятся в голове;
</i><i><b><b><i>•</i></b></b> деньги утекают в чёрную дыру страхов;
</i><i><b><b><i>•</i></b></b> тонете в долгах и тревоге.</i>

<b><i>Выбирайте — дверь закрывается</i></b> ⭐️
<i>{name}, последний шанс — жмите!</i>

<i>p.s. Через час ваша жизнь разделится на «до» и «после». </i><b><i>Выбор за вами</i></b> <b><i>💜</i></b>
        """,
        "photo_path": "src/misk/spam/1_hour_before_end_of_sales.png",
        "keyboard": [
            {
                "text": "> Оформить подписку <",
                "link": None,
                "callback_data": "subscribe_payment",
            },
            {
                "text": "> Оформить подписку на 3 мес. <",
                "link": None,
                "callback_data": "subscribe_payment_3",
            },
        ],
    },
    "thanks_for_referral": {
        "message": """
<i>Спасибо за доверие! </i>
<i>Ваш</i> <i>друг присоединился, </i><i><b>и ваши баллы уже ждут</b> 🫂</i>

<i>Привет!

Вы помогли другу сделать шаг к гармонии и развитию — по вашей рекомендации он только что стал частью нашего сообщества</i>⚡️<i>

</i><b><i>Как использовать баллы?</i></b>
<i>
</i><i><b><b><i>•</i></b></b> Баланс бонусов: {balance} </i><b><i>— ваша личная валюта роста.</i></b>
<i>
</i><i><b><b><i>•</i></b></b> С каждого приглашённого друга вам начисляется </i><i><b>10% от стоимости</b> его подписки, которыми вы сможете </i><i><u>оплатить продление</u> в следующем месяце.</i>
<i>
</i><i><b><b><i>•</i></b></b> В знак благодарности на ваш счёт </i><b><i>зачислены баллы в количестве {balance}</i></b> 💫

<i>Делиться полезным — выгодно</i> 🚀

🌪️ <b><i>Продолжайте приглашать друзей,</i></b> которым важны счастливые отношения, здоровье и внутренний баланс. 

Спасибо, что вы с нами и помогаете другим на их пути! 
<b><i>Желаем вам ярких результатов</i></b> 💜""",
        "photo_path": "src/misk/spam/thanks_for_referral.png",
    },
    "subscription_is_extended": {
        "message": """
<b><i>Ваш путь к лучшей жизни продолжается 🚀</i></b>

<i><u>Продление подписки</u></i> <i>— самая важная инвестиция в себя.</i>

<b><i><b><i>•</i></b></i></b> <i>На вашем счёте сейчас </i><b><i>{balance} баллов.</i></b> 
<b><i>Списать их?</i></b>
        """,
        "photo_path": None,
    },
    "investment_in_yourself_is_almost_completed": {
        "message": """
<b><i>Инвестиция в себя почти завершена⚡️</i></b>

<i>Баллы списаны, остаток</i><i><b> — {balance} рублей!</b>
</i><i><b>Оплатите {price} рублей</b> — и продолжайте рост без перерывов</i> 🚀
""",
        "photo_path": None,
    },
    "investment_in_yourself_is_completed": {
        "message": """
<b><i>Инвестиция в себя завершена⚡️</i></b>

<i>Баллы списаны, остаток</i><i><b> — {balance} рублей!</b>
</i><i><b>Оплати {price} рублей</b> — и продолжай рост без перерывов</i> 🚀""",
        "photo_path": None,
    },
    "your_points_are_waiting_for_their_hour": {
        "message": """
<b><i>Ваши баллы ждут своего часа</i></b> 🚀

Сила накоплений растёт!<i> 
</i><i><b>Ваш резерв</b> — {points} баллов.</i>

<i>Приглашайте друзей в наше сообщество </i><b><i>и кратно ускоряйте рост накоплений</i></b> 🫂
        """,
        "photo_path": None,
        "keyboard": [
            {
                "text": "> Пригласить <",
                "link": None,
                "callback_data": "ask_friends_to_join",
            }
        ],
    },
    "24_before_sales": {
        "message": """  
<i><b>ТОЛЬКО 24 ЧАСА:</b> ваш билет в жизнь, где энергия и мышление работают на вас</i> 🌒

<i>{name}, окно доступа к сообществу уже открыто — это пространство, где наука органично сочетается с практиками управления энергией и законов Вселенной. 
</i><b><i>Это система, которая уже изменила жизни тысяч людей 🫂</i></b>

⚡️<b><i>Почему это ваш шанс?</i></b>

<b><i>Эксклюзивные методики на стыке психологии и энергетических практик:</i></b>

<i><b><b><i>•</i></b></b> Перепрограммируйте мышление.

</i><i><b><b><i>•</i></b></b> Устраните ментальные блоки, крадущие ваши деньги и уверенность.

</i><i><b><b><i>•</i></b></b> Научитесь направлять энергию так, чтобы цели достигались вдвое быстрее, а отношения, здоровье и доход радовали вас.</i>

<b><i>Но окно закроется через 24 часа.</i></b> 
Мы не продаём подписку каждый день <i>— доступ получат только те, </i><b><i>кто готов действовать здесь и сейчас</i></b> 🚀

Через сутки дверь закроется <b><i>— следующего шанса может не быть</i></b> 💜

<i>p.s. Это не </i><i><b>«просто подписка»</b>, это точка, где ваши решения становятся результатами.</i>
""",
        "photo_path": "src/misk/spam/24_before_sales.png",
        "keyboard": [
            {
                "text": "> Оформить подписку <",
                "link": None,
                "callback_data": "subscribe_payment",
            },
            {
                "text": "> Оформить подписку на 3 мес. <",
                "link": None,
                "callback_data": "subscribe_payment_3",
            },
        ],
    },
}


class SpamManager:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_spam_message(
        self,
        user_id: int,
        message: str = None,
        with_photo: bool = False,
        photo_path: str = None,
        photo_id: str = None,
        keyboard: InlineKeyboardMarkup = None,
        name: str = None,
        points: int = None,
        type_of_spam: str = None,
        **kwargs,
    ):
        if type_of_spam:
            config = get_config()
            channel_manager = config.get_channel_manager()
            message = spam_types.get(type_of_spam)["message"]
            photo_path = spam_types.get(type_of_spam)["photo_path"]
            keyboard = spam_types.get(type_of_spam).get("keyboard")
            if photo_path:
                with_photo = True
            if keyboard:
                all_keyboard = []
                for item in keyboard:
                    if item["link"] == "chanel":
                        url = (
                            await channel_manager.create_welcome_link_whit_admin_approval()
                        )

                        all_keyboard.append(
                            # [
                            [
                                InlineKeyboardButton(
                                    text=item["text"],
                                    url=url,
                                    callback_data=item["callback_data"],
                                )
                            ]
                            # ],
                        )
                    else:
                        # keyboard = InlineKeyboardMarkup(
                        all_keyboard.append(
                            # [
                            [
                                InlineKeyboardButton(
                                    text=item["text"],
                                    url=item["link"],
                                    callback_data=item["callback_data"],
                                )
                            ]
                            # ]
                        )
                    # )
                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=all_keyboard
                    )
            elif type_of_spam == "subscription_is_extended":
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Да",
                                callback_data="subscription_is_extended_yes",
                            ),
                            InlineKeyboardButton(
                                text="Нет",
                                callback_data="subscription_is_extended_no",
                            ),
                        ]
                        # [
                        # ],
                    ]
                )

        # Форматируем сообщение
        if kwargs.get("price"):
            kwargs["price"] = format_price_and_balance(kwargs["price"])
        if kwargs.get("balance"):
            kwargs["balance"] = format_price_and_balance(kwargs["balance"])
        if points:
            points = format_price_and_balance(points)

        if message:
            formatted_message = message.format(
                name=name or "Избранный", points=points or 0, **kwargs
            )
        else:
            formatted_message = ""

        if with_photo:
            # Обрезаем сообщение до 1024 символов для caption
            # if len(formatted_message) > 1024:
            #     formatted_message = formatted_message[:1021] + "..."

            if photo_path:
                try:
                    # Используем FSInputFile для отправки файла
                    print("TYPE OF SPAM", type_of_spam)
                    photo = FSInputFile(photo_path)
                    await self.bot.send_photo(
                        user_id,
                        photo=photo,
                        caption=formatted_message,
                        reply_markup=keyboard,
                    )
                except FileNotFoundError:
                    # Если файл не найден, отправляем только текст
                    await self.bot.send_message(
                        user_id,
                        formatted_message,
                        reply_markup=keyboard,
                    )
            elif photo_id:
                await self.bot.send_photo(
                    user_id,
                    photo=photo_id,
                    caption=formatted_message,
                    reply_markup=keyboard,
                )
            else:
                raise ValueError("photo_path or photo_id must be provided")
        else:
            # Для обычных сообщений лимит 4096 символов
            if len(formatted_message) > 4096:
                # Разбиваем на части
                for i in range(0, len(formatted_message), 4096):
                    await self.bot.send_message(
                        user_id,
                        formatted_message[i : i + 4096],
                        reply_markup=(
                            keyboard
                            if i + 4096 >= len(formatted_message)
                            else None
                        ),
                    )
            else:
                await self.bot.send_message(
                    user_id,
                    formatted_message,
                    reply_markup=keyboard,
                )
