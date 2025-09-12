import asyncio
import re
from datetime import datetime
from pathlib import Path

from aiogram import Bot, F
from aiogram.types import ContentType, FSInputFile, Message
from aiogram_dialog import Dialog, DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.text import Const, Format

from config.config import get_config, load_config
from db.models.asto_info import set_astro_info, set_natal_json, set_natal_svg

# from utils.attachments import get_pay_photo_attachment
from db.models.old_workflow.big_mes import get_pay_photo_attachment
from db.models.user import (
    decrease_free_predictions_count,
    get_free_predictions_count,
    get_user_balance,
)

# from dialogs.payment import start_payment
from dialogs.states import (
    AstroStates,
    PaymentStates,
    YogaClubStates,
    format_price,
    get_price_for_user,
)
from utils.geocoding import GeocodingService
from utils.openai_helper import generate_numerology_prediction
from widgets.date_picker import DatePicker
from widgets.time_picker import TimePicker

ADMIN_IDS = load_config().admin_ids


def fix_html_tags_simple(text: str) -> str:
    """
    Простое исправление HTML тегов - закрывает все незакрытые теги в конце текста.
    """
    if not text.strip():
        return text

    # Поддерживаемые HTML теги в Telegram
    supported_tags = ["b", "i", "u", "s", "code", "pre", "a"]

    # Стек для отслеживания открытых тегов
    tag_stack = []

    # Паттерн для поиска HTML тегов
    tag_pattern = r"<(/?)(\w+)(?:\s[^>]*)?>"

    for match in re.finditer(tag_pattern, text):
        is_closing = bool(match.group(1))
        tag_name = match.group(2).lower()

        if tag_name not in supported_tags:
            continue

        if is_closing:
            # Закрывающий тег - убираем из стека если есть
            if tag_name in tag_stack:
                tag_stack.remove(tag_name)
        else:
            # Открывающий тег - добавляем в стек
            tag_stack.append(tag_name)

    # Просто закрываем все незакрытые теги в конце
    result = text
    for tag in reversed(tag_stack):
        result += f"</{tag}>"

    return result


def split_text_simple(text: str, max_length: int = 4000) -> list:
    """
    Простая разбивка текста на страницы с исправлением HTML.
    """
    if len(text) <= max_length:
        return [fix_html_tags_simple(text)]

    pages = []
    # Разбиваем текст по абзацам
    paragraphs = text.split("\n\n")
    current_page = ""

    for paragraph in paragraphs:
        # Проверяем, поместится ли абзац
        test_text = current_page + ("\n\n" if current_page else "") + paragraph

        if len(test_text) <= max_length:
            current_page = test_text
        else:
            # Сохраняем текущую страницу если она не пустая
            if current_page:
                pages.append(fix_html_tags_simple(current_page))
                current_page = paragraph
            else:
                # Абзац слишком длинный - разбиваем по предложениям
                sentences = paragraph.split(". ")
                for i, sentence in enumerate(sentences):
                    if i < len(sentences) - 1:
                        sentence += ". "

                    test_sentence = (
                        current_page + (" " if current_page else "") + sentence
                    )

                    if len(test_sentence) <= max_length:
                        current_page += (
                            " " if current_page else ""
                        ) + sentence
                    else:
                        if current_page:
                            pages.append(fix_html_tags_simple(current_page))
                            current_page = sentence
                        else:
                            # Предложение слишком длинное - просто добавляем
                            pages.append(fix_html_tags_simple(sentence))

    # Добавляем последнюю страницу
    if current_page:
        pages.append(fix_html_tags_simple(current_page))

    return pages if pages else [fix_html_tags_simple(text)]


async def process_name(
    message: Message, widget, dialog_manager: DialogManager, name: str
):
    """Обработка имени пользователя"""
    # print("BURDAAA", message.text)
    dialog_manager.dialog_data["name"] = message.text
    try:
        await message.delete()
    except Exception as e:
        print("BURDAAA 1", e)
    await dialog_manager.next(show_mode=ShowMode.DELETE_AND_SEND)


async def on_date_selected(
    event, widget, dialog_manager: DialogManager, selected_date
):
    """Обработка выбранной даты"""
    dialog_manager.dialog_data["birth_date"] = selected_date.isoformat()
    # await message.delete()
    await dialog_manager.next(show_mode=ShowMode.EDIT)


