from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

from aiogram import Bot
from kerykeion import (
    AstrologicalSubject,
    EphemerisDataFactory,
    KerykeionChartSVG,
    TransitsTimeRangeFactory,
)

try:
    import pytz
    from timezonefinder import TimezoneFinder

    TIMEZONEFINDER_AVAILABLE = True
except ImportError:
    TIMEZONEFINDER_AVAILABLE = False
    TimezoneFinder = None


class AstroManager:
    """
    Класс-обёртка над Kerykeion.
    Содержит натальную карту субъекта и
    выдаёт SVG/JSON/транзиты по запросу.
    """

    def __init__(
        self,
        bot: Bot,
        *,
        tz_str: str = "Europe/Moscow",
        houses_system: str = "P",
        perspective_type: str = "Apparent Geocentric",
        zodiac_type: str = "Tropic",
        output_dir: Path | str | None = None,
    ) -> None:
        self.bot = bot

        # Где сохранять SVG; по умолчанию — ./charts
        self.output_dir = Path(output_dir or "./charts").expanduser()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.tz_str = tz_str
        self.houses_system = houses_system
        self.perspective_type = perspective_type
        self.zodiac_type = zodiac_type

        # Инициализируем TimezoneFinder если доступен
        self.tf = TimezoneFinder() if TIMEZONEFINDER_AVAILABLE else None

    # self.subject = AstrologicalSubject(
    # self.name=name,
    # self.year=year,
    # self.month=month,
    # self.day=day,
    # self.hour=hour,
    # self.minute=minute,
    # self.lng=lng,
    # self.lat=lat,
    #  self.start_point = start_point
    #         self.left_hand_orientation = left_hand_orientation
    #         self.show_aspect_symbols = show_aspect_symbols
    #         self.show_configurations = show_configurations
    #         # )
    # self.plane = plane
    #         self.apparent = apparent
    # self.polar_houses_system = polar_houses_system
    #         self.horary_houses_system = horary_houses_system
    # ---------- SUBJECT ----------
    def get_subject(
        self,
        name: str,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        lng: float,
        lat: float,
        city: str,
        time_is_msk: bool = False,  # Флаг что время введено в МСК
        # country: str,
    ) -> AstrologicalSubject:
        """
        Создает астрологический субъект.

        Args:
            time_is_msk: Если True, переданное время считается московским и конвертируется
                        в местное время места рождения. Если False (по умолчанию),
                        время используется как местное время места рождения.
        """

        # Определяем часовой пояс места рождения
        local_timezone = self.get_timezone_by_coordinates(lat, lng)

        # Конвертируем время если оно в МСК
        if time_is_msk:
            local_year, local_month, local_day, local_hour, local_minute = (
                self.convert_msk_to_local_time(
                    year, month, day, hour, minute, local_timezone
                )
            )

            print(
                f"Конвертация времени: {hour:02d}:{minute:02d} МСК -> "
                f"{local_hour:02d}:{local_minute:02d} {local_timezone}"
            )
        else:
            local_year, local_month, local_day, local_hour, local_minute = (
                year,
                month,
                day,
                hour,
                minute,
            )

        subject = AstrologicalSubject(
            name=name,
            year=local_year,
            month=local_month,
            day=local_day,
            hour=local_hour,
            minute=local_minute,
            lng=lng,
            lat=lat,
            city=city,
            # country=country,
            tz_str=local_timezone,  # Используем местный часовой пояс
            houses_system_identifier=self.houses_system,
            perspective_type=self.perspective_type,
            zodiac_type=self.zodiac_type,
            online=False,  # У нас уже есть координаты и timezone
        )

        return subject

    # ---------- SVG ----------
    def get_svg(
        self,
        theme: str = "dark",
        file_name: Optional[str] = None,
        user_id: int = 0,
        subject: AstrologicalSubject | None = None,
    ) -> Path:
        """
        Генерирует красивый SVG-файл натальной карты и
        возвращает полный путь к нему.
        """
        file_name = file_name or f"{user_id}.svg"
        output_path = self.output_dir / file_name

        chart_svg = KerykeionChartSVG(
            subject,
            new_output_directory=str(self.output_dir),
            theme=theme,
            chart_language="RU",
        )

        svg_content = chart_svg.makeTemplate()
        # svg_content = chart_svg.makeTemplate(remove_css_variables=True)
        with output_path.open("w", encoding="utf-8") as fp:
            fp.write(svg_content)

        return output_path

    # ---------- JSON (radix) ----------
    def get_natal_json(
        self,
        *,
        indent: int = 2,
        compact: bool = False,
        subject: AstrologicalSubject | None = None,
    ) -> Dict[str, Any]:
        """
        Возвращает dict с полной структурой радикса.
        """
        return subject.json(
            dump=False,
            indent=indent,
            # compact=compact,
        )

    # ---------- JSON (transits) ----------
    def get_transits_json(
        self,
        *,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
        step_days: int = 1,
        indent: int = 2,
        subject: AstrologicalSubject | None = None,
    ) -> Dict[str, Any]:
        """
        Вычисляет транзиты к натальной карте
        за указанный период (по умолчанию 30 дней, начиная
        с сегодня) и возвращает их в формате dict.
        """
        start_datetime = start_datetime or datetime.now()
        end_datetime = end_datetime or (start_datetime + timedelta(days=30))

        ephemeris_factory = EphemerisDataFactory(
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            step_type="days",
            step=step_days,
            lat=subject.lat,
            lng=subject.lng,
            tz_str=subject.tz_str,
        )
        ephemeris_points = (
            ephemeris_factory.get_ephemeris_data_as_astrological_subjects()
        )

        trx_factory = TransitsTimeRangeFactory(
            natal_subject=subject,
            transit_subjects=ephemeris_points,
        )
        trx_model = trx_factory.get_transits_time_range_model()
        return trx_model.json(dump=False, indent=indent)

    # ---------- JSON (full) ----------
    def get_full_json(
        self,
        *,
        start_datetime: datetime | None = None,
        end_datetime: datetime | None = None,
        step_days: int = 1,
        indent: int = 2,
        subject: AstrologicalSubject | None = None,
    ) -> Dict[str, Any]:
        """
        Объединяет радикс и транзиты в один словарь.
        """
        return {
            "natal": self.get_natal_json(indent=indent, subject=subject),
            "transits": self.get_transits_json(
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                step_days=step_days,
                indent=indent,
                subject=subject,
            ),
        }

    def get_timezone_by_coordinates(self, lat: float, lng: float) -> str:
        """
        Определяет часовой пояс по координатам.
        Если timezonefinder недоступен, возвращает Europe/Moscow.
        """
        if self.tf is None:
            return "Europe/Moscow"

        try:
            timezone_name = self.tf.timezone_at(lat=lat, lng=lng)
            return timezone_name or "Europe/Moscow"
        except Exception:
            return "Europe/Moscow"

    def convert_msk_to_local_time(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        local_timezone: str,
    ) -> tuple[int, int, int, int, int]:
        """
        Конвертирует время из МСК в местное время места рождения.

        Args:
            year, month, day, hour, minute: Дата и время в МСК
            local_timezone: Часовой пояс места рождения

        Returns:
            tuple: (year, month, day, hour, minute) в местном времени
        """
        try:
            # Создаем datetime в МСК
            msk_tz = pytz.timezone("Europe/Moscow")
            local_tz = pytz.timezone(local_timezone)

            # Создаем naive datetime и локализуем его в МСК
            msk_time = datetime(year, month, day, hour, minute)
            msk_localized = msk_tz.localize(msk_time)

            # Конвертируем в местное время
            local_time = msk_localized.astimezone(local_tz)

            return (
                local_time.year,
                local_time.month,
                local_time.day,
                local_time.hour,
                local_time.minute,
            )
        except Exception as e:
            print(f"Ошибка конвертации времени: {e}")
            # В случае ошибки возвращаем исходное время
            return (year, month, day, hour, minute)


