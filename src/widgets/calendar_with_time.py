from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Optional, Protocol, Union

from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram_dialog.api.entities import ChatEvent
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    Calendar,
    CalendarConfig,
    CalendarScope,
    ManagedCalendar,
    date_from_raw,
)
from aiogram_dialog.widgets.text import Format, Text
from aiogram_dialog.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)

# Новые константы для времени
CALLBACK_SCOPE_TIME = "TIME"
CALLBACK_PREFIX_HOUR = "HOUR"
CALLBACK_BACK_TO_DATE = "BACK_DATE"
HOURS_HEADER_TEXT = Format("🕐 Выберите час для {date:%d.%m.%Y}")
HOUR_TEXT = Format("{hour:02d}:00")
SELECTED_HOUR_TEXT = Format("[ {hour:02d}:00 ]")
BACK_TO_DATE_TEXT = Format("◀️ Вернуться назад")


class CalendarTimeScope(Enum):
    """Расширенные scope для календаря с временем"""

    DAYS = "DAYS"
    MONTHS = "MONTHS"
    YEARS = "YEARS"
    TIME = "TIME"  # Новый scope для выбора времени


class OnDateTimeSelected(Protocol):
    """Протокол для обработки выбора даты и времени"""

    async def __call__(
        self,
        event: ChatEvent,
        widget: ManagedCalendarWithTime,
        dialog_manager: DialogManager,
        selected_datetime: datetime,
        /,
    ) -> Any:
        raise NotImplementedError


