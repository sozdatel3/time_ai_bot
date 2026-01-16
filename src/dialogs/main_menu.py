from pathlib import Path

from aiogram import Bot, F
from aiogram.types import CallbackQuery
from aiogram_dialog import (
    Dialog,
    DialogManager,
    ShowMode,
    StartMode,
    Window,
)
from aiogram_dialog.widgets.kbd import (
    Button,
    Group,
    Select,
    Start,
    Url,
)
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from config.config import ADMIN_IDS, get_config
from db.models.asto_info import get_astro_info
from db.models.old_workflow.big_mes import get_pay_photo_attachment
from db.models.user import get_user, get_user_language, set_language
from texts.text import (
    get_publications_buttons,
    get_text,
    get_prompts_texts,
    get_prompts_buttons,
)
from utils.telethon_status import send_playing_action

from .states import (
    AdminStates,
    AstroStates,
    ReferProgramStates,
    YogaClubStates,
)


async def yoga_club_getter(dialog_manager: DialogManager, **_):
    try:

        bot = dialog_manager.middleware_data.get("bot")

        if dialog_manager.dialog_data.get("main_photo") is None:
            main_photo = await get_pay_photo_attachment(
                bot,
                str(
                    Path(__file__).resolve().parent.parent
                    / "misk"
                    / "navigation"
                    / "main.png"
                ),
            )
            dialog_manager.dialog_data["main_photo"] = main_photo
        else:
            main_photo = dialog_manager.dialog_data.get("main_photo")

        user = dialog_manager.middleware_data.get("event_from_user")
        user_id = user.id
        language = await get_user_language(user_id) or "ru"

        publications_button = get_text("publications_button", language)
        # publications_button = "sad"
        print("PUBLICATIONS BUTTON 1", publications_button)

        publications_url_text = get_text("publications_url_text", language)
        prepared_prompts_button = get_text("prepared_prompts_button", language)

        return {
            "is_admin": user_id in ADMIN_IDS,
            "title": get_text("main_menu_title", language),
            "main_photo": main_photo,
            "full_text": "MAIN MENU",
            "publications_button": publications_button,
            "publications_url_text": publications_url_text,
            "prepared_prompts_button": prepared_prompts_button,
            "time_video": get_text("time_video", language),
            "time_video_button": get_text("time_video_button", language),
        }
    except Exception:
        import traceback

        traceback.print_exc()
        return {
            "active": False,
            "title": get_text("main_menu_title", "ru"),
            "publications_button": get_text("publications_button", "ru"),
            "publications_url_text": get_text("publications_url_text", "ru"),
            "is_admin": False,
            "user_test_status": False,
            "is_sales_window": False,
            "have_reminder": False,
            "have_active_test_period": False,
            "have_active_subscription": False,
            "has_next_page": True,
            "has_previous_page": False,
            "main_photo": main_photo,
            "status_text": "",
            "time_video": get_text("time_video", "ru"),
            "time_video_button": get_text("time_video_button", "ru"),
            "prepared_prompts_button": get_text(
                "prepared_prompts_button", "ru"
            ),
        }


async def on_main_menu(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        YogaClubStates.main,
        show_mode=ShowMode.EDIT,
    )


async def on_main_menu_publications(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        YogaClubStates.publications,
        show_mode=ShowMode.EDIT,
    )


