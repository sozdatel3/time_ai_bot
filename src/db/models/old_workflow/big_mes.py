import os
from enum import Enum
from typing import List, Optional, Tuple

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.types import FSInputFile, Message
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram_dialog.api.entities import MediaAttachment, MediaId
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.config import get_config
from db.db import AsyncSessionLocal, Base
from db.models.base import TimestampMixin


class MediaType(Enum):
    """Перечисление типов медиа для унификации"""

    PHOTO = "photo"
    VIDEO = "video"
    AUDIO = "audio"
    VOICE = "voice"
    DOCUMENT = "document"
    VIDEO_NOTE = "video_note"
    ANIMATION = "animation"


class BigMes(Base, TimestampMixin):
    __tablename__ = "big_mes"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer)
    message_name = Column(String)
    file_unique_id = Column(String, nullable=True, default=None)


# Базовые функции для работы с БД
async def _get_record_by_name(
    session: AsyncSession, name: str
) -> Optional[BigMes]:
    """Получить запись из БД по имени"""
    result = await session.execute(
        select(BigMes).where(BigMes.message_name == name)
    )
    return result.scalar_one_or_none()


async def _get_all_records_by_name(
    session: AsyncSession, name: str
) -> List[BigMes]:
    """Получить все записи из БД по имени"""
    result = await session.execute(
        select(BigMes).where(BigMes.message_name == name)
    )
    return result.scalars().all()


async def _save_or_update_record(
    session: AsyncSession,
    name: str,
    message_id: str,
    file_unique_id: Optional[str] = None,
) -> None:
    """Сохранить или обновить запись в БД"""
    existing_record = await _get_record_by_name(session, name)

    if existing_record:
        existing_record.message_id = message_id
        if file_unique_id:
            existing_record.file_unique_id = file_unique_id
    else:
        session.add(
            BigMes(
                message_id=message_id,
                message_name=name,
                file_unique_id=file_unique_id,
            )
        )
    await session.commit()


async def _delete_records_by_name(session: AsyncSession, name: str) -> None:
    """Удалить все записи по имени"""
    records = await _get_all_records_by_name(session, name)
    for record in records:
        await session.delete(record)
    await session.commit()


# Базовые функции для отправки медиа
async def _send_media(
    bot: Bot,
    file_path: str,
    media_type: MediaType,
    filename: Optional[str] = None,
    caption: Optional[str] = None,
) -> Message:
    """Универсальная функция для отправки медиа в Telegram"""
    config = get_config()
    chat_id = config.admin_ids[0]

    with open(file_path, "rb") as file:
        fs_input_file = FSInputFile(file.name, filename=filename)

        if media_type == MediaType.PHOTO:
            return await bot.send_photo(chat_id=chat_id, photo=fs_input_file)
        elif media_type == MediaType.VIDEO:
            return await bot.send_video(chat_id=chat_id, video=fs_input_file)
        elif media_type == MediaType.AUDIO:
            return await bot.send_audio(chat_id=chat_id, audio=fs_input_file)
        elif media_type == MediaType.VOICE:
            return await bot.send_voice(chat_id=chat_id, voice=fs_input_file)
        elif media_type == MediaType.DOCUMENT:
            return await bot.send_document(
                chat_id=chat_id,
                document=fs_input_file,
                # filename=filename,
                caption=caption,
            )
        elif media_type == MediaType.VIDEO_NOTE:
            return await bot.send_video_note(
                chat_id=chat_id, video_note=fs_input_file
            )
        elif media_type == MediaType.ANIMATION:
            return await bot.send_animation(
                chat_id=chat_id, animation=fs_input_file
            )
        else:
            raise ValueError(f"Unsupported media type: {media_type}")


def _extract_file_ids(
    message: Message, media_type: MediaType
) -> Tuple[str, str]:
    """Извлечь file_id и file_unique_id из сообщения"""
    if media_type == MediaType.PHOTO and message.photo:
        return message.photo[-1].file_id, message.photo[-1].file_unique_id
    elif media_type == MediaType.VIDEO and message.video:
        return message.video.file_id, message.video.file_unique_id
    elif media_type == MediaType.AUDIO and message.audio:
        return message.audio.file_id, message.audio.file_unique_id
    elif media_type == MediaType.VOICE and message.voice:
        return message.voice.file_id, message.voice.file_unique_id
    elif media_type == MediaType.DOCUMENT and message.document:
        return message.document.file_id, message.document.file_unique_id
    elif media_type == MediaType.VIDEO_NOTE and message.video_note:
        return message.video_note.file_id, message.video_note.file_unique_id
    elif media_type == MediaType.ANIMATION and message.animation:
        return message.animation.file_id, message.animation.file_unique_id
    else:
        raise ValueError(
            f"Could not extract file IDs for media type: {media_type}"
        )