async def on_time_selected(
    event, widget, dialog_manager: DialogManager, selected_time
):
    """Обработка выбранного времени"""
    if selected_time:
        dialog_manager.dialog_data["birth_time"] = selected_time.isoformat()
    else:
        dialog_manager.dialog_data["birth_time"] = None
    await dialog_manager.next(show_mode=ShowMode.EDIT)


async def process_location(
    message: Message, widget, dialog_manager: DialogManager, **_
):
    """Обработка локации"""
    if dialog_manager.dialog_data.get("error_message"):
        try:
            await dialog_manager.dialog_data["error_message"].delete()
        except Exception as e:
            print("BURDAAA 6", e)
        dialog_manager.dialog_data["error_message"] = None

    if message.text:
        geocoding = GeocodingService()
        location_info = await geocoding.get_location_from_query(message.text)
        if location_info:
            dialog_manager.dialog_data["location_info"] = {
                "city": location_info.city,
                "country": location_info.country,
                "full_address": location_info.full_address,
                "formatted": geocoding.format_location_string(location_info),
            }
            await message.delete()
            await dialog_manager.next(show_mode=ShowMode.DELETE_AND_SEND)
            return
        else:
            dialog_manager.dialog_data["error_message"] = await message.answer(
                """<i>Не удалось определить город по указанному названию. Пожалуйста, попробуйте отправить геолокацию или введите точное наименование города.</i>"""
            )
            try:
                await message.delete()
            except Exception as e:
                print("BURDAAA 5", e)
            await dialog_manager.update(show_mode=ShowMode.DELETE_AND_SEND)
            return

    if message.location:
        # Сохраняем координаты
        dialog_manager.dialog_data["lat"] = message.location.latitude
        dialog_manager.dialog_data["lng"] = message.location.longitude
        # print(
        #     "lat=",
        #     message.location.latitude,
        #     "lng=",
        #     message.location.longitude,
        # )

        # Получаем информацию о городе
        geocoding = GeocodingService()
        location_info = await geocoding.get_location_info(
            message.location.latitude, message.location.longitude
        )

        if location_info:
            dialog_manager.dialog_data["location_info"] = {
                "city": location_info.city,
                "country": location_info.country,
                "full_address": location_info.full_address,
                "formatted": geocoding.format_location_string(location_info),
            }
            await message.delete()
            await dialog_manager.next(show_mode=ShowMode.DELETE_AND_SEND)
        else:
            # await message.answer(
            #     "❌ Не удалось определить город по координатам. "
            #     "Попробуйте отправить локацию еще раз."
            # )
            return
    else:
        # await message.answer(
        #     "❌ Пожалуйста, отправьте локацию через кнопку 📎 -> 📍 Локация или напишите название города в котором родились"
        # )
        dialog_manager.dialog_data["error_message"] = await message.answer(
            """<i>Не удалось определить город по указанному названию. Пожалуйста, попробуйте отправить геолокацию или введите точное наименование города.</i>"""
        )
        try:
            await message.delete()
        except Exception as e:
            print("BURDAAA 5", e)
        await dialog_manager.update(show_mode=ShowMode.DELETE_AND_SEND)
        return


async def get_confirmation_text(dialog_manager: DialogManager, **kwargs):
    """Получить текст для подтверждения данных"""
    # print("BURDAAA 2", dialog_manager.dialog_data)
    try:
        data = dialog_manager.dialog_data

        name = data.get("name", "")
        birth_date = datetime.fromisoformat(data.get("birth_date", ""))
        birth_time = data.get("birth_time")

        # text = "✨ <b>Проверьте ваши данные:</b>\n\n"
        # text += f"👤 <b>Имя:</b> \n"
        # text += f"📅 <b>Дата рождения:</b> \n"
        if birth_time:
            # Парсим время как строку времени, а не как datetime
            from datetime import time

            time_obj = time.fromisoformat(birth_time)
            time_str = f"{time_obj.strftime('%H:%M')}"
        else:
            time_str = "не указано"
        text = f"""
<i><b>Проверьте введённые данные:</b>

</i><i>→ Имя: {name}
</i><i>→ Дата рождения: {birth_date.strftime('%d.%m.%Y')}
</i><i>→ Время рождения: {time_str}</i>
        """
    except Exception as e:
        print("BURDAAA 3", e)
        text = "❌ Ошибка при получении данных"
    try:
        ai_pred_photo = await ai_photo_getter(dialog_manager)
        if ai_pred_photo:
            ai_pred_photo = ai_pred_photo.get("ai_pred_photo")
    except Exception as e:
        print("BURDAAA 4", e)
        ai_pred_photo = None
    return {
        "confirmation_text": text,
        "ai_pred_photo": ai_pred_photo,
    }


