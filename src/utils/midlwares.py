from aiogram import Bot, Dispatcher
from aiogram.types import ErrorEvent
from aiogram_dialog import ShowMode, StartMode
from aiogram_dialog.api.exceptions import UnknownIntent

from db.models.user import get_user_language
from dialogs.states import YogaClubStates


def get_error_handler(dp: Dispatcher, bot: Bot):
    async def error_handler(error: ErrorEvent, dialog_manager=None) -> bool:
        """Обработчик ошибок"""
        if isinstance(error.exception, UnknownIntent):
            callback = error.update.callback_query
            if callback:

                # Сначала отвечаем на callback query
                # print(callback.from_user.id)
                user_id = callback.from_user.id
                await callback.answer(
                    "Произошла ошибка. Вы будете перенаправлены в главное меню.",
                    show_alert=False,
                )
                try:
                    await callback.message.delete()
                except:
                    pass

                if not await get_user_language(user_id):
                    await dialog_manager.start(
                        # YogaClubStates.name,
                        YogaClubStates.choose_language,
                        mode=StartMode.RESET_STACK,
                        show_mode=ShowMode.DELETE_AND_SEND,
                        data={
                            "user_id": user_id,
                            "full_name": callback.from_user.full_name,
                            "username": callback.from_user.username,
                        },
                    )
                else:
                    await dialog_manager.start(
                        YogaClubStates.main,
                        mode=StartMode.RESET_STACK,
                        show_mode=ShowMode.DELETE_AND_SEND,
                        data={
                            "user_id": user_id,
                            "full_name": callback.from_user.full_name,
                            "username": callback.from_user.username,
                        },
                    )
                return True
        return False

    return error_handler
