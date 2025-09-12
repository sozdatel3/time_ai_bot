from __future__ import annotations

from datetime import date, datetime
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


class DatePickerScope(Enum):
    """Scope для выбора даты"""

    YEARS = "YEARS"
    MONTHS = "MONTHS"
    DAYS = "DAYS"


class OnDateSelected(Protocol):
    """Протокол для обработки выбора даты"""

    async def __call__(
        self,
        event: ChatEvent,
        widget: ManagedDatePicker,
        dialog_manager: DialogManager,
        selected_date: date,
        /,
    ) -> Any:
        raise NotImplementedError


MONTHS_RU = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]


class DatePicker(Keyboard):
    """Виджет для последовательного выбора даты"""

    def __init__(
        self,
        id: str,
        on_click: Union[OnDateSelected, WidgetEventProcessor, None] = None,
        when: WhenCondition = None,
        min_year: int = 1920,
        max_year: Optional[int] = None,
    ) -> None:
        super().__init__(id=id, when=when)
        self.on_date_selected = ensure_event_processor(on_click)
        self.min_year = min_year
        self.max_year = max_year or datetime.now().year

    def _item_callback_data(self, data: str) -> str:
        return f"{self.widget_id}:{data}"

    def get_scope(self, manager: DialogManager) -> DatePickerScope:
        """Получить текущий scope"""
        data = self.get_widget_data(manager, {})
        scope_str = data.get("scope", DatePickerScope.YEARS.value)
        return DatePickerScope(scope_str)

    def set_scope(
        self, scope: DatePickerScope, manager: DialogManager
    ) -> None:
        """Установить scope"""
        data = self.get_widget_data(manager, {})
        data["scope"] = scope.value

    def get_selected_year(self, manager: DialogManager) -> Optional[int]:
        """Получить выбранный год"""
        data = self.get_widget_data(manager, {})
        return data.get("year")

    def set_selected_year(self, year: int, manager: DialogManager) -> None:
        """Установить выбранный год"""
        data = self.get_widget_data(manager, {})
        data["year"] = year

    def get_selected_month(self, manager: DialogManager) -> Optional[int]:
        """Получить выбранный месяц"""
        data = self.get_widget_data(manager, {})
        return data.get("month")

    def set_selected_month(self, month: int, manager: DialogManager) -> None:
        """Установить выбранный месяц"""
        data = self.get_widget_data(manager, {})
        data["month"] = month

    def get_current_year_page(self, manager: DialogManager) -> int:
        """Получить текущую страницу годов"""
        data = self.get_widget_data(manager, {})
        return data.get("year_page", 0)

    def set_current_year_page(self, page: int, manager: DialogManager) -> None:
        """Установить текущую страницу годов"""
        data = self.get_widget_data(manager, {})
        data["year_page"] = page

    async def _render_keyboard(self, data, manager: DialogManager):
        """Рендеринг клавиатуры в зависимости от scope"""
        scope = self.get_scope(manager)

        if scope == DatePickerScope.YEARS:
            return await self._render_years(manager)
        elif scope == DatePickerScope.MONTHS:
            return await self._render_months(manager)
        elif scope == DatePickerScope.DAYS:
            return await self._render_days(manager)

    async def _render_years(
        self, manager: DialogManager
    ) -> list[list[InlineKeyboardButton]]:
        """Рендеринг выбора года"""
        keyboard = []

        # Константы для пагинации
        YEARS_PER_ROW = 3
        ROWS_PER_PAGE = 8
        YEARS_PER_PAGE = YEARS_PER_ROW * ROWS_PER_PAGE  # 24 года на страницу

        # Получаем все года
        years = list(range(self.max_year, self.min_year - 1, -1))
        total_pages = (len(years) + YEARS_PER_PAGE - 1) // YEARS_PER_PAGE
        current_page = self.get_current_year_page(manager)

        # Проверяем границы страницы
        if current_page >= total_pages:
            current_page = total_pages - 1
            self.set_current_year_page(current_page, manager)
        elif current_page < 0:
            current_page = 0
            self.set_current_year_page(current_page, manager)

        # # Заголовок с информацией о странице
        # page_info = (
        #     f"Страница {current_page + 1} из {total_pages}"
        #     if total_pages > 1
        #     else ""
        # )
        # header_text = f"Выберите год рождения: {page_info}"
        header_text = "Выберите год рождения:"
        keyboard.append(
            [InlineKeyboardButton(text=header_text, callback_data="ignore")]
        )

        # Получаем года для текущей страницы
        start_idx = current_page * YEARS_PER_PAGE
        end_idx = min(start_idx + YEARS_PER_PAGE, len(years))
        page_years = years[start_idx:end_idx]

        # Годы по 3 в ряд
        for i in range(0, len(page_years), YEARS_PER_ROW):
            row = []
            for j in range(YEARS_PER_ROW):
                if i + j < len(page_years):
                    year = page_years[i + j]
                    row.append(
                        InlineKeyboardButton(
                            text=str(year),
                            callback_data=self._item_callback_data(
                                f"year:{year}"
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

        return keyboard

    async def _render_months(
        self, manager: DialogManager
    ) -> list[list[InlineKeyboardButton]]:
        """Рендеринг выбора месяца"""
        keyboard = []
        year = self.get_selected_year(manager)

        # Заголовок
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="Выберите месяц: ",
                    callback_data="ignore",
                )
            ]
        )

        # Месяцы по 2 в ряд
        for i in range(0, 12, 2):
            row = []
            for j in range(2):
                if i + j < 12:
                    month_num = i + j + 1
                    month_name = MONTHS_RU[i + j]
                    row.append(
                        InlineKeyboardButton(
                            text=month_name,
                            callback_data=self._item_callback_data(
                                f"month:{month_num}"
                            ),
                        )
                    )
            keyboard.append(row)

        # Кнопка назад
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="<< Вернуться к выбору года",
                    callback_data=self._item_callback_data("back:years"),
                )
            ]
        )

        return keyboard

    async def _render_days(
        self, manager: DialogManager
    ) -> list[list[InlineKeyboardButton]]:
        """Рендеринг выбора дня"""
        keyboard = []
        year = self.get_selected_year(manager)
        month = self.get_selected_month(manager)

        # Заголовок
        month_name = MONTHS_RU[month - 1]
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="Выберите день:",
                    callback_data="ignore",
                )
            ]
        )

        # Определяем количество дней в месяце
        if month == 2:  # Февраль
            if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
                days_in_month = 29
            else:
                days_in_month = 28
        elif month in [4, 6, 9, 11]:
            days_in_month = 30
        else:
            days_in_month = 31

        # Дни по 6 в ряд
        for i in range(0, days_in_month, 6):
            row = []
            for j in range(6):
                if i + j < days_in_month:
                    day = i + j + 1
                    row.append(
                        InlineKeyboardButton(
                            text=str(day),
                            callback_data=self._item_callback_data(
                                f"day:{day}"
                            ),
                        )
                    )
            if row:
                keyboard.append(row)

        # Кнопка назад
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="<< Вернуться к выбору месяца",
                    callback_data=self._item_callback_data("back:months"),
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
        parts = data.split(":")

        if parts[0] == "year":
            year = int(parts[1])
            self.set_selected_year(year, manager)
            self.set_scope(DatePickerScope.MONTHS, manager)
            return True

        elif parts[0] == "month":
            month = int(parts[1])
            self.set_selected_month(month, manager)
            self.set_scope(DatePickerScope.DAYS, manager)
            return True

        elif parts[0] == "day":
            day = int(parts[1])
            year = self.get_selected_year(manager)
            month = self.get_selected_month(manager)

            selected_date = date(year, month, day)

            # Вызываем обработчик
            await self.on_date_selected.process_event(
                manager.event,
                self.managed(manager),
                manager,
                selected_date,
            )
            return True

        elif parts[0] == "back":
            if parts[1] == "years":
                self.set_scope(DatePickerScope.YEARS, manager)
            elif parts[1] == "months":
                self.set_scope(DatePickerScope.MONTHS, manager)
            return True

        elif parts[0] == "page":
            current_page = self.get_current_year_page(manager)
            if parts[1] == "prev" and current_page > 0:
                self.set_current_year_page(current_page - 1, manager)
                return True
            elif parts[1] == "next":
                # Проверим, что есть следующая страница
                years = list(range(self.max_year, self.min_year - 1, -1))
                total_pages = (len(years) + 23) // 24  # 24 года на страницу
                if current_page < total_pages - 1:
                    self.set_current_year_page(current_page + 1, manager)
                    return True

        return False

    def managed(self, manager: DialogManager) -> ManagedDatePicker:
        """Возвращаем managed виджет"""
        return ManagedDatePicker(self, manager)


class ManagedDatePicker:
    """Managed версия DatePicker"""

    def __init__(self, widget: DatePicker, manager: DialogManager):
        self.widget = widget
        self.manager = manager

    def get_selected_date(self) -> Optional[date]:
        """Получить выбранную дату если все компоненты выбраны"""
        year = self.widget.get_selected_year(self.manager)
        month = self.widget.get_selected_month(self.manager)

        if year and month:
            # Для managed версии возвращаем дату с первым числом если день не выбран
            return date(year, month, 1)
        return None

    def reset(self) -> None:
        """Сбросить выбор"""
        data = self.widget.get_widget_data(self.manager, {})
        data.clear()
        data["scope"] = DatePickerScope.YEARS.value
        data["year_page"] = 0