# from aiogram import Bot
# from kerykeion import AstrologicalSubject, KerykeionChartSVG


# class Astromanager:
#     bot: Bot

#     def __init__(self, bot):
#         self.bot = bot


# subject = AstrologicalSubject(
#     name="Test",
#     year=1999,
#     month=4,
#     day=8,
#     hour=6,
#     minute=0,
#     lng=58.56,
#     lat=51.23,
#     tz_str="Asia/Yekaterinburg",
#     houses_system="P",  # Placidus
#     polar_houses_system="EQU_M_C",  # Equal-MC above Polar Circle
#     horary_houses_system="R",  # Regiomontanus
#     perspective_type="Geocentric",
#     plane="Ecliptic",
#     apparent=True,  # видимые координаты
#     zodiac_type="Tropical",
#     start_point="Asc",
#     left_hand_orientation=True,
#     show_aspect_symbols=True,
#     show_configurations=True,
# )

# svg = KerykeionChartSVG(subject, theme="classic")
# svg.makeSVG()  # получаете готовый файл wheel.svg

# # ➜ Получаем Python-dict с полной структурой
# data = subject.json(dump=False, indent=2)

# # ➜ или сразу сохраняем на диск:
# subject.json(dump=True, indent=2, path="demo_chart.json")  # ← запишет в файл

