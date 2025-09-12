import contextlib

from aiogram import Bot
from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const

from config.config import load_config
from db.models.old_workflow.question import (
    answer_question,
    create_question,
    get_question,
)
from dialogs.states import AskQuestionStates, YogaClubStates

ADMIN_IDS = load_config().admin_ids


async def ask_question_handler(c, button, manager):
    # await c.answer(
    #     "Пожалуйста, отправьте ваш вопрос по услугам либо оставьте обратную связь в любом удобном формате (текст, голосовое сообщение и т.д.)"
    # )
    await manager.start(AskQuestionStates.waiting_for_question)


async def process_question(
    message: Message, widget, dialog_manager: DialogManager
):
    user_id = message.from_user.id
    bot = dialog_manager.middleware_data["bot"]

    question = await create_question(user_id, str(message.message_id))

    for admin_id in ADMIN_IDS:
        with contextlib.suppress(Exception):
            forwarded = await bot.forward_message(
                admin_id, user_id, message.message_id
            )
            await bot.send_message(
                admin_id,
                f"Вопрос ID: {question.id}. Для ответа ответьте на это сообщение при помощи (Reply).",
                reply_to_message_id=forwarded.message_id,
            )
    # await message.answer(
    #     "<i>Ваш вопрос получен! Ответ будет направлен в ближайшее время</i> 💜"
    # )
    try:
        await message.delete()
    except Exception as e:
        print(e)
    await dialog_manager.switch_to(
        AskQuestionStates.waiting_for_question_thanks,
        show_mode=ShowMode.DELETE_AND_SEND,
    )


async def admin_reply(message: Message, bot: Bot):
    if message.from_user.id not in ADMIN_IDS or not message.reply_to_message:
        return
        # print("MEEEES\n", message)
    with contextlib.suppress(Exception):
        question_id = int(message.reply_to_message.text.split()[2].rstrip("."))

        question = await get_question(question_id)
        if question:
            user_id = question.user_id

            await answer_question(question_id, str(message.message_id))

            await bot.send_message(
                user_id,
                "<i>Ответ на ваш вопрос направлен ниже, в следующем сообщении 🕊</i>",
            )
            # await bot.forward_message(
            #     user_id, message.chat.id, message.message_id
            # )
            await bot.copy_message(
                user_id,
                message.chat.id,
                message.message_id,
                protect_content=True,
            )


ask_question_dialog = Dialog(
    Window(
        Const(
            # "Напиши любой вопрос, который тебя интересует👇🏻 Я отвечу на него в течение дня!"
            """<i>Здесь вы можете </i><i><b>обратиться к Инне с любыми вопросами</b> об её услугах, уточнить детали проекта и оплаты, а также оставить отзыв</i> 🕊<i>
</i>
<i>Ваша обратная связь вдохновляет нас расти и совершенствоваться </i>
<b><i>— это бесценно</i></b> 🪄
            """
        ),
        MessageInput(process_question),
        Button(
            Const("<< Вернуться назад"),
            id="cancel",
            on_click=lambda c, b, m: m.start(
                YogaClubStates.main, mode=StartMode.RESET_STACK
            ),
        ),
        state=AskQuestionStates.waiting_for_question,
    ),
    Window(
        Const(
            """<i>Ваш вопрос получен — ответ будет направлен в ближайшее время 🕊</i>"""
        ),
        Button(
            Const("<< Вернуться в главное меню"),
            id="cancel",
            on_click=lambda c, b, m: m.start(
                YogaClubStates.main,
                mode=StartMode.RESET_STACK,
                show_mode=ShowMode.DELETE_AND_SEND,
            ),
        ),
        state=AskQuestionStates.waiting_for_question_thanks,
    ),
)