async def on_main_menu_prompts(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(
        YogaClubStates.prompts,
        show_mode=ShowMode.EDIT,
    )


async def test_period_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(YogaClubStates.test_period)


async def on_previous_page(c: CallbackQuery, b: Button, m: DialogManager):
    current = m.dialog_data.get("current_page", 0)
    m.dialog_data["current_page"] = current - 1
    await m.switch_to(YogaClubStates.main, show_mode=ShowMode.EDIT)


async def on_next_page(c: CallbackQuery, b: Button, m: DialogManager):

    current = m.dialog_data.get("current_page", 0)
    m.dialog_data["current_page"] = current + 1

    await m.switch_to(YogaClubStates.main, show_mode=ShowMode.EDIT)


async def process_refer_program(
    c: CallbackQuery, button: Button, manager: DialogManager
):

    await manager.start(
        ReferProgramStates.main,
        show_mode=ShowMode.EDIT,
    )


async def astro_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):

    astro_info = await get_astro_info(c.from_user.id)

    if manager.start_data:
        try:
            mes_to_del = manager.start_data.get("mes_to_del")
            if mes_to_del:
                await mes_to_del.delete()
        except Exception as e:
            print("BURDAAA 5", e)
            pass

    try:
        if astro_info is None:
            await manager.start(AstroStates.name, mode=StartMode.RESET_STACK)
        else:
            await manager.start(
                AstroStates.ai_prediction_input,
                data={
                    "not_first_time": True,
                    "name": astro_info.name or c.from_user.first_name,
                },
                show_mode=ShowMode.EDIT,
            )

    except Exception as e:
        print("BURDAAA 5", e)
        await manager.start(AstroStates.name, mode=StartMode.RESET_STACK)


async def notify_admins_about_ai(user_id: int, bot: Bot):
    config = get_config()
    user = await get_user(user_id)
    await config.get_admin_notifier(bot)._send_to_admins(
        f"""<i>🪄Пользователь @{user.username} нажал на раздел «AI-прогноз».
</i><b><i>Дата регистрации пользователя:</i></b> {user.created_at}"""
    )


async def test_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):

    try:
        await send_playing_action(c.from_user.id)
    except Exception as e:
        print("BURDAAA 6", e)

    c.answer()