# ///////////////////////////////////////////////////////////////////////////////////////
# from flatlib import const
# chart = Chart(date, pos, hsys=const.HOUSES_REGIOMONTANUS)
# ``` :contentReference[oaicite:3]{index=3}

# ---

# ### 🧪 Пример использования

# ```python
# from flatlib.chart import Chart
# from flatlib.datetime import Datetime
# from flatlib.geopos import GeoPos
# from flatlib import const

# # Заданные тобой: 14.06.2025 19:59 (Санкт‑Петербург UTC+3)
# date = Datetime('2025/06/14', '19:59', '+03:00')
# pos = GeoPos('59n56', '30e18')

# chart = Chart(date, pos, hsys=const.HOUSES_REGIOMONTANUS, IDs=const.LIST_OBJECTS)

# # Доступ к домам и планетам
# for i in range(1,13):
#     house = chart.get(const.HOUSE_NAMES[i-1])
#     print(f"Дом {i}: {house.sign} {house.lon:.2f}°")

# sun = chart.get(const.SUN)
# print("Солнце в", sun.sign, f"{sun.lon:.2f}°")


# | Параметр                  | Значение                   |
# | ------------------------- | -------------------------- |
# | Город                     | Санкт-Петербург, RU        |
# | Система домов             | Плацидус                   |
# | Система домов за полярьем | Равнодомная от MC          |
# | Система хорара            | Региомонтанус              |
# | Центр координат           | Геоцентрическая система    |
# | Плоскость                 | Эклиптика                  |
# | Позиция планет            | Видимая                    |
# | Аянсамса                  | Тропическая (без аянсамсы) |
# | Точка отсчета             | Асцендент                  |
# | Левосторонний зодиак      | Включено                   |
# | Символы аспектов          | Включено                   |
# | Пропорциональные дома     | Отключено                  |
# | Конфигурации аспектов     | Включено                   |

# Пример использования конвертации времени:
# if __name__ == "__main__":
#     # Пример: пользователь ввел время 15:00 МСК для рождения в Новосибирске
#     astro_manager = AstroManager(bot=None)
#
#     # Координаты Новосибирска
#     lat, lng = 55.0084, 82.9357
#
#     # Определяем часовой пояс
#     timezone = astro_manager.get_timezone_by_coordinates(lat, lng)
#     print(f"Часовой пояс Новосибирска: {timezone}")
#
#     # Конвертируем 15:00 МСК в местное время
#     local_time = astro_manager.convert_msk_to_local_time(
#         2000, 1, 1, 15, 0, timezone
#     )
#     print(f"15:00 МСК = {local_time[3]:02d}:{local_time[4]:02d} местного времени")
#
#     # Создаем субъекта (время автоматически конвертируется)
#     subject = astro_manager.get_subject(
#         name="Тест",
#         year=2000, month=1, day=1,
#         hour=15, minute=0,  # Время в МСК
#         lng=lng, lat=lat,
#         city="Новосибирск",
#         time_is_msk=True  # Указываем что время в МСК
#     )