async def get_location_confirmation_text(
    dialog_manager: DialogManager, **kwargs
):
    """Получить текст для подтверждения локации"""
    location_info = dialog_manager.dialog_data.get("location_info", {})
    formatted = location_info.get("formatted", "Неизвестная локация")

    # text = f"📍 <b>Место рождения:</b>\n\n\n"
    # text += "Это правильный город?"
    text = f"""
<b><i>Подтвердите, пожалуйста, правильность выбранного города:</i></b>

<i>→ {formatted}</i>
    """
    try:
        ai_pred_photo = await ai_photo_getter(dialog_manager)
        if ai_pred_photo:
            ai_pred_photo = ai_pred_photo.get("ai_pred_photo")
    except Exception as e:
        print("BURDAAA 4", e)
        ai_pred_photo = None
    return {
        "location_text": text,
        "ai_pred_photo": ai_pred_photo,
    }


async def confirm_data(callback, button, dialog_manager: DialogManager):
    """Подтверждение введенных данных"""
    await dialog_manager.next(show_mode=ShowMode.EDIT)


async def restart_input(callback, button, dialog_manager: DialogManager):
    """Начать ввод данных заново"""
    dialog_manager.dialog_data.clear()
    await dialog_manager.start(AstroStates.name, show_mode=ShowMode.EDIT)


async def confirm_location(callback, button, dialog_manager: DialogManager):
    """Подтверждение локации и генерация натальной карты"""
    try:
        data = dialog_manager.dialog_data

        # Подготавливаем данные
        name = data.get("name", "")
        birth_date = datetime.fromisoformat(data.get("birth_date", ""))
        birth_time = data.get("birth_time")
        lat = data.get("lat")
        lng = data.get("lng")

        # Определяем время
        if birth_time:
            # Парсим время как строку времени, а не как datetime
            from datetime import time

            time_obj = time.fromisoformat(birth_time)
            hour = time_obj.hour
            minute = time_obj.minute
        else:
            hour = 12
            minute = 0

        await set_astro_info(
            user_id=dialog_manager.event.from_user.id,
            name=name,
            birth_year=birth_date.year,
            birth_month=birth_date.month,
            birth_day=birth_date.day,
            birth_hour=hour,
            birth_minute=minute,
            lng=lng,
            lat=lat,
            city=data.get("location_info", {}).get("city"),
            country=data.get("location_info", {}).get("country"),
        )

        config = get_config()
        astro_manager = config.get_astro_manager()

        location_info = data.get("location_info", {})
        subject = astro_manager.get_subject(
            name=name,
            year=birth_date.year,
            month=birth_date.month,
            day=birth_date.day,
            hour=hour,
            minute=minute,
            lng=lng,
            lat=lat,
            city=location_info.get("city"),
            # country=location_info.country,
        )

        # Генерируем SVG
        svg_path = astro_manager.get_svg(
            theme="dark",
            # file_name=f"{name}.svg",
            user_id=dialog_manager.event.from_user.id,
            subject=subject,
        )
        await set_natal_svg(
            user_id=dialog_manager.event.from_user.id,
            natal_svg=svg_path,
        )
        natal_json = astro_manager.get_natal_json(subject=subject)
        await set_natal_json(
            user_id=dialog_manager.event.from_user.id,
            natal_json=natal_json,
        )
        # print("NATAL JSON", natal_json)

        # # Пытаемся конвертировать в PNG
        # print("BURDAAA 5", svg_path)
        # png_path = SVGConverter.convert(
        #     svg_path, png_path=svg_path.with_suffix(".png")
        # )

        # Сохраняем путь к файлу для следующего окна
        # if png_path and png_path.exists():
        #     dialog_manager.dialog_data["chart_path"] = str(png_path)
        #     dialog_manager.dialog_data["is_png"] = True
        #     # Удаляем SVG если успешно конвертировали
        #     svg_path.unlink(missing_ok=True)
        # else:
        # Если не удалось конвертировать, используем SVG
        dialog_manager.dialog_data["natal_json"] = natal_json
        dialog_manager.dialog_data["chart_path"] = str(svg_path)
        dialog_manager.dialog_data["is_png"] = False

        await dialog_manager.switch_to(
            AstroStates.ai_prediction_input, show_mode=ShowMode.EDIT
        )
    except Exception as e:
        print("BURDAAA 4", e)
        await dialog_manager.switch_to(
            AstroStates.ai_prediction_input, show_mode=ShowMode.EDIT
        )


