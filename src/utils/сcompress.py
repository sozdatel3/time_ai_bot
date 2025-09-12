import os
import shutil
import tempfile

from PIL import Image

# Max photo size for Telegram in bytes (10 MB)
TELEGRAM_MAX_PHOTO_SIZE = 10 * 1024 * 1024


async def compress_png(
    input_path: str, output_path: str, quality: int = 95, optimize: bool = True
) -> bool:
    """
    Сжимает PNG изображение с сохранением максимального качества.
    Сжатие применяется только если файл больше 10 МБ.

    Args:
        input_path: Путь к исходному PNG файлу.
        output_path: Путь для сохранения сжатого файла.
        quality: Качество сжатия (0-100). По умолчанию 95 для сохранения качества.
        optimize: Включить ли оптимизацию.

    Returns:
        True, если сжатие успешно, иначе False.
    """
    try:
        original_size = os.path.getsize(input_path)

        # Если файл меньше 10 МБ, просто копируем его
        if original_size <= TELEGRAM_MAX_PHOTO_SIZE:
            if input_path != output_path:
                shutil.copy2(input_path, output_path)
            print(
                f"File {input_path} is already under 10MB ({original_size} bytes), no compression needed."
            )
            return True

        print(
            f"File {input_path} is {original_size} bytes, attempting quality-preserving compression..."
        )

        with Image.open(input_path) as img:
            # Сохраняем информацию о прозрачности
            has_transparency = img.mode in ("RGBA", "LA") or (
                img.mode == "P" and "transparency" in img.info
            )

            # Стратегия 1: Попробуем простую PNG оптимизацию без изменения качества
            temp_fd, temp_path = tempfile.mkstemp(suffix=".png")
            try:
                os.close(temp_fd)

                # Сначала пробуем сохранить с максимальной оптимизацией без изменений
                save_kwargs = {
                    "format": "PNG",
                    "optimize": True,
                    "compress_level": 9,  # Максимальное сжатие
                }

                # Сохраняем оригинальное изображение без изменений
                img_copy = img.copy()
                img_copy.save(temp_path, **save_kwargs)
                optimized_size = os.path.getsize(temp_path)

                if optimized_size <= TELEGRAM_MAX_PHOTO_SIZE:
                    shutil.move(temp_path, output_path)
                    print(
                        f"Successfully compressed with PNG optimization only. "
                        f"Original: {original_size} bytes, New: {optimized_size} bytes "
                        f"({100 - (optimized_size * 100 // original_size)}% reduction)"
                    )
                    return True

                # Стратегия 2: Немного уменьшаем размер изображения (сохраняя 90% от оригинала)
                if img.width > 3000 or img.height > 3000:
                    scale_factor = 0.9
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    img_resized = img.resize(
                        (new_width, new_height), Image.Resampling.LANCZOS
                    )

                    img_resized.save(temp_path, **save_kwargs)
                    resized_size = os.path.getsize(temp_path)

                    if resized_size <= TELEGRAM_MAX_PHOTO_SIZE:
                        shutil.move(temp_path, output_path)
                        print(
                            f"Successfully compressed with minimal resize (90%). "
                            f"Original: {original_size} bytes, New: {resized_size} bytes"
                        )
                        return True

                    # Используем уменьшенное изображение для дальнейших операций
                    img = img_resized

                # Стратегия 3: Уменьшаем до максимального размера для высокого качества
                max_dimension = 4096  # Высокое разрешение
                if img.width > max_dimension or img.height > max_dimension:
                    img.thumbnail(
                        (max_dimension, max_dimension),
                        Image.Resampling.LANCZOS,
                    )
                    img.save(temp_path, **save_kwargs)
                    thumbnail_size = os.path.getsize(temp_path)

                    if thumbnail_size <= TELEGRAM_MAX_PHOTO_SIZE:
                        shutil.move(temp_path, output_path)
                        print(
                            f"Successfully compressed with resize to {max_dimension}px. "
                            f"Original: {original_size} bytes, New: {thumbnail_size} bytes"
                        )
                        return True

                # Стратегия 4: Если нет прозрачности, конвертируем в высококачественный JPEG
                if not has_transparency:
                    if img.mode == "RGBA":
                        # Создаем белый фон для прозрачных областей
                        background = Image.new(
                            "RGB", img.size, (255, 255, 255)
                        )
                        background.paste(img, mask=img.split()[3])
                        img = background
                    elif img.mode != "RGB":
                        img = img.convert("RGB")

                    # Сохраняем как JPEG с очень высоким качеством
                    jpeg_path = output_path.replace(".png", ".jpg")
                    img.save(
                        jpeg_path,
                        format="JPEG",
                        quality=quality,
                        optimize=True,
                        subsampling=0,
                    )
                    jpeg_size = os.path.getsize(jpeg_path)

                    if jpeg_size <= TELEGRAM_MAX_PHOTO_SIZE:
                        print(
                            f"Converted to high-quality JPEG (quality={quality}). "
                            f"Original: {original_size} bytes, JPEG: {jpeg_size} bytes"
                        )
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        return True
                    else:
                        # Если JPEG все еще большой, пробуем качество 90
                        img.save(
                            jpeg_path,
                            format="JPEG",
                            quality=90,
                            optimize=True,
                            subsampling=0,
                        )
                        jpeg_size = os.path.getsize(jpeg_path)

                        if jpeg_size <= TELEGRAM_MAX_PHOTO_SIZE:
                            print(
                                f"Converted to JPEG with quality=90. "
                                f"Original: {original_size} bytes, JPEG: {jpeg_size} bytes"
                            )
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            return True
                        else:
                            os.remove(jpeg_path)

                # Стратегия 5: Последняя попытка - уменьшаем до 3000px с PNG
                if img.width > 3000 or img.height > 3000:
                    img.thumbnail((3000, 3000), Image.Resampling.LANCZOS)
                    img.save(temp_path, **save_kwargs)
                    final_size = os.path.getsize(temp_path)

                    if final_size <= TELEGRAM_MAX_PHOTO_SIZE:
                        shutil.move(temp_path, output_path)
                        print(
                            f"Successfully compressed with resize to 3000px. "
                            f"Original: {original_size} bytes, New: {final_size} bytes"
                        )
                        return True

                # Если ничего не помогло
                print(
                    f"Warning: Could not compress {input_path} below 10MB while maintaining quality. "
                    f"File size: {original_size} bytes"
                )
                if input_path != output_path:
                    shutil.copy2(input_path, output_path)
                return False

            finally:
                # Удаляем временный файл, если он остался
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    except Exception as e:
        print(f"Error compressing PNG {input_path}: {e}")
        # Если произошла ошибка и пути разные, пытаемся скопировать оригинал
        if input_path != output_path:
            try:
                shutil.copy2(input_path, output_path)
            except:
                pass
        return False
