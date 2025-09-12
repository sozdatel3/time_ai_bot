from aiogram import Dispatcher, F

from config.config import get_config
from dialogs.about_me import about_me_dialog
from dialogs.admin.statistic import statistic_dialog
from dialogs.ask_question import (
    admin_reply,
    ask_question_dialog,
)
from dialogs.astro import astro_dialog
from dialogs.certificates import certificates_dialog
from dialogs.main_menu import yoga_club_dialog
from dialogs.payment import payment_dialog
from dialogs.refer_program import referral_program_dialog
from handlers.start import router as start_router

from .admin.admin_dialog import admin_dialog


def register_dialogs(dp: Dispatcher):
    config = get_config()
    dp.include_router(start_router)

    dp.include_router(ask_question_dialog)
    dp.include_router(astro_dialog)
    dp.include_router(about_me_dialog)
    dp.include_router(certificates_dialog)
    dp.include_router(payment_dialog)

    dp.include_router(admin_dialog)
    dp.include_router(statistic_dialog)

    dp.include_router(yoga_club_dialog)

    dp.include_router(referral_program_dialog)
    dp.message.register(admin_reply, F.reply_to_message)
    dp.message.register(
        admin_reply, lambda message: message.reply_to_message is not None
    )