async def choose_language_handler(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await set_language(c.from_user.id, button.widget_id)
    await manager.start(
        YogaClubStates.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT,
    )


async def on_publications(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(
        YogaClubStates.publications,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT,
    )


async def on_prepared_prompts(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.start(
        YogaClubStates.prompts,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT,
    )


async def publications_getter(dialog_manager: DialogManager, **_):
    try:
        language = (
            await get_user_language(dialog_manager.event.from_user.id) or "ru"
        )
    except Exception as e:
        print("BURDAAA 7", e)
        language = "ru"
    # publications = []
    # publications =
    print("PUBLICATIONS", get_publications_buttons(language))
    photo = await get_pay_photo_attachment(
        dialog_manager.event.bot,
        str(
            Path(__file__).resolve().parent.parent
            / "misk"
            / "navigation"
            / "mam.png"
        ),
    )
    return {
        "publications": get_publications_buttons(language),
        "photo": photo,
        # "publications_texts": [i["name"] for i in publications],
        "publications_text": get_text("publications_text", language),
        "back_button_to_main_menu": get_text(
            "back_button_to_main_menu", language
        ),
    }


async def publication_selected_getter(dialog_manager: DialogManager, **_):
    # print("\n\nPUBLICATION SELECTED GETTER\n\n")
    language = (
        await get_user_language(dialog_manager.event.from_user.id) or "ru"
    )
    id = dialog_manager.dialog_data.get("selected_publication_id")
    new_id = id.split("_")[1]
    # new_id_minus_one = int(new_id) - 1
    # print("NEW ID MINUS ONE", new_id_minus_one)
    photo_pub = await get_pay_photo_attachment(
        dialog_manager.event.bot,
        str(
            Path(__file__).resolve().parent.parent
            / "misk"
            / "publication"
            / f"{new_id}.png"
        ),
    )
    # print("PHOTO", photo_pub)
    print("ID", id)
    publication_text = get_text(f"publication_{new_id}_text", language)

    # print("PUBLICATION TEXT", publication_text)

    return {
        "photo_pub": photo_pub,
        "publication_text": publication_text,
        "back_button_to_publications": get_text(
            "back_button_to_publications", language
        ),
    }


async def on_publications_selected(
    c: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    print("BUTTONsssss")

    print("ID", item_id)
    manager.dialog_data["selected_publication_id"] = item_id
    await manager.switch_to(
        YogaClubStates.publications_selected, show_mode=ShowMode.EDIT
    )


async def on_prompt_selected(
    c: CallbackQuery, widget: Select, manager: DialogManager, item_id: str
):
    print("PROMPT SELECTED")

    print("ID", item_id)
    manager.dialog_data["selected_prompt_id"] = item_id
    await manager.switch_to(
        YogaClubStates.prompt_selected, show_mode=ShowMode.EDIT
    )


async def prompt_selected_getter(dialog_manager: DialogManager, **_):
    try:
        # print("\n\nPUBLICATION SELECTED GETTER\n\n")
        language = (
            await get_user_language(dialog_manager.event.from_user.id) or "ru"
        )
        id = dialog_manager.dialog_data.get("selected_prompt_id")
        new_id = id.split("_")[1]
        # new_id_minus_one = int(new_id) - 1
        # print("NEW ID MINUS ONE", new_id_minus_one)
        photo_pub = await get_pay_photo_attachment(
            dialog_manager.event.bot,
            str(
                Path(__file__).resolve().parent.parent
                / "misk"
                / "prompts"
                / f"{new_id}.png"
            ),
        )
        # print("PHOTO", photo_pub)
        print("ID", id)
        publication_text = get_text(f"prompt_{new_id}_text", language)

        # print("PUBLICATION TEXT", publication_text)

        return {
            "prompt_photo": photo_pub,
            "prompt_text": publication_text,
            "back_button_to_prompts": get_text(
                "back_button_to_prompts", language
            ),
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "photo_pub": None,
            "prompt_text": "Error",
            "back_button_to_prompts": "Back",
        }


async def on_time_video(
    c: CallbackQuery, button: Button, manager: DialogManager
):
    await manager.switch_to(YogaClubStates.time_video, show_mode=ShowMode.EDIT)


async def time_video_getter(dialog_manager: DialogManager, **_):

    language = (
        await get_user_language(dialog_manager.event.from_user.id) or "ru"
    )
    time_video_gif = await get_pay_photo_attachment(
        dialog_manager.event.bot,
        str(
            Path(__file__).resolve().parent.parent
            / "misk"
            / "person_interior"
            / "time.MP4"
        ),
        True,
    )

    time_video = get_text(
        "time_video",
        language,
    )
    back_button_to_main_menu = get_text("back_button_to_main_menu", language)
    time_stat_button = get_text("time_stat_button", language)

    return {
        "time_video_gif": time_video_gif,
        "time_video": time_video,
        "back_button_to_main_menu": back_button_to_main_menu,
        "time_stat_button": time_stat_button,
    }


async def prepared_prompts_select_getter(dialog_manager: DialogManager, **_):
    try:
        language = (
            await get_user_language(dialog_manager.event.from_user.id) or "ru"
        )
        prepared_prompts = get_text(
            "prompt_main_text",
            language,
        )
        back_button_to_main_menu = get_text(
            "back_button_to_main_menu", language
        )
        # prepared_prompts_button = get_text("prepared_prompts_button", language)
        photo_pub = await get_pay_photo_attachment(
            dialog_manager.event.bot,
            str(
                Path(__file__).resolve().parent.parent
                / "misk"
                / "prompts"
                / "main.png"
            ),
        )
        # prompts = get_prompts_texts(language)
        print("promm")
        prompts = get_prompts_buttons(language)
        print("promm", prompts)
        print("prommmmmpts", prepared_prompts)
        return {
            "prompts": prompts,
            "prompt_main_text": prepared_prompts,
            "back_button_to_main_menu": back_button_to_main_menu,
            # "prepared_prompts_button": prepared_prompts_button,
            "prompt_main_photo": photo_pub,
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        return {
            "prompts": [],
            "prompt_main_text": "Error",
            "back_button_to_main_menu": "Back",
            "prompt_main_photo": None,
        }


yoga_club_dialog = Dialog(
    Window(
        Format(
            """<b>Выбери язык — и войди в историю.</b>
<i><u>Select your language — and step into the story.</u></i>"""
        ),
        Button(
            Const("Русский — язык чувств"),
            id="ru",
            on_click=choose_language_handler,
        ),
        Button(
            Const("English — language of ideas"),
            id="en",
            on_click=choose_language_handler,
        ),
        state=YogaClubStates.choose_language,
    ),
    Window(
        DynamicMedia("main_photo", when="main_photo"),
        Format("{title}"),
        Button(
            Format("{prepared_prompts_button}"),
            id="prepared_prompts",
            on_click=on_prepared_prompts,
        ),
        Button(
            Format("{time_video_button}"),
            id="time_video",
            on_click=on_time_video,
        ),
        Button(
            Format("{publications_button}"),
            id="publications",
            on_click=on_publications,
        ),
        Url(
            Format("{publications_url_text}"),
            Format("timeai.ai"),
            id="publications_url",
        ),
        # Button(
        #     Const("[ АI-прогноз ]"),
        #     id="astro",
        #     on_click=astro_handler,
        # ),
        # Start(
        #     Const("[ Как я могу помочь ]"),
        #     id="about_me",
        #     state=AboutMeStates.main,
        #     mode=StartMode.RESET_STACK,
        #     show_mode=ShowMode.DELETE_AND_SEND,
        # ),
        # Button(
        #     Const("Задать вопрос"),
        #     id="ask_question",
        #     on_click=ask_question_handler,
        # ),
        Start(
            Const("Администрация"),
            id="admin",
            state=AdminStates.MAIN,
            mode=StartMode.RESET_STACK,
            show_mode=ShowMode.EDIT,
            when=F["is_admin"],
        ),
        state=YogaClubStates.main,
        getter=yoga_club_getter,
    ),
    Window(
        DynamicMedia("time_video_gif", when="time_video_gif"),
        Format("{time_video}"),
        Url(
            Format("{time_stat_button}"),
            Format(
                "https://dsgners.ru/timeaiai/24574-chelovek-interer-v-stile-kubizm"
            ),
            id="time_stat_button",
        ),
        Button(
            Format("{back_button_to_main_menu}"),
            id="back_to_main_menu",
            on_click=on_main_menu,
        ),
        state=YogaClubStates.time_video,
        getter=time_video_getter,
    ),
    Window(
        DynamicMedia("photo", when="photo"),
        Format("{publications_text}"),
        Group(
            Select(
                Format("{item[name]}"),
                id="publications_select",
                item_id_getter=lambda x: x["id"],
                items="publications",
                on_click=on_publications_selected,
            ),
            width=1,
        ),
        Button(
            Format("{back_button_to_main_menu}"),
            id="back_to_main_menu",
            on_click=on_main_menu,
        ),
        # id="publications_main",
        # on_click=on_publications,
        state=YogaClubStates.publications,
        getter=publications_getter,
    ),
    Window(
        DynamicMedia("photo_pub", when="photo_pub"),
        Format("{publication_text}"),
        Button(
            Format("{back_button_to_publications}"),
            id="back_to_publications",
            on_click=on_main_menu_publications,
        ),
        # id="publications_main",
        # on_click=on_publications,
        state=YogaClubStates.publications_selected,
        getter=publication_selected_getter,
    ),
    Window(
        DynamicMedia("prompt_main_photo", when="prompt_main_photo"),
        Format("{prompt_main_text}"),
        Group(
            Select(
                Format("{item[name]}"),
                id="prompt_select",
                item_id_getter=lambda x: x["id"],
                items="prompts",
                on_click=on_prompt_selected,
            ),
            width=1,
        ),
        Button(
            Format("{back_button_to_main_menu}"),
            id="back_to_main_menu",
            on_click=on_main_menu,
        ),
        # id="publications_main",
        # on_click=on_publications,
        state=YogaClubStates.prompts,
        getter=prepared_prompts_select_getter,
    ),
    Window(
        DynamicMedia("prompt_photo", when="prompt_photo"),
        Format("{prompt_text}"),
        Button(
            Format("{back_button_to_prompts}"),
            id="back_to_prompts",
            on_click=on_main_menu_prompts,
        ),
        # id="publications_main",
        # on_click=on_publications,
        state=YogaClubStates.prompt_selected,
        getter=prompt_selected_getter,
    ),
    # *hello_windows,
)
