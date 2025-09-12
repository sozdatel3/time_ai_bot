import asyncio
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    Message,
)
from aiogram_dialog import DialogManager, ShowMode, StartMode

from config.config import get_config
from db.models.first_mes import try_to_del_and_add_new_first_mes
from db.models.old_workflow.links import increment_link_clicks
from db.models.old_workflow.price_for_group import get_price_for_user
from db.models.user import (
    create_user,
    do_we_know_user_language,
    get_all_user_ids,
    get_name,
    get_user,
    update_user_refer_id,
)
from dialogs.states import (
    AboutMeStates,
    YogaClubStates,
)

router = Router()


@router.message(CommandStart(deep_link=True))
async def handle_deep_link(message: Message, dialog_manager: DialogManager):
    deep_link = message.text.split()[1]
    existing_user = await get_user(message.from_user.id)
    user = await create_user(message.from_user.id, message.from_user.username)

    if deep_link.startswith("link_"):
        link_code = deep_link.split("_")[1]
        await increment_link_clicks(link_code)
        await start_or_birth_date(message, dialog_manager)
        return
    elif deep_link.startswith("refer_"):
        ref_id = deep_link.split("_")[1]
        print("inside refer_", ref_id)
        if message.from_user.id != int(ref_id):
            await update_user_refer_id(
                message.from_user.id, int(ref_id) if ref_id.isdigit() else 1
            )

        await start_or_birth_date(message, dialog_manager)
        return
    else:
        await message.answer("Неверная команда.")

    await start_or_birth_date(message, dialog_manager, None)


@router.message(CommandStart())
async def command_start(message: Message, dialog_manager: DialogManager):
    try:
        await try_to_del_and_add_new_first_mes(
            message.bot, message.from_user.id, message.message_id
        )
    except Exception as e:
        print(f"Error in command_start trying to delete/add first mes: {e}")
    await create_user(message.from_user.id, message.from_user.username)

    await start_or_birth_date(message, dialog_manager)


async def delete_messages(bot: Bot, message_ids: list[int], chat_id: int):
    if message_ids:
        for mes in message_ids:
            try:
                await bot.delete_message(chat_id, mes.message_id)
            except Exception as e:
                print(
                    f"Error deleting message {mes.message_id} in chat {chat_id}: {e}"
                )
                print(
                    "ERROR DELETING EDUCATION MESSAGE (in delete_messages func)"
                )


async def start_or_birth_date(
    message: Message,
    dialog_manager: DialogManager,
    mes_to_del2: Message | None = None,
):
    try:
        mes_to_del = dialog_manager.dialog_data.get("mes_to_del")
        another_mes_to_del = dialog_manager.dialog_data.get("messages_to_del")
        asyncio.create_task(
            delete_messages(
                message.bot,
                mes_to_del,
                message.from_user.id,
            )
        )
        asyncio.create_task(
            delete_messages(
                message.bot,
                another_mes_to_del,
                message.from_user.id,
            )
        )
    except:
        pass
    if not await do_we_know_user_language(message.from_user.id):
        await dialog_manager.start(
            YogaClubStates.choose_language,
            mode=StartMode.RESET_STACK,
            show_mode=ShowMode.DELETE_AND_SEND,
            data={"mes_to_del": mes_to_del2},
        )
    else:
        await dialog_manager.start(
            YogaClubStates.main,
            mode=StartMode.RESET_STACK,
            show_mode=ShowMode.DELETE_AND_SEND,
            data={"mes_to_del": mes_to_del2},
        )


async def delete_messages_from_callback(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    mes: Message | None = None,
):
    try:
        if mes:
            await mes.delete()
        else:
            await callback.message.delete()
    except:
        pass
    try:
        mes_to_del = dialog_manager.dialog_data.get("mes_to_del")
        another_mes_to_del = dialog_manager.dialog_data.get("messages_to_del")
        if mes_to_del:
            asyncio.create_task(
                delete_messages(
                    mes.bot,
                    mes_to_del,
                    mes.chat.id,
                )
            )
        else:
            asyncio.create_task(
                delete_messages(
                    callback.message.bot,
                    mes_to_del,
                    callback.message.chat.id,
                )
            )
        if mes:
            asyncio.create_task(
                delete_messages(
                    mes.bot,
                    another_mes_to_del,
                    mes.chat.id,
                )
            )
        else:
            asyncio.create_task(
                delete_messages(
                    callback.message.bot,
                    another_mes_to_del,
                    callback.message.chat.id,
                )
            )
    except:
        pass


@router.callback_query(F.data == "main_menu")
async def handle_main_menu(
    callback: CallbackQuery, dialog_manager: DialogManager
):
    await callback.answer()
    await delete_messages_from_callback(callback, dialog_manager)

    await start_or_birth_date(callback.message, dialog_manager)


@router.message(Command("services"))
async def handle_services(message: Message, dialog_manager: DialogManager):
    try:
        await message.delete()
    except:
        pass
    await dialog_manager.start(
        AboutMeStates.all_services,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.DELETE_AND_SEND,
    )


@router.message(Command("send_all_spam"))
async def send_all_spam(message: Message):
    await message.answer("Sending all spam...")
    from manager.spam_service import spam_types

    users_ids = await get_all_user_ids()
    print(f"users_ids: {users_ids}")
    config = get_config()
    spam_manager = config.get_spam_manager()
    try:
        for user_id in users_ids:
            for spam_type, _ in spam_types.items():
                try:
                    user = await get_user(user_id)
                    await spam_manager.send_spam_message(
                        user_id,
                        type_of_spam=spam_type,
                        name=await get_name(user_id),
                        date=datetime.now().strftime("%d.%m.%Y"),
                        balance=user.balance,
                        price=await get_price_for_user(
                            user_id, "subscription_start"
                        ),
                    )
                except Exception as e:
                    print(f"Error sending spam to user {user_id}: {e}")
    except Exception as e:
        print(f"Error sending all spam: {e}")
