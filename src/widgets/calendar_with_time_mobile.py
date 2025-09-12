"""
Мобильно-оптимизированная версия CalendarWithTime
"""

from typing import Optional

from aiogram.types import InlineKeyboardButton
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.text import Format

from widgets.calendar_with_time import (
    CalendarTimeView,
    CalendarWithTime,
)


class MobileTimeView(CalendarTimeView):
    """Оптимизированный для мобильных устройств view выбора времени"""

    async def _render_hours(
        self,
        data: dict,
        manager: DialogManager,
        selected_hour: Optional[int] = None,
    ) -> list[list[InlineKeyboardButton]]:
        """Рендерим часы от 00 до 23, по 4 в ряд"""
        keyboard = []
        row = []
        for hour in range(24):
            row.append(
                await self._render_hour_button(
                    hour, selected_hour, data, manager
                )
            )
            if len(row) == 4:
                keyboard.append(row)
                row = []
        return keyboard


class MobileCalendarWithTime(CalendarWithTime):
    """Мобильно-оптимизированный календарь с выбором времени"""

    def _init_views(self):
        """Используем мобильно-оптимизированный TimeView"""
        views = super()._init_views()
        # Заменяем стандартный TimeView на мобильный
        from widgets.calendar_with_time import CalendarTimeScope

        views[CalendarTimeScope.TIME] = MobileTimeView(
            self._item_callback_data,
            hour_text=Format("{hour:02d}:00"),
            selected_hour_text=Format("✅ {hour:02d}:00"),
            header_text=Format("📅 {date:%d.%m.%Y}\n🕐 Выберите время:"),
            back_text=Format("◀️ Изменить дату"),
        )
        return views


# Альтернативный компактный вариант с популярными временными слотами
class QuickTimeView(CalendarTimeView):
    """View с быстрым выбором популярных временных слотов"""

    def __init__(self, *args, popular_hours=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Популярные часы по умолчанию
        self.popular_hours = popular_hours or [
            9,
            10,
            11,
            14,
            15,
            16,
            17,
            18,
            19,
        ]

    async def _render_hours(
        self,
        data: dict,
        manager: DialogManager,
        selected_hour: Optional[int] = None,
    ) -> list[list[InlineKeyboardButton]]:
        """Рендерим только популярные часы + кнопка "Все часы" """
        keyboard = []

        # Популярные часы
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="⭐ Популярное время", callback_data=""
                )
            ]
        )

        row = []
        for hour in self.popular_hours:
            row.append(
                await self._render_hour_button(
                    hour, selected_hour, data, manager
                )
            )
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        # Кнопка для показа всех часов
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="🕐 Показать все часы",
                    callback_data=self.callback_generator("SHOW_ALL_HOURS"),
                )
            ]
        )

        return keyboard


class QuickCalendarWithTime(CalendarWithTime):
    """Календарь с быстрым выбором популярных временных слотов"""

    def __init__(self, *args, popular_hours=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.popular_hours = popular_hours
        self.show_all_hours = False

    def _init_views(self):
        """Используем QuickTimeView или стандартный в зависимости от режима"""
        views = super()._init_views()
        from widgets.calendar_with_time import CalendarTimeScope

        if not self.show_all_hours:
            views[CalendarTimeScope.TIME] = QuickTimeView(
                self._item_callback_data,
                popular_hours=self.popular_hours,
                hour_text=Format("{hour:02d}:00"),
                selected_hour_text=Format("✅ {hour:02d}:00"),
                header_text=Format("📅 {date:%d.%m.%Y}"),
            )
        return views

    async def _process_item_callback(self, callback, data, dialog, manager):
        """Обработка кнопки показа всех часов"""
        if data == "SHOW_ALL_HOURS":
            self.show_all_hours = True
            # Перерисовываем виджет
            self._init_views()
            return True

        return await super()._process_item_callback(
            callback, data, dialog, manager
        )