class CalendarTimeView:
    """View для отображения выбора времени"""

    def __init__(
        self,
        callback_generator: Callable[[str], str],
        hour_text: Text = HOUR_TEXT,
        selected_hour_text: Text = SELECTED_HOUR_TEXT,
        header_text: Text = HOURS_HEADER_TEXT,
        back_text: Text = BACK_TO_DATE_TEXT,
    ):
        self.callback_generator = callback_generator
        self.hour_text = hour_text
        self.selected_hour_text = selected_hour_text
        self.header_text = header_text
        self.back_text = back_text

    async def _render_hour_button(
        self,
        hour: int,
        selected_hour: Optional[int],
        data: dict,
        manager: DialogManager,
    ) -> InlineKeyboardButton:
        hour_data = {
            "hour": hour,
            "data": data,
        }

        if hour == selected_hour:
            text = self.selected_hour_text
        else:
            text = self.hour_text

        return InlineKeyboardButton(
            text=await text.render_text(hour_data, manager),
            callback_data=self.callback_generator(
                f"{CALLBACK_PREFIX_HOUR}{hour}"
            ),
        )

    async def _render_hours(
        self,
        data: dict,
        manager: DialogManager,
        selected_hour: Optional[int] = None,
    ) -> list[list[InlineKeyboardButton]]:
        """Рендерим кнопки с часами в формате 3x8 для лучшего отображения"""
        keyboard = []

        # Группируем часы по 3 в ряд для лучшего отображения на мобильных
        for row_start in range(0, 24, 3):
            row = []
            for col in range(3):
                hour = row_start + col
                if hour < 24:
                    row.append(
                        await self._render_hour_button(
                            hour, selected_hour, data, manager
                        )
                    )
            if row:
                keyboard.append(row)

        return keyboard

    async def _render_header(
        self,
        selected_date: date,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        header_data = {
            "date": selected_date,
            "data": data,
        }
        return [
            InlineKeyboardButton(
                text=await self.header_text.render_text(header_data, manager),
                callback_data="",
            )
        ]

    async def _render_back_button(
        self,
        data: dict,
        manager: DialogManager,
    ) -> list[InlineKeyboardButton]:
        """Кнопка возврата к выбору даты"""
        return [
            InlineKeyboardButton(
                text=await self.back_text.render_text(data, manager),
                callback_data=self.callback_generator(CALLBACK_BACK_TO_DATE),
            )
        ]

    async def render(
        self,
        selected_date: date,
        data: dict,
        manager: DialogManager,
        selected_hour: Optional[int] = None,
    ) -> list[list[InlineKeyboardButton]]:
        return [
            await self._render_header(selected_date, data, manager),
            *await self._render_hours(data, manager, selected_hour),
            await self._render_back_button(data, manager),
        ]


class CalendarWithTime(Calendar):
    """Календарь с возможностью выбора времени (часов)"""

    def __init__(
        self,
        id: str,
        on_click: Union[OnDateTimeSelected, WidgetEventProcessor, None] = None,
        config: Optional[CalendarConfig] = None,
        when: WhenCondition = None,
    ) -> None:
        # Не вызываем super().__init__ с on_click, так как мы переопределяем логику
        super().__init__(
            id=id,
            on_click=None,  # Передаем None, так как будем обрабатывать сами
            config=config,
            when=when,
        )
        # Сохраняем обработчик для финального выбора даты и времени
        self.on_datetime_selected = ensure_event_processor(on_click)

        # Добавляем обработчик для кнопки "Назад"
        self._handlers[CALLBACK_BACK_TO_DATE] = self._handle_back_to_date

    def _init_views(self) -> dict[CalendarScope, Any]:
        """Инициализируем views включая новый TimeView"""
        views = super()._init_views()
        # Добавляем view для выбора времени
        views[CalendarTimeScope.TIME] = CalendarTimeView(
            self._item_callback_data
        )
        return views

    def get_scope(
        self, manager: DialogManager
    ) -> Union[CalendarScope, CalendarTimeScope]:
        """Переопределяем для поддержки TIME scope"""
        calendar_data = self.get_widget_data(manager, {})
        current_scope = calendar_data.get("current_scope")

        if current_scope == CalendarTimeScope.TIME.value:
            return CalendarTimeScope.TIME

        # Для остальных используем родительский метод
        return super().get_scope(manager)

    def set_scope(
        self,
        new_scope: Union[CalendarScope, CalendarTimeScope],
        manager: DialogManager,
    ) -> None:
        """Устанавливаем scope с поддержкой TIME"""
        data = self.get_widget_data(manager, {})
        if isinstance(new_scope, CalendarTimeScope):
            data["current_scope"] = new_scope.value
        else:
            data["current_scope"] = new_scope.value

    def get_selected_date(self, manager: DialogManager) -> Optional[date]:
        """Получаем выбранную дату"""
        data = self.get_widget_data(manager, {})
        selected_date_str = data.get("selected_date")
        if selected_date_str:
            return date.fromisoformat(selected_date_str)
        return None

    def set_selected_date(
        self, selected_date: date, manager: DialogManager
    ) -> None:
        """Сохраняем выбранную дату"""
        data = self.get_widget_data(manager, {})
        data["selected_date"] = selected_date.isoformat()

    def get_selected_hour(self, manager: DialogManager) -> Optional[int]:
        """Получаем выбранный час"""
        data = self.get_widget_data(manager, {})
        return data.get("selected_hour")

    def set_selected_hour(self, hour: int, manager: DialogManager) -> None:
        """Сохраняем выбранный час"""
        data = self.get_widget_data(manager, {})
        data["selected_hour"] = hour

    async def _render_keyboard(self, data, manager: DialogManager):
        """Переопределяем рендеринг для поддержки TIME scope"""
        scope = self.get_scope(manager)

        if scope == CalendarTimeScope.TIME:
            # Рендерим выбор времени
            view = self.views[CalendarTimeScope.TIME]
            selected_date = self.get_selected_date(manager)
            selected_hour = self.get_selected_hour(manager)

            if selected_date:
                return await view.render(
                    selected_date, data, manager, selected_hour
                )
            else:
                # Если дата не выбрана, возвращаемся к календарю
                self.set_scope(CalendarScope.DAYS, manager)
                return await super()._render_keyboard(data, manager)
        else:
            # Для остальных scope используем родительский метод
            return await super()._render_keyboard(data, manager)

    async def _handle_click_date(
        self, data: str, manager: DialogManager
    ) -> None:
        """Переопределяем обработку клика по дате"""
        selected_date = date_from_raw(int(data))

        # Сохраняем выбранную дату
        self.set_selected_date(selected_date, manager)

        # Переключаемся на выбор времени
        self.set_scope(CalendarTimeScope.TIME, manager)

    async def _handle_click_hour(
        self, data: str, manager: DialogManager
    ) -> None:
        """Обработка выбора часа"""
        hour = int(data[len(CALLBACK_PREFIX_HOUR) :])
        selected_date = self.get_selected_date(manager)

        if selected_date:
            # Создаем datetime объект
            selected_time = time(hour=hour, minute=0, second=0)
            selected_datetime = datetime.combine(selected_date, selected_time)

            # Сохраняем выбранный час
            self.set_selected_hour(hour, manager)

            # Вызываем обработчик
            await self.on_datetime_selected.process_event(
                manager.event,
                self.managed(manager),
                manager,
                selected_datetime,
            )

    async def _handle_back_to_date(
        self, data: str, manager: DialogManager
    ) -> None:
        """Обработка возврата к выбору даты"""
        # Очищаем выбранную дату и час
        widget_data = self.get_widget_data(manager, {})
        widget_data.pop("selected_date", None)
        widget_data.pop("selected_hour", None)

        # Возвращаемся к календарю
        self.set_scope(CalendarScope.DAYS, manager)

    async def _process_item_callback(
        self,
        callback: CallbackQuery,
        data: str,
        dialog,
        manager: DialogManager,
    ) -> bool:
        """Расширяем обработку callback для поддержки выбора времени"""
        if data.startswith(CALLBACK_PREFIX_HOUR):
            await self._handle_click_hour(data, manager)
            return True
        elif data == CALLBACK_BACK_TO_DATE:
            await self._handle_back_to_date(data, manager)
            return True

        # Для остальных используем родительский метод
        return await super()._process_item_callback(
            callback, data, dialog, manager
        )

    def managed(self, manager: DialogManager) -> ManagedCalendarWithTime:
        """Возвращаем расширенный managed виджет"""
        return ManagedCalendarWithTime(self, manager)


class ManagedCalendarWithTime(ManagedCalendar):
    """Расширенный managed календарь с поддержкой времени"""

    widget: CalendarWithTime

    def get_selected_date(self) -> Optional[date]:
        """Получить выбранную дату"""
        return self.widget.get_selected_date(self.manager)

    def get_selected_hour(self) -> Optional[int]:
        """Получить выбранный час"""
        return self.widget.get_selected_hour(self.manager)

    def get_selected_datetime(self) -> Optional[datetime]:
        """Получить выбранные дату и время как datetime"""
        date = self.get_selected_date()
        hour = self.get_selected_hour()

        if date and hour is not None:
            return datetime.combine(date, time(hour=hour, minute=0, second=0))
        return None

    def reset_selection(self) -> None:
        """Сбросить выбранные дату и время"""
        data = self.widget.get_widget_data(self.manager, {})
        data.pop("selected_date", None)
        data.pop("selected_hour", None)
        self.widget.set_scope(CalendarScope.DAYS, self.manager)
