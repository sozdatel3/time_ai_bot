from sqlalchemy import Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin

BASE_PRICES = {
    # "subscription_start": 2490,
    # "subscription_start_3": 6990,
    # "subscription_long": 2490,
    "ai_prediction": 300,
    "one_question": 1000,
    "financial_analysis": 1000,
    "natal_chart_analysis": 1000,
    "solar_analysis": 10000,
}

BASE_PRICES_RU = {
    # "subscription_start": "«Первичная подписка»",
    # "subscription_start_3": "«Первичная подписка на 3 месяца»",
    # "subscription_long": "«Продление подписки»",
    "unknown": "Неизвестная услуга",
    "ai_prediction": "АI-прогноз",
    "one_question": "Один вопрос",
    "financial_analysis": "Финансовый разбор",
    "natal_chart_analysis": "Разбор Натальной карты",
    "solar_analysis": "Соляр",
}

BASE_PRICES_RU_SHORT = {
    # "subscription_start": "Первичная подписка",
    # "subscription_start_3": "Первичная подписка на 3 месяца",
    # "subscription_long": "Продление подписки",
    "unknown": "Неизвестная услуга",
    "ai_prediction": "АI-прогноз",
    "one_question": "Один вопрос",
    "financial_analysis": "Финансовый разбор",
    "natal_chart_analysis": "Разбор Натальной карты",
    "solar_analysis": "Соляр",
}

EXTRA_DESCRIPTIONS = {
    "one_question": """
<b><i>Услуга «Один вопрос» 🪐</i></b>

<i>Что входит:

<b><i>•</i></b> рассмотрение любой сферы жизни,
<b><i>•</i></b> разбор вашей ситуации,
<b><i>•</i></b> подсказки и рекомендации,
<b><i>•</i></b> определение временного периода событий.

</i><i><b>Срок выполнения</b> — в течение 24 часов с момента оплаты.

Важные условия:</i>

<i><b><i>•</i></b> в случае экстренной ситуации в выходной день стоимость услуги увеличивается на 50%,
<b><i>•</i></b> любую услугу можно оформить в рассрочку до 6 месяцев без переплат.</i>

<i>Для уточнения деталей — пишите в личные сообщения</i> 🌙

<i>△ Стоимость — {price} рублей. </i>""",
    "financial_analysis": """
<b><i>Услуга «Финансовый разбор» 🪐</i></b>

<i>Что входит:

<b><i>•</i></b> рассмотрение финансовых показателей в Натальной карте,
<b><i>•</i></b> ответ на главный вопрос:
«Чем мне заниматься/где работать, чтобы были деньги?»,
<b><i>•</i></b> персональные подсказки и рекомендации.

</i><i><b>Срок выполнения</b> — в течение 3 дней с момента оплаты.

Важные условия:</i>

<i><b><i>•</i></b> в случае экстренной ситуации в выходной день стоимость услуги увеличивается на 50%,
<b><i>•</i></b> любую услугу можно оформить в рассрочку до 6 месяцев без переплат.</i>

<i>Для уточнения деталей — пишите в личные сообщения</i> 🌙

<i>△ Стоимость — {price} рублей. </i>""",
    "natal_chart_analysis": """
<b><i>Услуга «Разбор Натальной карты» 🪐</i></b>

<i>Что входит:

<b><i>•</i></b> подробный разбор 12 сфер жизни,
<b><i>•</i></b> углублённое рассмотрение волнующих именно вас сфер,
<b><i>•</i></b> компенсаторика негативных показателей,
<b><i>•</i></b> персональные подсказки и рекомендации.

</i><i><b>Срок выполнения</b> — в течение 5</i>-<i>7 дней с момента оплаты.

Важные условия:</i>

<i><b><i>•</i></b> в случае экстренной ситуации в выходной день стоимость услуги увеличивается на 50%,
<b><i>•</i></b> любую услугу можно оформить в рассрочку до 6 месяцев без переплат.</i>

<i>Для уточнения деталей — пишите в личные сообщения</i> 🌙

<i>△ Стоимость — {price} рублей. </i>""",
    "solar_analysis": """
<b><i>Услуга «Соляр» (личный годовой прогноз) 🪐</i></b>

<i>Что входит:

<b><i>•</i></b> прогнозирование событий личного года,
<b><i>•</i></b> указание на временные периоды,
<b><i>•</i></b> указание на возможные риски и сложности,
<b><i>•</i></b> персональные подсказки и рекомендации.

</i><i><b>Срок выполнения</b> — в течение 10-14 дней с момента оплаты.

Важные условия:</i>

<i><b><i>•</i></b> в случае экстренной ситуации в выходной день стоимость услуги увеличивается на 50%,
<b><i>•</i></b> любую услугу можно оформить в рассрочку до 6 месяцев без переплат.</i>

<i>Для уточнения деталей — пишите в личные сообщения</i> 🌙

<i>△ Стоимость — {price} рублей. </i>""",
}


class Price(Base, TimestampMixin):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    amount: Mapped[int] = mapped_column(Integer)


async def get_price(
    service_name: str, session: AsyncSession | None = None
) -> int:
    if session is None:
        async with AsyncSessionLocal() as session:
            query = select(Price).where(Price.name == service_name)
            result = await session.execute(query)
            price = result.scalar_one_or_none()

            if price is None:
                return BASE_PRICES[service_name]

            return price.amount
    else:
        query = select(Price).where(Price.name == service_name)
        result = await session.execute(query)
        price = result.scalar_one_or_none()

        if price is None:
            return BASE_PRICES[service_name]
        return price.amount


async def set_price(service_name: str, amount: int) -> None:
    async with AsyncSessionLocal() as session:
        query = select(Price).where(Price.name == service_name)
        result = await session.execute(query)
        price = result.scalar_one_or_none()

        if price is None:
            price = Price(name=service_name, amount=amount)
            session.add(price)
        else:
            price.amount = amount

        await session.commit()
