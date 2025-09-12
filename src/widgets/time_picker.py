from __future__ import annotations

from datetime import time
from enum import Enum
from typing import Any, Optional, Protocol, Union

from aiogram.types import CallbackQuery, InlineKeyboardButton
from aiogram_dialog.api.entities import ChatEvent
from aiogram_dialog.api.protocols import DialogManager
from aiogram_dialog.widgets.common import WhenCondition
from aiogram_dialog.widgets.kbd import Keyboard
from aiogram_dialog.widgets.widget_event import (
    WidgetEventProcessor,
    ensure_event_processor,
)


class TimePickerScope(Enum):
    """Scope для выбора времени"""

    HOURS = "HOURS"
    MINUTES = "MINUTES"


class OnTimeSelected(Protocol):
    """Протокол для обработки выбора времени"""

    async def __call__(
        self,
        event: ChatEvent,
        widget: ManagedTimePicker,
        dialog_manager: DialogManager,
        selected_time: Optional[time],
        /,
    ) -> Any:
        raise NotImplementedError


class TimePicker(Keyboard):
    """Виджет для последовательного выбора времени"""

    def __init__(
        self,
        id: str,
        on_click: Union[OnTimeSelected, WidgetEventProcessor, None] = None,
        when: WhenCondition = None,
        allow_unknown: bool = True,
    ) -> None:
        super().__init__(id=id, when=when)
        self.on_time_selected = ensure_event_processor(on_click)
        self.allow_unknown = allow_unknown

    def _item_callback_data(self, data: str) -> str:
        return f"{self.widget_id}:{data}"

    def get_scope(self, manager: DialogManager) -> TimePickerScope:
        """Получить текущий scope"""
        data = self.get_widget_data(manager, {})
        scope_str = data.get("scope", TimePickerScope.HOURS.value)
        return TimePickerScope(scope_str)

    def set_scope(
        self, scope: TimePickerScope, manager: DialogManager
    ) -> None:
        """Установить scope"""
        data = self.get_widget_data(manager, {})
        data["scope"] = scope.value

    def get_selected_hour(self, manager: DialogManager) -> Optional[int]:
        """Получить выбранный час"""
        data = self.get_widget_data(manager, {})
        return data.get("hour")

    def set_selected_hour(
        self, hour: Optional[int], manager: DialogManager
    ) -> None:
        """Установить выбранный час"""
        data = self.get_widget_data(manager, {})
        if hour is None:
            data.pop("hour", None)
        else:
            data["hour"] = hour

    def get_selected_minute(self, manager: DialogManager) -> Optional[int]:
        """Получить выбранную минуту"""
        data = self.get_widget_data(manager, {})
        return data.get("minute")

    def set_selected_minute(
        self, minute: Optional[int], manager: DialogManager
    ) -> None:
        """Установить выбранную минуту"""
        data = self.get_widget_data(manager, {})
        if minute is None:
            data.pop("minute", None)
        else:
            data["minute"] = minute

    def is_time_unknown(self, manager: DialogManager) -> bool:
        """Проверить, выбрано ли "Не знаю" """
        data = self.get_widget_data(manager, {})
        return data.get("unknown", False)

    def set_time_unknown(self, unknown: bool, manager: DialogManager) -> None:
        """Установить флаг "Не знаю" """
        data = self.get_widget_data(manager, {})
        data["unknown"] = unknown

    def get_current_hour_page(self, manager: DialogManager) -> int:
        """Получить текущую страницу часов"""
        data = self.get_widget_data(manager, {})
        return data.get("hour_page", 0)

    def set_current_hour_page(self, page: int, manager: DialogManager) -> None:
        """Установить текущую страницу часов"""
        data = self.get_widget_data(manager, {})
        data["hour_page"] = page

    def get_current_minute_page(self, manager: DialogManager) -> int:
        """Получить текущую страницу минут"""
        data = self.get_widget_data(manager, {})
        return data.get("minute_page", 0)

    def set_current_minute_page(
        self, page: int, manager: DialogManager
    ) -> None:
        """Установить текущую страницу минут"""
        data = self.get_widget_data(manager, {})
        data["minute_page"] = page

    async def _render_keyboard(self, data, manager: DialogManager):
        """Рендеринг клавиатуры в зависимости от scope"""
        scope = self.get_scope(manager)

        if scope == TimePickerScope.HOURS:
            return await self._render_hours(manager)
        elif scope == TimePickerScope.MINUTES:
            return await self._render_minutes(manager)

    async def _render_hours(
        self, manager: DialogManager
    ) -> list[list[InlineKeyboardButton]]:
        """Рендеринг выбора часа"""
        keyboard = []

        # Константы для пагинации
        HOURS_PER_ROW = 4
        ROWS_PER_PAGE = 3
        HOURS_PER_PAGE = HOURS_PER_ROW * ROWS_PER_PAGE  # 12 часов на страницу

        # Получаем все часы
        hours = list(range(0, 24))
        total_pages = (len(hours) + HOURS_PER_PAGE - 1) // HOURS_PER_PAGE
        current_page = self.get_current_hour_page(manager)

        # Проверяем границы страницы
        if current_page >= total_pages:
            current_page = total_pages - 1
            self.set_current_hour_page(current_page, manager)
        elif current_page < 0:
            current_page = 0
            self.set_current_hour_page(current_page, manager)

        # Заголовок
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="Выберите час рождения:",
                    callback_data="ignore",
                )
            ]
        )

        # Получаем часы для текущей страницы
        start_idx = current_page * HOURS_PER_PAGE
        end_idx = min(start_idx + HOURS_PER_PAGE, len(hours))
        page_hours = hours[start_idx:end_idx]

        # Часы по 4 в ряд
        for i in range(0, len(page_hours), HOURS_PER_ROW):
            row = []
            for j in range(HOURS_PER_ROW):
                if i + j < len(page_hours):
                    hour = page_hours[i + j]
                    row.append(
                        InlineKeyboardButton(
                            text=f"{hour:02d}",
                            callback_data=self._item_callback_data(
                                f"hour:{hour}"
                            ),
                        )
                    )
            if row:
                keyboard.append(row)

        # Кнопки навигации (если нужны)
        if total_pages > 1:
            nav_row = []

            # Кнопка "Назад"
            if current_page > 0:
                nav_row.append(
                    InlineKeyboardButton(
                        text="<< Назад",
                        callback_data=self._item_callback_data("page:prev"),
                    )
                )

            # Кнопка "Вперед"
            if current_page < total_pages - 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text="Вперед >>",
                        callback_data=self._item_callback_data("page:next"),
                    )
                )

            if nav_row:
                keyboard.append(nav_row)

        # Кнопка "Не знаю"
        if self.allow_unknown:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        text="Не знаю точное время...",
                        callback_data=self._item_callback_data("unknown"),
                    )
                ]
            )

        return keyboard

    async def _render_minutes(
        self, manager: DialogManager
    ) -> list[list[InlineKeyboardButton]]:
        """Рендеринг выбора минут"""
        keyboard = []
        hour = self.get_selected_hour(manager)

        # Константы для пагинации
        MINUTES_PER_ROW = 5
        ROWS_PER_PAGE = 6
        MINUTES_PER_PAGE = (
            MINUTES_PER_ROW * ROWS_PER_PAGE
        )  # 30 минут на страницу

        # Получаем все минуты
        minutes = list(range(0, 60))
        total_pages = (len(minutes) + MINUTES_PER_PAGE - 1) // MINUTES_PER_PAGE
        current_page = self.get_current_minute_page(manager)

        # Проверяем границы страницы
        if current_page >= total_pages:
            current_page = total_pages - 1
            self.set_current_minute_page(current_page, manager)
        elif current_page < 0:
            current_page = 0
            self.set_current_minute_page(current_page, manager)

        # Заголовок
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="Выберите минуты:",
                    callback_data="ignore",
                )
            ]
        )

        # Получаем минуты для текущей страницы
        start_idx = current_page * MINUTES_PER_PAGE
        end_idx = min(start_idx + MINUTES_PER_PAGE, len(minutes))
        page_minutes = minutes[start_idx:end_idx]

        # Минуты по 5 в ряд
        for i in range(0, len(page_minutes), MINUTES_PER_ROW):
            row = []
            for j in range(0, MINUTES_PER_ROW):
                if i + j < len(page_minutes):
                    minute = page_minutes[i + j]
                    row.append(
                        InlineKeyboardButton(
                            text=f"{minute:02d}",
                            callback_data=self._item_callback_data(
                                f"minute:{minute}"
                            ),
                        )
                    )
            if row:
                keyboard.append(row)

        # Кнопки навигации (если нужны)
        if total_pages > 1:
            nav_row = []

            # Кнопка "Назад"
            if current_page > 0:
                nav_row.append(
                    InlineKeyboardButton(
                        text="<< Назад",
                        callback_data=self._item_callback_data(
                            "page_min:prev"
                        ),
                    )
                )

            # Кнопка "Вперед"
            if current_page < total_pages - 1:
                nav_row.append(
                    InlineKeyboardButton(
                        text="Вперед >>",
                        callback_data=self._item_callback_data(
                            "page_min:next"
                        ),
                    )
                )

            if nav_row:
                keyboard.append(nav_row)

        # Кнопка назад
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="<< Вернуться к выбору часа",
                    callback_data=self._item_callback_data("back:hours"),
                )
            ]
        )

        return keyboard

    async def _process_item_callback(
        self,
        callback: CallbackQuery,
        data: str,
        dialog,
        manager: DialogManager,
    ) -> bool:
        """Обработка callback"""
        if data == "unknown":
            # Пользователь не знает время
            self.set_time_unknown(True, manager)

            # Вызываем обработчик с None
            await self.on_time_selected.process_event(
                manager.event,
                self.managed(manager),
                manager,
                None,
            )
            return True

        parts = data.split(":")

        if parts[0] == "hour":
            hour = int(parts[1])
            self.set_selected_hour(hour, manager)
            self.set_scope(TimePickerScope.MINUTES, manager)
            return True

        elif parts[0] == "minute":
            minute = int(parts[1])
            self.set_selected_minute(minute, manager)

            hour = self.get_selected_hour(manager)
            selected_time = time(hour=hour, minute=minute)

            # Вызываем обработчик
            await self.on_time_selected.process_event(
                manager.event,
                self.managed(manager),
                manager,
                selected_time,
            )
            return True

        elif parts[0] == "back":
            if parts[1] == "hours":
                self.set_scope(TimePickerScope.HOURS, manager)
            return True

        elif parts[0] == "page":
            current_page = self.get_current_hour_page(manager)
            if parts[1] == "prev" and current_page > 0:
                self.set_current_hour_page(current_page - 1, manager)
                return True
            elif parts[1] == "next":
                # Проверим, что есть следующая страница
                hours = list(range(0, 24))
                total_pages = (len(hours) + 11) // 12  # 12 часов на страницу
                if current_page < total_pages - 1:
                    self.set_current_hour_page(current_page + 1, manager)
                    return True

        elif parts[0] == "page_min":
            current_page = self.get_current_minute_page(manager)
            if parts[1] == "prev" and current_page > 0:
                self.set_current_minute_page(current_page - 1, manager)
                return True
            elif parts[1] == "next":
                # Проверим, что есть следующая страница
                minutes = list(range(0, 60))
                total_pages = (len(minutes) + 29) // 30  # 30 минут на страницу
                if current_page < total_pages - 1:
                    self.set_current_minute_page(current_page + 1, manager)
                    return True

        return False

    def managed(self, manager: DialogManager) -> ManagedTimePicker:
        """Возвращаем managed виджет"""
        return ManagedTimePicker(self, manager)


class ManagedTimePicker:
    """Managed версия TimePicker"""

    def __init__(self, widget: TimePicker, manager: DialogManager):
        self.widget = widget
        self.manager = manager

    def get_selected_time(self) -> Optional[time]:
        """Получить выбранное время если все компоненты выбраны"""
        if self.widget.is_time_unknown(self.manager):
            return None

        hour = self.widget.get_selected_hour(self.manager)
        minute = self.widget.get_selected_minute(self.manager)

        if hour is not None and minute is not None:
            return time(hour=hour, minute=minute)
        return None

    def is_unknown(self) -> bool:
        """Проверить, выбрано ли "Не знаю" """
        return self.widget.is_time_unknown(self.manager)

    def reset(self) -> None:
        """Сбросить выбор"""
        data = self.widget.get_widget_data(self.manager, {})
        data.clear()
        data["scope"] = TimePickerScope.HOURS.value
        data["hour_page"] = 0
        data["minute_page"] = 0
