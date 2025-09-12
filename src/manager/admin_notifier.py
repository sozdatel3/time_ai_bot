from typing import Dict

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config.config import Config
from db.models.user import get_user, get_user_created_at


class AdminNotifier:
    """Сервис для отправки уведомлений администраторам"""

    def __init__(self, bot: Bot, config: Config):
        self.bot = bot
        self.admin_ids = config.admin_ids
        self.chat_admin_ids = config.chat_admin_ids

    async def _send_to_admins(self, message: str) -> None:
        """Отправка сообщения всем администраторам"""
        for admin_id in self.chat_admin_ids:
            try:
                await self.bot.send_message(
                    chat_id=admin_id, text=message, parse_mode="HTML"
                )
            except TelegramAPIError as e:
                print(f"Ошибка при отправке уведомления админу: {e}")

    async def _get_user_info(self, user_id: int) -> Dict[str, str]:
        """Получение информации о пользователе"""
        user = await get_user(user_id)
        username = (
            user.username if user and user.username else f"user_{user_id}"
        )
        registration_date = (
            await get_user_created_at(user_id) if user else None
        )

        return {
            "username": username,
            "registration_date": registration_date or "Неизвестно",
        }

    async def notify_payment_attempt(
        self, username: str, amount: float
    ) -> None:
        """Уведомление о попытке списания средств"""
        message = f"""Попытка списания {amount} рублей у пользователя @{username}. Сообщу, если операция пройдет успешно!"""
        await self._send_to_admins(message)

    async def notify_subscription_purchase(
        self, username: str, amount: float, registration_date: str
    ) -> None:
        """Уведомление о покупке подписки"""
        message = f"""Пользователь @{username} оформил подписку на сумму {amount} рублей. Дата регистрации — {registration_date}."""
        await self._send_to_admins(message)

    async def notify_subscription_renewal(
        self,
        username: str,
        amount: float,
        registration_date: str,
        join_date: str,
        months_count: int,
    ) -> None:
        """Уведомление об успешном продлении подписки"""
        message = f"""Пользователь @{username} продлил подписку за {amount} рублей, дата регистрации в боте — {registration_date}, дата присоединения к сообществу {join_date}, он с нами уже {months_count} месяцев подряд!"""
        await self._send_to_admins(message)

    async def notify_user_removal(
        self,
        username: str,
        registration_date: str,
        join_date: str,
        months_count: int,
    ) -> None:
        """Уведомление об исключении пользователя из канала"""
        message = f"""Пользователь @{username} был удалён из сообщества в связи с неуплатой (отмена подписки).

Дата регистрации в боте — {registration_date}.

Дата присоединения к сообществу — {join_date}.

Пользователь находился в сообществе на протяжении {months_count} месяцев подряд."""
        await self._send_to_admins(message)

    async def notify_referral_subscription(
        self,
        username: str,
        referrer_username: str,
        amount: float,
        registration_date: str,
    ) -> None:
        """Уведомление об оформлении подписки через реферальную систему"""
        message = f"""Пользователь @{username} оформил подписку на сумму {amount} рублей от пользователя @{referrer_username}. Дата регистрации — {registration_date}."""
        await self._send_to_admins(message)

    # Удобные методы для работы с user_id вместо username
    async def notify_payment_attempt_by_id(
        self, user_id: int, amount: float
    ) -> None:
        """Уведомление о попытке списания средств по ID пользователя"""
        user_info = await self._get_user_info(user_id)
        await self.notify_payment_attempt(user_info["username"], amount)

    async def notify_subscription_purchase_by_id(
        self, user_id: int, amount: float
    ) -> None:
        """Уведомление о покупке подписки по ID пользователя"""
        user_info = await self._get_user_info(user_id)
        await self.notify_subscription_purchase(
            user_info["username"], amount, user_info["registration_date"]
        )

    async def notify_referral_subscription_by_id(
        self, user_id: int, referrer_id: int, amount: float
    ) -> None:
        """Уведомление о реферальной подписке по ID пользователей"""
        user_info = await self._get_user_info(user_id)
        referrer_info = await self._get_user_info(referrer_id)
        await self.notify_referral_subscription(
            user_info["username"],
            referrer_info["username"],
            amount,
            user_info["registration_date"],
        )


# <b>Уведомления для админа:</b>

# Попытка списания X рублей у пользователя @souldevchat. Сообщу, если операция пройдет успешно!

# <b>При покупке подписки:</b>

# Пользователь @souldevchat оформил подписку на сумму X рублей. Дата регистрации — 08.04.1999.

# <b>При успешном продлении:
# </b>
# Пользователь @souldevchat продлил подписку за X рублей, дата регистрации в боте — 08.04.1999, дата присоединения к сообществу XX.XX.XXXX, он с нами уже X месяцев подряд!

# <b>При исключении из канала:</b>

# Пользователь @souldevchat был удалён из сообщества в связи с неуплатой (отмена подписки).

# Дата регистрации в боте — 08.04.1999.

# Дата присоединения к сообществу — XX.XX.XXXX.

# Пользователь находился в сообществе на протяжении X месяцев подряд.


# <b>При оформлении подписки через реферальную  систему:</b>

# Пользователь @souldevchat оформил подписку на сумму X рублей от пользователя @N. Дата регистрации — 08.04.1999.
