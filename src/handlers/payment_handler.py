from aiogram import Bot
from aiogram.types import (
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from config.config import get_config, load_config
from db.models.old_workflow.certificate import get_certificate
from db.models.order import Order, update_order_status
from db.models.price import BASE_PRICES_RU
from db.models.user import (
    get_user,
    get_user_created_at,
    increase_free_predictions_count,
    update_user_balance_to_use_this_month,
    update_user_frozen_balance,
)

config = load_config()


class PaymentHandler:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def handle_payment(self, order: Order):
        # if order.status == "completed":
        config = get_config()
        # spam_manager = config.get_spam_manager()
        user = await get_user(order.user_id)
        try:
            await update_user_balance_to_use_this_month(order.user_id, 0)
        except Exception as e:
            print(e)
        try:
            created_at = await get_user_created_at(order.user_id)
        except Exception:
            created_at = None

        # if user.refer_id:
        #     try:
        #         refer_user = await get_user(user.refer_id)
        #         await update_user_balance(
        #             user.refer_id,
        #             refer_user.balance + (order.amount * 0.1),
        #         )
        #         refer_user = await get_user(user.refer_id)
        #         # await spam_manager.send_spam_message(
        #         #     user.refer_id,
        #         #     type_of_spam="thanks_for_referral",
        #         #     name=refer_user.name,
        #         #     balance=refer_user.balance,
        #         # )
        #     except Exception as e:
        #         print(e)
        if order.product in BASE_PRICES_RU:
            buy = f"{BASE_PRICES_RU[order.product]}"
        elif order.product.startswith("custom_payment_link:"):
            buy = "Платежная ссылка"
            for admin_id in config.admin_ids:
                try:
                    await self.bot.send_message(
                        admin_id,
                        f"""
🪄<i> Кто-то приобрёл продукт «{buy}» на сумму {order.amount} рублей.</i>
                """,
                    )
                except Exception as e:
                    print(e)
            await update_order_status(order.id, "completed")
            return

        else:
            buy = f"{order.product}"
        # sum_display = f'{order.amount:,}.replace(",", " ")}'
        sum_display = f"{order.amount:,}".replace(",", " ")
        for admin_id in config.admin_ids:
            try:
                await self.bot.send_message(
                    admin_id,
                    f"""
🪄<i> Пользователь @{user.username} приобрёл продукт «{buy}» на сумму {sum_display} рублей.
</i><i><b>Дата регистрации пользователя:</b> {created_at}</i>
                """,
                )
            except Exception as e:
                print(e)

        await update_order_status(order.id, "completed")
        try:
            await update_user_frozen_balance(
                order.user_id, order.balance_to_use
            )
        except Exception as e:
            print(e)
        # if order.product == "certificate":
        #     await self._handle_certificate_payment(order)
        # if (
        #     order.product == "subscription_start"
        #     or order.product == "subscription"
        # ):
        #     await self._handle_yoga_club_payment(order)
        # elif order.game_id < 0:
        #     await self._handle_brief_payment(order)

        if order.product == "ai_prediction":
            await self._handle_ai_payment(order)
        else:
            await self._handle_default_payment(order)

    async def _handle_certificate_payment(self, order: Order):
        certificate = await get_certificate(order.game_id)
        if certificate:
            # Send certificate image first
            await self.bot.send_photo(
                order.user_id,
                photo=FSInputFile("src/misk/sertificate.PNG"),
                caption=f"Спасибо за покупку сертификата!\n\nНе переходи по этой ссылке - перешли это сообщение получателю и он получит сууму сертификата на баланс! Вот <a href='{certificate.url}'>ссылка для активации</a>",
            )
        else:
            print(f"Ошибка: сертификат с id {order.game_id} не найден")

    async def _handle_brief_payment(self, order: Order):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Перейти к брифу",
                        callback_data=f"shitbrief:{order.id}",
                    )
                ]
            ]
        )
        await self.bot.send_message(
            order.user_id,
            "Спасибо за доверие! Теперь давайте заполним бриф, чтобы я могла лучше понять ваши потребности.",
            reply_markup=keyboard,
        )

    async def _handle_ai_payment(self, order: Order):
        # await self.bot.send_message(
        #     order.user_id,
        #     f"Получена оплата для заказа №{order.id}. Спасибо за покупку!",
        # )
        await increase_free_predictions_count(order.user_id)
        await self.bot.send_message(
            order.user_id,
            """<i>Благодарим вас за покупку и за оказанное доверие 🪶</i>
<i>
[</i> <i>Пожалуйста, вернитесь в раздел </i><i><b>«AI-прогноз»</b> и задайте вопрос заново.</i> <i>]</i>""",
        )

    async def _handle_default_payment(self, order: Order):
        # await self.bot.send_message(
        #     order.user_id,
        #     f"Получена оплата для заказа №{order.id}. Спасибо за покупку!",
        # )
        await self.bot.send_message(
            order.user_id,
            """<i>Благодарим вас за покупку и за оказанное доверие 🪶</i>
<i>
</i>[ <i>Пожалуйста, свяжитесь с Инной в личных сообщениях для получения услуги: </i><i>@bulgarova_astrolog</i><i> ]</i>""",
            parse_mode="HTML",
        )

    async def _handle_yoga_club_payment(self, order: Order):
        await self.bot.send_photo(
            order.user_id,
            photo=FSInputFile("src/misk/spam/subscription_is_active.png"),
            caption="""
<b><i>Добро пожаловать в круг избранных 🫂</i></b>

Ваша подписка <u>активирована</u> <i>— теперь вы часть сообщества, где мечты становятся реальностью.</i> <i>Вы только что </i><i><b>открыли дверь</b> в мир, где:</i>

<i><b><b><i>•</i></b></b> Ваша энергия и цели — наш главный фокус.
</i>
<i><b><b><i>•</i></b></b> Эксклюзивные практики работают на ваше изобилие, здоровье и счастье.
</i>
<i><b><b><i>•</i></b></b> Единомышленники поддерживают каждый ваш шаг к идеальной жизни.</i>

<i><b>Вы не просто приобрели доступ</b> — вы </i><i><u>инвестировали</u> в версию себя, которая не ждёт, а создаёт</i> 🧠

Теперь вы ближе к своей мечте, чем когда-либо. <i><b>Не останавливайтесь</b> — вы этого достойны!</i>
            """,
        )