async def send_chart(dialog_manager: DialogManager, **kwargs):
    """Отправка натальной карты"""
    chart_path = dialog_manager.dialog_data.get("chart_path")
    is_png = dialog_manager.dialog_data.get("is_png", False)

    if chart_path and Path(chart_path).exists():
        bot: Bot = dialog_manager.middleware_data["bot"]
        user_id = dialog_manager.event.from_user.id

        if is_png:
            # Отправляем как фото если это PNG
            await bot.send_photo(
                chat_id=user_id,
                photo=FSInputFile(chart_path),
                caption="🌟 Ваша натальная карта готова!",
            )
        else:
            # Отправляем как документ если это SVG
            await bot.send_document(
                chat_id=user_id,
                document=FSInputFile(chart_path),
                caption="🌟 Ваша натальная карта готова!\n\n"
                "📎 Файл в формате SVG можно открыть в браузере.",
            )

        # Удаляем временный файл
        Path(chart_path).unlink(missing_ok=True)

    return {}


async def ai_prediction_loading_getter(
    dialog_manager: DialogManager, **kwargs
):
    """Getter for AI prediction loading screen"""
    loading_text = dialog_manager.dialog_data.get(
        "loading_text", "Анализирую числовые вибрации..."
    )
    ai_pred_photo = dialog_manager.dialog_data.get("ai_pred_photo")

    return {
        "loading_text": loading_text,
        "ai_pred_photo": ai_pred_photo,
    }


async def on_submit_query(
    # message: Message, widget, dialog_manager: DialogManager, query: str
    message: Message,
    widget,
    dialog_manager: DialogManager,
    **_,
):
    if dialog_manager.dialog_data.get("error_message"):
        try:
            await dialog_manager.dialog_data["error_message"].delete()
        except Exception as e:
            print("BURDAAA 6", e)
        dialog_manager.dialog_data["error_message"] = None

    if not message.text:
        dialog_manager.dialog_data["error_message"] = await message.answer(
            """<i>Обработка возможна только для текстовых сообщений. Повторите, пожалуйста, ваш запрос.</i>"""
        )
        try:
            await message.delete()
        except Exception as e:
            print("BURDAAA 5", e)
        await dialog_manager.update(show_mode=ShowMode.DELETE_AND_SEND)
        return
    """Handle user query submission for AI prediction"""
    user_id = message.from_user.id

    free_predictions = await get_free_predictions_count(user_id)

    dialog_manager.dialog_data["ai_query"] = message.text

    paid_prediction = dialog_manager.dialog_data.get("paid_prediction", False)
    # print("FREE PREDICTIONS", free_predictions)
    if paid_prediction:
        dialog_manager.dialog_data["paid_prediction"] = False
    elif free_predictions <= 0:
        try:
            await message.delete()
        except Exception as e:
            print(e)
            pass
        await dialog_manager.start(
            (
                PaymentStates.payment_choice
                if await get_user_balance(user_id) > 0
                else PaymentStates.payment
            ),
            data={
                # "amount": 10000,
                # "amount": await get_price("personal_brand"),
                "amount": await get_price_for_user(user_id, "ai_prediction"),
                "description": ("ai_prediction"),
                "previous_state": AstroStates.ai_prediction_input,
                "item_oficial_description": "Прогноз AI-астролог",
                # "was_subscribe": True,
            },
            show_mode=ShowMode.DELETE_AND_SEND,
        )
        return

    try:
        # await message.delete()
        pass
    except Exception as e:
        print(e)
    await dialog_manager.switch_to(
        AstroStates.ai_prediction_loading,
        show_mode=ShowMode.EDIT,
    )

    try:
        natal_json = dialog_manager.dialog_data.get("natal_json")
        task = asyncio.create_task(
            generate_numerology_prediction(message.text, natal_json)
        )
        loading_messages = [
            "🌙 <i>Настраиваюсь на потоки космической энергии...</i>",
            "🌙 <i>Погружаюсь в тайны вашей натальной карты...</i>",
            "🌙 <i>Собираю картину вашей судьбы через звёзды...</i>",
            "🌙 <i>Раскрываю послания, зашифрованные в планетах...</i>",
            "🌙 <i>Исследую гармонию небесных тел в вашем гороскопе...</i>",
            "🌙 <i>Анализирую влияние планет на ваш жизненный путь...</i>",
            "🌙 <i>Изучаю аспекты между планетами в момент рождения...</i>",
            "🌙 <i>Расшифровываю символы астрологических домов...</i>",
            "🌙 <i>Считываю энергетические потоки созвездий...</i>",
            "🌙 <i>Формирую персональный астрологический прогноз...</i>",
        ]

        for i in range(len(loading_messages)):
            dialog_manager.dialog_data["loading_text"] = loading_messages[i]
            await dialog_manager.update({"loading_text": loading_messages[i]})
            if (
                i < len(loading_messages) - 1
            ):  # Don't delay after the last message
                await asyncio.sleep(1.5)

        await dialog_manager.event.bot.send_chat_action(
            user_id, "find_location"
        )
        # try:
        #     await dialog_manager.event.bot.send_chat_action(user_id, "playing")
        #     await asyncio.sleep(2)
        # except Exception as er:
        #     print(er)
        #     pass
        # try:
        #     await dialog_manager.event.bot.send_chat_action(user_id, "typing")
        #     await asyncio.sleep(1.5)
        # except Exception:
        #     pass
        # try:
        #     await dialog_manager.event.bot.send_chat_action(
        #         user_id, "choose_sticker"
        #     )
        #     await asyncio.sleep(1.5)
        # except Exception:
        #     pass
        try:
            prediction = await task
        except Exception as e:
            print(f"\n\nError generating numerology prediction: {e}\n\n")
            prediction = "Произошла ошибка при получении предсказания. Пожалуйста, попробуйте ещё раз чуть позже!"

        dialog_manager.dialog_data["ai_prediction"] = prediction

        try:
            await decrease_free_predictions_count(user_id)
        except Exception as e:
            print(f"\n\nError decreasing free predictions count: {e}\n\n")

        await dialog_manager.switch_to(
            AstroStates.ai_prediction_result,
            show_mode=ShowMode.DELETE_AND_SEND,
        )

    except Exception as e:

        print(f"\n\nError generating numerology prediction: {e}\n\n")

        error_message = """<i><u>Произошла ошибка</u> при получении предсказания.</i> 

<b><i>Пожалуйста, попробуйте ещё раз чуть позже!</i></b>"""
        dialog_manager.dialog_data["ai_prediction"] = error_message

        await dialog_manager.switch_to(
            AstroStates.ai_prediction_result,
            show_mode=ShowMode.DELETE_AND_SEND,
        )