async def is_valid_file_id(bot: Bot, file_id: str) -> bool:
    """Проверить валидность file_id"""
    try:
        await bot.get_file(file_id)
        return True
    except Exception as e:
        print(f"Invalid file_id {file_id}: {e}")
        return False


# Универсальная функция для создания/получения медиа
async def _create_or_get_media(
    bot: Bot,
    name: str,
    file_path: str,
    media_type: MediaType,
    force: bool = False,
    filename: Optional[str] = None,
    validate: bool = True,
    caption: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Универсальная функция для создания или получения медиа из БД

    Args:
        bot: Экземпляр бота
        name: Имя записи в БД
        file_path: Путь к файлу
        media_type: Тип медиа
        force: Принудительное обновление
        filename: Имя файла для отправки
        validate: Проверять ли валидность file_id

    Returns:
        Tuple[file_id, file_unique_id]
    """
    try:
        async with AsyncSessionLocal() as session:
            # Попытка получить из БД
            if not force:
                existing_record = await _get_record_by_name(session, name)
                if existing_record and existing_record.message_id:
                    if not validate or await is_valid_file_id(
                        bot, str(existing_record.message_id)
                    ):
                        return (
                            str(existing_record.message_id),
                            existing_record.file_unique_id,
                        )
                    else:
                        force = True

            # Создание нового
            if force or not existing_record:
                try:
                    message = await _send_media(
                        bot, file_path, media_type, filename, caption
                    )
                    file_id, file_unique_id = _extract_file_ids(
                        message, media_type
                    )

                    await _save_or_update_record(
                        session, name, file_id, file_unique_id
                    )
                    return file_id, file_unique_id

                except Exception as e:
                    print(f"Error creating media {name}: {e}")
                    return None, None

    except Exception as e:
        print(f"General error in _create_or_get_media for {name}: {e}")
        return None, None


# Специализированные функции с использованием универсальной
async def create_hello_mes(
    bot: Bot,
    forse: bool = False,
    name: str = "misk/hello.ogg",
    is_pdf: bool = False,
    is_video_note: bool = False,
    is_edu: bool = False,
    filename: Optional[str] = None,
    caption: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Создать или получить приветственное сообщение"""
    # Определяем тип медиа и имя файла
    if is_pdf:
        media_type = MediaType.DOCUMENT
        filename = filename
    elif is_video_note:
        media_type = MediaType.VIDEO_NOTE
        filename = None
    else:
        media_type = MediaType.VOICE
        filename = None

    return await _create_or_get_media(
        bot,
        name,
        name,
        media_type,
        forse,
        filename=filename,
        caption=caption,
    )


async def create_hello_mes_old(
    bot: Bot,
    forse=False,
    mes_name: str = "misk/usefull/ЭФИР 1 │ DESENKO.mp3",
    filename: str = "misk/usefull/ЭФИР 1 │ DESENKO.mp3",
    caption: str = "<i>🎙️Практика получения ресурсов от родителей и Рода.</i>",
):
    async with AsyncSessionLocal() as session:
        hello_mes = None
        if not forse:
            hello_mes = (
                await session.execute(
                    select(BigMes).where(BigMes.message_name == mes_name)
                )
            ).scalar_one_or_none()
            if hello_mes:
                return hello_mes.message_id
            else:
                forse = True
        if forse:
            config = get_config()
            with open(mes_name, "rb") as video_file:
                hello_mes = await bot.send_document(
                    chat_id=config.admin_ids[0],
                    document=FSInputFile(video_file.name, filename=filename),
                    caption=caption,
                )
                hello_mes_last = (
                    await session.execute(
                        select(BigMes).where(BigMes.message_name == mes_name)
                    )
                ).scalar_one_or_none()
            if hello_mes_last:
                hello_mes_last.message_id = hello_mes.message_id
            else:
                session.add(
                    BigMes(
                        message_id=hello_mes.message_id,
                        message_name=mes_name,
                    )
                )
            await session.commit()
            return hello_mes.message_id


async def create_edu_mes(
    bot: Bot,
    forse: bool = False,
    name: str = "misk/hello.ogg",
    filename: str = "Введение в моё обучение.mp3",
) -> Tuple[Optional[str], Optional[str]]:
    """Создать или получить образовательное сообщение"""
    try:
        async with AsyncSessionLocal() as session:
            # Получаем все записи с таким именем
            all_records = await _get_all_records_by_name(session, name)

            # Если не форсируем и есть ровно одна запись - возвращаем её
            if not forse and len(all_records) == 1:
                record = all_records[0]
                return str(record.message_id), record.file_unique_id

            # Иначе удаляем все старые записи
            if all_records:
                await _delete_records_by_name(session, name)

            # Создаём новую
            return await _create_or_get_media(
                bot, name, name, MediaType.AUDIO, True, filename, False
            )

    except Exception as e:
        print(f"Error in create_edu_mes: {e}")
        return None, None


async def create_pay_photo(
    bot: Bot,
    forse: bool = False,
    name: str = "misk/pay_photo.jpg",
    is_gif: bool = False,
) -> Tuple[Optional[str], Optional[str]]:
    """Создать или получить платёжное фото"""
    media_type = MediaType.ANIMATION if is_gif else MediaType.PHOTO
    return await _create_or_get_media(bot, name, name, media_type, forse)


async def create_edu_photo(
    bot: Bot, name: str, forse: bool = False
) -> Optional[str]:
    """Создать или получить образовательное фото"""
    file_path = f"{name}"
    file_id, _ = await _create_or_get_media(
        bot, name, file_path, MediaType.PHOTO, forse
    )
    return file_id


async def create_review_photo(
    bot: Bot, name: str, forse: bool = False, media_type: str = "photo"
) -> Tuple[Optional[str], Optional[str]]:
    """Создать или получить фото отзыва"""
    # Путь к файлу уже содержит расширение
    file_path = f"{name}"

    # Проверяем существование файла
    if not os.path.exists(file_path):
        # Если файл не существует, возвращаем None
        print(f"File not found: {file_path}")
        return None, None

    # Конвертируем строковый тип в enum
    media_type_enum = MediaType(media_type)

    try:
        return await _create_or_get_media(
            bot, name, file_path, media_type_enum, forse
        )
    except Exception as e:
        print(f"Error in create_review_photo: {e}")
        return None, None


async def create_education_audio(
    bot: Bot, animal: str, forse: bool = False, as_file: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """Создать или получить образовательное аудио"""
    file_path = f"misk/education/{animal}"
    media_type = MediaType.AUDIO if as_file else MediaType.VOICE
    filename = "Введение в моё обучение.ogg" if as_file else None

    return await _create_or_get_media(
        bot, animal, file_path, media_type, forse, filename
    )


# Функции-обёртки для обратной совместимости
async def get_pay_photo(
    bot: Bot, name: str, is_gif: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """Получить платёжное фото с проверкой валидности"""
    file_id, file_unique_id = await create_pay_photo(bot, False, name, is_gif)

    if file_id and file_unique_id and await is_valid_file_id(bot, file_id):
        return file_id, file_unique_id

    # Если невалидно - пересоздаём
    return await create_pay_photo(bot, True, name, is_gif)


async def get_hello_message(
    bot: Bot,
    name: str,
    is_pdf: bool = False,
    is_video_note: bool = False,
    is_edu: bool = False,
    filename: Optional[str] = None,
    caption: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Получить приветственное сообщение с проверкой валидности"""
    file_id, file_unique_id = await create_hello_mes(
        bot, False, name, is_pdf, is_video_note, is_edu, filename, caption
    )

    if file_id and file_unique_id and await is_valid_file_id(bot, file_id):
        return file_id, file_unique_id

    return await create_hello_mes(
        bot, True, name, is_pdf, is_video_note, is_edu, filename, caption
    )


async def get_edu_message(
    bot: Bot,
    name: str,
    filename: str = "Введение в моё обучение.mp3",
) -> Tuple[Optional[str], Optional[str]]:
    """Получить образовательное сообщение с проверкой валидности"""
    file_id, file_unique_id = await create_edu_mes(bot, False, name, filename)

    if file_id and file_unique_id and await is_valid_file_id(bot, file_id):
        return file_id, file_unique_id

    return await create_edu_mes(bot, True, name, filename)


async def get_education_audio(
    bot: Bot, animal: str, as_file: bool = False
) -> Optional[MediaAttachment]:
    """Получить образовательное аудио как MediaAttachment"""
    file_id, file_unique_id = await create_education_audio(
        bot, animal, False, as_file
    )

    if not file_id or not file_unique_id:
        return None

    if not await is_valid_file_id(bot, str(file_id)):
        file_id, file_unique_id = await create_education_audio(
            bot, animal, True, as_file
        )

    if file_id and file_unique_id:
        return MediaAttachment(
            file_id=MediaId(file_id, file_unique_id),
            type=ContentType.AUDIO if as_file else ContentType.VOICE,
        )
    return None


# Функции для создания MediaAttachment
async def get_pay_photo_attachment(
    bot: Bot, name: str, is_gif: bool = False
) -> Optional[MediaAttachment]:
    """Получить платёжное фото как MediaAttachment"""
    try:
        file_id, file_unique_id = await get_pay_photo(bot, name, is_gif)
        if file_id and file_unique_id:
            return MediaAttachment(
                file_id=MediaId(file_id, file_unique_id),
                type=ContentType.ANIMATION if is_gif else ContentType.PHOTO,
            )
    except Exception as e:
        print(f"Error in get_pay_photo_attachment: {e}")
    return None


async def get_hello_message_attachment(
    bot: Bot,
    name: str,
    is_pdf: bool = False,
    is_video_note: bool = False,
    is_edu: bool = False,
    filename: Optional[str] = None,
    caption: Optional[str] = None,
) -> Optional[MediaAttachment]:
    """Получить приветственное сообщение как MediaAttachment"""
    try:
        file_id, file_unique_id = await get_hello_message(
            bot, name, is_pdf, is_video_note, is_edu, filename, caption
        )
        if file_id and file_unique_id:
            if is_video_note:
                content_type = ContentType.VIDEO_NOTE
            elif is_pdf:
                content_type = ContentType.DOCUMENT
            else:
                content_type = ContentType.VOICE

            return MediaAttachment(
                file_id=MediaId(file_id, file_unique_id),
                type=content_type,
            )
    except Exception as e:
        print(f"Error in get_hello_message_attachment: {e}")
    return None


async def get_edu_message_attachment(
    bot: Bot,
    name: str,
    filename: str = "Введение в моё обучение.mp3",
) -> Optional[MediaAttachment]:
    """Получить образовательное сообщение как MediaAttachment"""
    try:
        file_id, file_unique_id = await get_edu_message(bot, name, filename)
        if file_id and file_unique_id:
            return MediaAttachment(
                file_id=MediaId(file_id, file_unique_id),
                type=ContentType.AUDIO,
            )
    except Exception as e:
        print(f"Error in get_edu_message_attachment: {e}")
    return None


async def create_media_album(
    bot: Bot,
    album_name: str,
    media_files: List[str],
    media_type: str = "photo",
    force: bool = False,
) -> List[str]:
    """Создать альбом медиафайлов"""
    async with AsyncSessionLocal() as session:
        album_record = None

        if not force:
            album_record = await _get_record_by_name(session, album_name)

            if album_record and album_record.message_id:
                try:
                    file_ids = album_record.message_id.split(",")
                    if file_ids and await is_valid_file_id(bot, file_ids[0]):
                        return file_ids
                except Exception:
                    force = True

        if force or not album_record:
            config = get_config()
            media_group = MediaGroupBuilder()

            # Добавляем файлы в медиагруппу
            for media_file in media_files:
                if media_type == "photo":
                    media_group.add_photo(media=FSInputFile(media_file))
                elif media_type == "video":
                    media_group.add_video(media=FSInputFile(media_file))
                elif media_type == "document":
                    media_group.add_document(media=FSInputFile(media_file))

            messages = await bot.send_media_group(
                chat_id=config.admin_ids[0], media=media_group.build()
            )

            # Собираем file_ids
            file_ids = []
            for msg in messages:
                if media_type == "photo" and msg.photo:
                    file_ids.append(msg.photo[-1].file_id)
                elif media_type == "video" and msg.video:
                    file_ids.append(msg.video.file_id)
                elif media_type == "document" and msg.document:
                    file_ids.append(msg.document.file_id)

            # Сохраняем как строку
            file_ids_str = ",".join(file_ids)
            await _save_or_update_record(session, album_name, file_ids_str)

            return file_ids


async def get_media_album(bot: Bot, album_name: str) -> List[dict]:
    """Получить альбом медиафайлов"""
    async with AsyncSessionLocal() as session:
        album_record = await _get_record_by_name(session, album_name)

        if not album_record or not album_record.message_id:
            return []

        file_ids = album_record.message_id.split(",")

        # Определяем тип медиа
        media_type = ContentType.PHOTO
        if "video" in album_name:
            media_type = ContentType.VIDEO
        elif "document" in album_name or "doc" in album_name:
            media_type = ContentType.DOCUMENT

        return [
            {"file_id": file_id, "type": media_type} for file_id in file_ids
        ]
