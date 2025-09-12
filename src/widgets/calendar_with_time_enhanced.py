"""
Расширенная версия CalendarWithTime с дополнительными функциями
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.text import Format, Text

from widgets.calendar_with_time import (
    CalendarScope,
    CalendarTimeScope,
    CalendarTimeView,
    CalendarWithTime,
)

# Константы для навигации
CALLBACK_BACK_TO_CALENDAR = "BACK_CAL"
BACK_TO_CALENDAR_TEXT = Format("◀️ Вернуться назад")


class EnhancedTimeView(CalendarTimeView):
    """Улучшенный view для выбора времени с дополнительными возможностями"""

    def __init__(
        self,
        callback_generator,
        hour_text=None,
        selected_hour_text=None,
        header_text=None,
        back_text: Text = BACK_TO_CALENDAR_TEXT,
        hour_range: Optional[Tuple[int, int]] = None,  # (start_hour, end_hour)
        disabled_hours: Optional[List[int]] = None,
    ):
        super().__init__(
            callback_generator,
            hour_text or Format("{hour:02d}:00"),
            selected_hour_text or Format("[ {hour:02d}:00 ]"),
            header_text or Format("🕐 Выберите время для {date:%d.%m.%Y}"),
        )
        self.back_text = back_text
        self.hour_range = hour_range or (0, 23)
        self.disabled_hours = disabled_hours or []

    async def _render_hour_button(
        self,
        hour: int,
        selected_hour: Optional[int],
        data: dict,
        manager: DialogManager,
    ) -> InlineKeyboardButton:
        """Рендерим кнопку часа с учетом доступности"""
        # Проверяем, доступен ли этот час
        start_hour, end_hour = self.hour_range
        if hour < start_hour or hour > end_hour or hour in self.disabled_hours:
            # Недоступный час - пустая кнопка
            return InlineKeyboardButton(text="—", callback_data="")

        return await super()._render_hour_button(
            hour, selected_hour, data, manager
        )

    async def _render_back_button(
        self,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        """Кнопка возврата к календарю"""
        return [
            InlineKeyboardButton(
                text=await self.back_text.render_text(data, manager),
                callback_data=self.callback_generator(
                    CALLBACK_BACK_TO_CALENDAR
                ),
            )
        ]

    async def render(
        self,
        selected_date: date,
        data: dict,
        manager: DialogManager,
        selected_hour: Optional[int] = None,
    ) -> list[list[InlineKeyboardButton]]:
        """Рендерим с кнопкой назад"""
        keyboard = await super().render(
            selected_date, data, manager, selected_hour
        )
        # Добавляем кнопку назад
        keyboard.append(await self._render_back_button(data, manager))
        return keyboard


class CalendarWithTimeEnhanced(CalendarWithTime):
    """Расширенный календарь с дополнительными настройками времени"""

    def __init__(
        self,
        id: str,
        on_click=None,
        config=None,
        when=None,
        hour_range: Optional[Tuple[int, int]] = None,
        disabled_hours: Optional[List[int]] = None,
        show_current_selection: bool = True,
    ):
        super().__init__(id, on_click, config, when)
        self.hour_range = hour_range
        self.disabled_hours = disabled_hours
        self.show_current_selection = show_current_selection

    def _init_views(self):
        """Инициализируем views с расширенным TimeView"""
        views = super()._init_views()
        # Заменяем стандартный TimeView на расширенный
        views[CalendarTimeScope.TIME] = EnhancedTimeView(
            self._item_callback_data,
            hour_range=self.hour_range,
            disabled_hours=self.disabled_hours,
        )
        return views

    async def _handle_back_to_calendar(
        self, data: str, manager: DialogManager
    ):
        """Обработка возврата к календарю"""
        # Очищаем выбранную дату
        widget_data = self.get_widget_data(manager, {})
        widget_data.pop("selected_date", None)
        widget_data.pop("selected_hour", None)

        # Возвращаемся к календарю
        self.set_scope(CalendarScope.DAYS, manager)

    async def _process_item_callback(
        self,
        callback,
        data: str,
        dialog,
        manager: DialogManager,
    ) -> bool:
        """Расширяем обработку для кнопки назад"""
        if data == CALLBACK_BACK_TO_CALENDAR:
            await self._handle_back_to_calendar(data, manager)
            return True

        return await super()._process_item_callback(
            callback, data, dialog, manager
        )


# Пример использования с бизнес-логикой
class BusinessHoursCalendar(CalendarWithTimeEnhanced):
    """Календарь только для рабочих часов"""

    def __init__(self, id: str, on_click=None, config=None, when=None):
        # Рабочие часы с 9 до 18, обед с 13 до 14
        super().__init__(
            id=id,
            on_click=on_click,
            config=config,
            when=when,
            hour_range=(9, 18),
            disabled_hours=[13],  # Обеденный перерыв
        )

    async def _get_disabled_hours_for_date(
        self, selected_date: date, manager: DialogManager
    ) -> List[int]:
        """Получить занятые часы для конкретной даты"""
        # Здесь можно загрузить из БД занятые слоты
        # Пример: проверяем выходные
        if selected_date.weekday() in [5, 6]:  # Суббота, воскресенье
            return list(range(24))  # Все часы недоступны

        # Загружаем занятые слоты из БД
        # booked_hours = await get_booked_hours(selected_date)
        booked_hours = [10, 11, 15]  # Пример

        return [13] + booked_hours  # Обед + занятые часы


# Пример с динамической проверкой доступности
async def smart_datetime_handler(
    c: CallbackQuery,
    widget: CalendarWithTimeEnhanced,
    manager: DialogManager,
    selected_datetime: datetime,
):
    """Умный обработчик с проверкой доступности"""

    # Проверяем доступность в реальном времени
    # is_available = await check_slot_availability(selected_datetime)

    # Пример: проверка на минимальное время бронирования (2 часа вперед)
    min_booking_time = datetime.now() + timedelta(hours=2)
    if selected_datetime < min_booking_time:
        await c.answer(
            "❌ Бронирование возможно минимум за 2 часа", show_alert=True
        )
        return

    # Сохраняем выбор
    manager.dialog_data["selected_datetime"] = selected_datetime

    await c.answer(
        f"✅ Выбрано: {selected_datetime.strftime('%d.%m.%Y в %H:00')}"
    )

    # Переходим к подтверждению
    await manager.next()