async def ai_prediction_getter(dialog_manager: DialogManager, **kwargs):
    """Getter for AI prediction main screen"""
    user_id = dialog_manager.event.from_user.id

    free_predictions_count = await get_free_predictions_count(user_id)

    prediction_price_str = await format_price(user_id, "ai_prediction")
    return {
        "free_predictions_count": free_predictions_count,
        "prediction_price_str": prediction_price_str,
    }


async def restart_location(callback, button, dialog_manager: DialogManager):
    """Вернуться к вводу локации"""
    await dialog_manager.switch_to(AstroStates.natal_place)


async def next_page(callback, button, dialog_manager: DialogManager):
    """Переход на следующую страницу"""
    current_page = dialog_manager.dialog_data.get("current_page", 0)
    dialog_manager.dialog_data["current_page"] = current_page + 1
    await dialog_manager.update({})


async def prev_page(callback, button, dialog_manager: DialogManager):
    """Переход на предыдущую страницу"""
    current_page = dialog_manager.dialog_data.get("current_page", 0)
    dialog_manager.dialog_data["current_page"] = current_page - 1
    await dialog_manager.update({})


async def ai_prediction_result_getter(dialog_manager: DialogManager, **kwargs):
    """Getter for AI prediction result screen"""
    try:
        prediction = dialog_manager.dialog_data.get("ai_prediction", "")
        # print("PREDICTION", prediction)
        current_page = dialog_manager.dialog_data.get("current_page", 0)

        # Максимальная длина сообщения в Telegram (оставляем запас для кнопок)
        MAX_MESSAGE_LENGTH = 4000

        # Используем простую функцию для разбиения текста с исправлением HTML
        pages = split_text_simple(prediction, MAX_MESSAGE_LENGTH)

        total_pages = len(pages)
        # print("CURRENT PAGE", current_page)
        # print("TOTAL PAGES", total_pages)

        if current_page >= total_pages:
            current_page = total_pages - 1
            dialog_manager.dialog_data["current_page"] = current_page
        elif current_page < 0:
            current_page = 0
            dialog_manager.dialog_data["current_page"] = current_page

        has_next = current_page < total_pages - 1
        has_prev = current_page > 0

        current_page_text = (
            pages[current_page] if 0 <= current_page < len(pages) else ""
        )

        return {
            "ai_prediction": current_page_text,
            "current_page": current_page,
            "total_pages": total_pages,
            "show_pagination": total_pages > 1,
            "has_next": has_next,
            "has_prev": has_prev,
            # "page_info": f"Страница {current_page + 1} из {total_pages}",
        }
    except Exception as e:
        print(f"Error in ai_prediction_result_getter: {e}")
        # В случае ошибки возвращаем безопасные значения
        prediction = dialog_manager.dialog_data.get(
            "ai_prediction", "Произошла ошибка при отображении прогноза."
        )
        return {
            "ai_prediction": prediction,
            "current_page": 0,
            "total_pages": 1,
            "show_pagination": False,
            "has_next": False,
            "has_prev": False,
        }


