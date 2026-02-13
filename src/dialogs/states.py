from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import StartMode

from db.models.old_workflow.price_for_group import get_price_for_user


def format_price_and_balance(value: float) -> str:
    """Formats a number to a string with a space for thousands separator."""
    if value is None:
        value = 0.0
    return f"{int(value):,}".replace(",", " ")


async def format_price(user_id: int, price_type: str) -> str:
    """Format price with spaces for thousands"""
    price = await get_price_for_user(user_id, price_type)
    return f"{int(price):,}".replace(",", " ")


class MainMenuStates(StatesGroup):
    main = State()
    choose_language = State()


class ReferProgramStates(StatesGroup):
    main = State()


class AskQuestionStates(StatesGroup):
    main = State()
    waiting_for_question = State()
    waiting_for_question_thanks = State()


class UsefulMaterialsStates(StatesGroup):
    main = State()


async def main_menu_back(c, b, m):
    await m.start(MainMenuStates.main, mode=StartMode.RESET_STACK)


class SubscriptionStates(StatesGroup):
    select_plan = State()
    manage_subscription = State()


class CertificatesStates(StatesGroup):
    main = State()
    enter_amount = State()
    confirm_purchase = State()
    payment = State()


class PaymentStates(StatesGroup):
    payment_choice = State()
    payment = State()


class AdminStates(StatesGroup):
    MAIN = State()
    STOP_PAYMENT = State()

    EDIT_MESSAGE = State()
    BROADCAST = State()
    BROADCAST_SEND = State()
    AB_GROUPS_ANDMORE = State()
    MATERIALS = State()
    ADD_MATERIAL = State()
    ADD_MATERIAL_NAME = State()
    ADD_MATERIAL_COST = State()
    START_PAYMENT = State()
    EVENT_PLANNING = State()
    DELETE_MATERIAL = State()
    NOTIFICATION_CHOICE = State()
    CREATE_CERTIFICATE = State()
    CONFIRM_CERTIFICATE = State()
    EDIT_PRICE = State()
    PRICES = State()
    SALES_MAIN = State()
    ADD_LINK_DESCRIPTION = State()
    SALES_PROMO = State()
    LINKS = State()
    PERMANENT_BROADCAST_NAME = State()
    PERMANENT_BROADCAST = State()
    PERMANENT_BROADCAST_LIST = State()
    PERMANENT_BROADCAST_SEND = State()
    PAYMENT_LINKS = State()
    ADD_LINK = State()
    EDIT_LINK = State()
    AB_GROUPS_MAIN = State()
    AB_GROUPS_BUTTONS = State()  # Новое состояние для выбора кнопки
    AB_GROUPS_BUTTONS_COUNT = State()
    AB_GROUPS_NAME = State()
    AB_GROUPS_SPLIT = State()
    AB_GROUPS_DESCRIPTION = State()
    PRICE_TYPE_SELECT = State()  # Выбор типа цен (базовые/групповые)
    GROUP_SELECT = State()  # Выбор AB группы
    GROUP_PRICES = State()  # Управление ценами группы
    EDIT_GROUP_PRICE = State()  # Редактирование цены для группы
    BROADCAST_AB_GROUPS = State()
    # Состояния для настроек
    SETTINGS_MAIN = State()
    SETTINGS_TEST_PERIOD = State()
    SETTINGS_SALE_WINDOW_START = State()
    SETTINGS_SALE_WINDOW_END = State()
    SETTINGS_SALE_WINDOW_DAYS = State()

    # AI Promo states
    AIPROMO_MAIN = State()
    AIPROMO_COUNT_INPUT = State()
    AIPROMO_CONFIRM = State()
    AIPROMO_LIST = State()


class StatisticStates(StatesGroup):
    main = State()
    users = State()
    games = State()
    sales = State()
    select_period = State()
    sales_by_weekday = State()
    sales_by_monthday = State()
    time_to_purchase = State()
    meta_cards = State()
    meta_cards_analytics = State()
    subscriptions = State()
    yoga = State()
    buttons = State()
    broadcast = State()


class YogaClubStates(StatesGroup):
    main = State()
    goticks = State()
    minimal = State()
    vintaaj = State()
    name = State()
    name_2 = State()
    what_inside = State()
    phone_input = State()
    payment = State()
    publications = State()
    subscription = State()
    publications_selected = State()
    subscription_confirm = State()
    choose_language = State()
    test_period = State()
    remind_about_opening = State()
    prompts = State()
    prompt_selected = State()
    time_video = State()


class PublicationsStates(StatesGroup):
    main = State()


class PersonalCabinaStates(StatesGroup):
    main = State()
    subscription = State()
    subscription_confirm = State()
    subscription_canceled_thanks = State()
    subscription_canceled = State()


class AstroStates(StatesGroup):
    main = State()
    name = State()
    natal_date = State()
    natal_time = State()
    natal_place = State()
    confirm_data = State()
    confirm_location = State()
    show_result = State()
    ai_prediction_input = State()
    ai_prediction_result = State()
    ai_prediction_loading = State()


class AboutMeStates(StatesGroup):
    main = State()
    all_services = State()