async def back_to_main(callback, button, dialog_manager: DialogManager):
    """Вернуться в главное меню"""
    await dialog_manager.start(
        YogaClubStates.main, show_mode=ShowMode.DELETE_AND_SEND
    )


async def back_to_main_save(callback, button, dialog_manager: DialogManager):
    """Вернуться в главное меню"""
    prediction = dialog_manager.dialog_data.get("ai_prediction", "")
    # print("PREDICTION", prediction)
    current_page = 0

    MAX_MESSAGE_LENGTH = 4000

    pages = split_text_simple(prediction, MAX_MESSAGE_LENGTH)

    for page in pages:
        await dialog_manager.event.bot.send_message(
            dialog_manager.event.from_user.id,
            page,
            parse_mode="HTML",
        )

    await dialog_manager.start(
        YogaClubStates.main, show_mode=ShowMode.DELETE_AND_SEND
    )


async def ai_photo_getter(dialog_manager: DialogManager, **kwargs):
    """Getter for AI photo"""
    if dialog_manager.dialog_data.get("ai_pred_photo") is None:
        ai_pred_photo = await get_pay_photo_attachment(
            dialog_manager.event.bot, "src/misk/navigation/ai_predict.png"
        )
        dialog_manager.dialog_data["ai_pred_photo"] = ai_pred_photo
    else:
        ai_pred_photo = dialog_manager.dialog_data.get("ai_pred_photo")
    name = dialog_manager.dialog_data.get("name", "")
    return {
        "ai_pred_photo": dialog_manager.dialog_data.get("ai_pred_photo", None),
        "name": name,
    }


async def ai_question_getter(dialog_manager: DialogManager, **kwargs):
    """Getter for AI question"""
    try:
        name = dialog_manager.dialog_data.get("name", "")
        not_first_time = dialog_manager.dialog_data.get(
            "not_first_time", False
        )
        prediction_price_str = await format_price(
            dialog_manager.event.from_user.id, "ai_prediction"
        )
        free_predictions_count = await get_free_predictions_count(
            dialog_manager.event.from_user.id
        )
        if dialog_manager.start_data:
            not_first_time = dialog_manager.start_data.get(
                "not_first_time", False
            )
            name = dialog_manager.start_data.get("name", name)
        try:
            ai_pred_photo = await ai_photo_getter(dialog_manager)
            if ai_pred_photo:
                ai_pred_photo = ai_pred_photo.get("ai_pred_photo")
        except Exception as e:
            print("BURDAAA 4", e)
            ai_pred_photo = None
        return {
            "first_time": not not_first_time,
            "name": name,
            "not_first_time": not_first_time,
            "ai_pred_photo": ai_pred_photo,
            "price": prediction_price_str,
            "free_predictions_count": free_predictions_count,
            "have_free": free_predictions_count > 0,
            "dont_have_free": (
                free_predictions_count == 0
                or free_predictions_count is None
                or free_predictions_count < 0
            ),
        }
    except Exception as e:
        print(f"Error in ai_question_getter: {e}")
        return {
            "first_time": not not_first_time,
            "name": name,
            "not_first_time": not_first_time,
        }


# Отладочные функции удалены для упрощения кода

astro_dialog = Dialog(
    # Окно 1: Ввод имени
    # Window(
    #     DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
    #     Const("ТЕКСТ"),
    #     SwitchTo(
    #         Format("Ввести данные"),
    #         id="switch_to_input",
    #         state=AstroStates.name,
    #     ),
    #     SwitchTo(
    #         Format("Задать вопрос"),
    #         id="switch_to_question",
    #         state=AstroStates.ai_prediction_input,
    #     ),
    #     Button(
    #         Const("Вернуться в главное меню"),
    #         id="back_to_main",
    #         on_click=back_to_main,
    #     ),
    #     state=AstroStates.main,
    #     getter=ai_photo_getter,
    # ),
    Window(
        DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Const(
            """
<i><b>Добро пожаловать в раздел AI-прогноз по натальной карте 🪐</b>

Я — виртуальный помощник астролога Инны Булгаровой. Отправьте, пожалуйста, данные о рождении, и я быстро построю и проанализирую вашу карту, </i><i><b>чтобы ответить на главный вопрос.</b>

Чтобы вы убедились в точности прогноза, </i><i><b>мы дарим вам один бесплатный прогноз,</b> а стоимость каждого последующего </i><i><b>— 799 рублей. </b>

[ При желании более глубокого разбора вы всегда можете записаться на персональную консультацию к Инне. ]

</i><i><b>Готовы начать?</b> Для построения карты мне понадобятся ваши данные 🪄

→ Пожалуйста, введите имя:</i>
              """
        ),
        TextInput(
            id="name_input",
            on_success=process_name,
        ),
        state=AstroStates.name,
        getter=ai_photo_getter,
    ),
    # Окно 2: Выбор даты рождения
    Window(
        DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Format(
            """<b><i>Отлично, {name}, продолжаем</i></b>⚡️

<i>Пожалуйста, укажите в моём виджете дату своего рождения!</i>"""
        ),
        DatePicker(
            id="birth_date_picker",
            on_click=on_date_selected,
        ),
        state=AstroStates.natal_date,
        getter=ai_photo_getter,
    ),
    # Окно 3: Выбор времени рождения
    Window(
        DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Const(
            """
<b><i>Выберите время рождения:</i></b>

<i>→ Время указывается по вашему местному времени.</i>
              """
        ),
        # Const("<i>→ Время указывается по вашему местному времени.</i>"),
        TimePicker(
            id="birth_time_picker",
            on_click=on_time_selected,
            allow_unknown=True,
        ),
        state=AstroStates.natal_time,
        getter=ai_photo_getter,
    ),
    # Окно 4: Ввод места рождения
    Window(
        DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Format(
            """
<b><i>Пожалуйста, укажите в текстовом виде название города, в котором вы родились, либо, для большей точности, отправьте геолокацию места рождения в следующем формате:</i></b>

<i>→ Нажмите на символ «📎»...
→ Выберите «Геопозиция»...
→ Нажмите «🔍» и введите город на карте...</i>
<i>→ Отправьте карту</i>.
            """
        ),
        MessageInput(
            func=process_location,
            content_types=[ContentType.LOCATION, ContentType.TEXT],
        ),
        state=AstroStates.natal_place,
        getter=ai_photo_getter,
    ),
    # Окно 5: Подтверждение данных
    Window(
        DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Format("{confirmation_text}"),
        Row(
            Button(
                Const("Да, все верно"),
                id="confirm_data",
                on_click=confirm_data,
            ),
            Button(
                Const("Изменить"),
                id="restart_input",
                on_click=restart_input,
            ),
        ),
        state=AstroStates.confirm_data,
        getter=get_confirmation_text,
    ),
    # Окно 6: Подтверждение локации
    Window(
        DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Format("{location_text}"),
        Row(
            Button(
                Const("Да, все верно"),
                id="confirm_location",
                on_click=confirm_location,
            ),
            Button(
                Const("Изменить"),
                id="restart_location",
                on_click=restart_location,
            ),
        ),
        state=AstroStates.confirm_location,
        getter=get_location_confirmation_text,
    ),
    Window(
        DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Format(
            """
<i>Мы очень рады познакомиться с вами 🪐</i>

<i>[</i> <i>{name}, сформулируйте, пожалуйста, вопрос </i><i><b>— и мы с удовольствием поможем вам,</b> опираясь на астрологические принципы.</i> <i>]</i>

<i>Если пока трудно определиться, </i><b><i>приведём несколько примеров:</i></b>

<i><b><b><i>•</i></b></b> Когда я встречу свою любовь?
</i><i><b><b><i>•</i></b></b> Когда наступит период роста?
</i><i><b><b><i>•</i></b></b> Как улучшить карьеру?
</i><i><b><b><i>•</i></b></b> Когда воцарится гармония в отношениях?</i>
            """,
            when=F["first_time"],
        ),
        Format(
            """<i><b>{name}, рады видеть вас вновь в этом разделе</b> 🌙

Что бы вы хотели узнать сегодня?

</i><b><i>Вот несколько примеров:</i></b>
<i>
<b><i>•</i></b> В каком году я выйду замуж?
<b><i>•</i></b> Каково моё предназначение?
<b><i>•</i></b> Сколько у меня будет детей?</i>
""",
            when=F["not_first_time"],
        ),
        Format(
            """<i>[ Стоимость одного вопроса — {price} рублей. ]</i>
<i>
Ждем ваш вопрос </i><b><i>— напишите его ниже:</i></b>
              """,
            when=F["dont_have_free"] & F["not_first_time"],
        ),
        # when=F,
        Format(
            """<i>[ Ваш баланс запросов: {free_predictions_count} ]</i>
<i>
Ждем ваш вопрос </i><b><i>— напишите его ниже:</i></b>
              """,
            when=F["have_free"],
        ),
        # when=F,
        MessageInput(
            # id="query_input",
            func=on_submit_query,
            # content_types=[ContentType.TEXT],
        ),
        # Start(
        #     Format("<< Вернуться в главное меню"),
        #     id="back_to_ai_main",
        #     state=YogaClubStates.main,
        #     show_mode=ShowMode.DELETE_AND_SEND,
        # ),
        state=AstroStates.ai_prediction_input,
        # getter=ai_prediction_getter,
        # getter=ai_photo_getter,
        getter=ai_question_getter,
    ),
    Window(
        # DynamicMedia("ai_pred_photo", when="ai_pred_photo"),
        Format("{loading_text}"),
        state=AstroStates.ai_prediction_loading,
        getter=ai_prediction_loading_getter,
    ),
    Window(
        Format("{ai_prediction}"),
        Row(
            Button(
                Const("<< Назад"),
                id="prev_page",
                on_click=prev_page,
                when=F["has_prev"],
            ),
            Button(
                Const("Вперед >>"),
                id="next_page",
                on_click=next_page,
                when=F["has_next"],
            ),
        ),
        Button(
            # Const("Вернуться в главное меню"),
            Const("[ Принимаю и благодарю ]"),
            id="back_to_main_2",
            on_click=back_to_main_save,
        ),
        state=AstroStates.ai_prediction_result,
        getter=ai_prediction_result_getter,
    ),
)

# if len(prediction) <= MAX_MESSAGE_LENGTH:
#     # Если текст помещается в одно сообщение
#     return {
#         "ai_prediction": prediction,
#         "current_page": current_page,
#         "total_pages": 1,
#         "show_pagination": False,
#         "has_next": False,
#         "has_prev": False,
#     }

# # Разбиваем текст по абзацам
# paragraphs = prediction.split("\n\n")
# pages = []
# current_page_text = ""

# for paragraph in paragraphs:
#     # Проверяем, поместится ли абзац в текущую страницу
#     test_text = (
#         current_page_text
#         + ("\n\n" if current_page_text else "")
#         + paragraph
#     )

#     if len(test_text) <= MAX_MESSAGE_LENGTH:
#         current_page_text = test_text
#     else:
#         # Если текущая страница не пустая, сохраняем её
#         if current_page_text:
#             pages.append(current_page_text)
#             current_page_text = paragraph
#         else:
#             # Если абзац слишком длинный даже для отдельной страницы,
#             # разбиваем его по предложениям
#             sentences = paragraph.split(". ")
#             for i, sentence in enumerate(sentences):
#                 if i < len(sentences) - 1:
#                     sentence += ". "

#                 test_text = (
#                     current_page_text
#                     + ("\n\n" if current_page_text else "")
#                     + sentence
#                 )

#                 if len(test_text) <= MAX_MESSAGE_LENGTH:
#                     current_page_text = test_text
#                 else:
#                     if current_page_text:
#                         pages.append(current_page_text)
#                         current_page_text = sentence
#                     else:
#                         # Если предложение всё ещё слишком длинное, просто добавляем его
#                         pages.append(sentence)
#                         current_page_text = ""

# if current_page_text:
#     pages.append(current_page_text)

# if not pages:
#     pages = [prediction]
