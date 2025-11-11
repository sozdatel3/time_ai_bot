import logging
from typing import TYPE_CHECKING, Any, Optional

from aiogram import Bot
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ConfigDict, SecretStr
from pydantic_settings import BaseSettings

if TYPE_CHECKING:
    from manager.admin_notifier import AdminNotifier
    from manager.spam_service import SpamManager
    from utils.astro_manager import AstroManager
load_dotenv()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ADMIN_IDS = [
    1358227914,
    7683253987,
    7851627121,
    424831637,
    821895433,
    383446904,
]
DEBUG = True


DATABASE_URL = "sqlite+aiosqlite:///milena.db"


class BotConfig(BaseSettings):

    token: SecretStr
    link: str
    id: str = ""
    name: str = ""
    api_token: str = ""
    payment_handler: Any = None
    api_id: int
    api_hash: str
    telethon_client: Any = None


class DatabaseConfig(BaseSettings):
    url: str
    # name: str


class RobokassaConfig(BaseSettings):
    LOGIN: str
    PASSWORD1: str
    PASSWORD2: str
    TEST_PASSWORD1: str
    TEST_PASSWORD2: str


#
class Config(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="allow",
        arbitrary_types_allowed=True,
    )

    bot: BotConfig
    openai_api_key: str = ""
    open_ai_client: OpenAI | None = None
    db: DatabaseConfig
    robokassa: RobokassaConfig
    admin_ids: list[int] = [
        1358227914,
        7683253987,
        7851627121,
        424831637,
        821895433,
        383446904,
    ]
    # chanel_id: int = -4591969999
    chanel_id: int = -1002759594261
    # chat_admin_ids: list[int] = [-4831020502]
    chat_admin_ids: list[int] = [-1003319704973]
    # chanel_id: int = -1002507666461
    api_url: str
    oferta_url: str = (
        "https://drive.google.com/file/d/1kH59RxQTTZwqsPX7h13NatmizvySg9uy/view?usp=sharing"
    )
    admin_notifier: Any = None

    def set_bot_id(self, bot_id: str):
        self.bot.id = bot_id

    def set_bot_name(self, bot_name: str):
        self.bot.name = bot_name

    def set_bot_token(self, bot_token: str):
        self.bot.api_token = bot_token

    def set_payment_handler(self, payment_handler):
        self.bot.payment_handler = payment_handler

    def set_admin_notifier(self, admin_notifier: "AdminNotifier"):
        self.admin_notifier = admin_notifier

    def get_admin_notifier(self, bot: Bot) -> "AdminNotifier":
        from manager.admin_notifier import AdminNotifier

        return self.admin_notifier or AdminNotifier(bot, self)

    def set_spam_manager(self, spam_manager: "SpamManager"):
        self.spam_manager = spam_manager

    def get_spam_manager(self) -> "SpamManager":
        from manager.spam_service import SpamManager

        return self.spam_manager or SpamManager(self.bot)

    def set_astro_manager(self, astro_manager: "AstroManager"):
        self.astro_manager = astro_manager

    def get_astro_manager(self) -> "AstroManager":
        from utils.astro_manager import AstroManager

        return self.astro_manager or AstroManager(self.bot)

    def set_openai_client(self):

        if self.open_ai_client is None:
            self.open_ai_client = OpenAI(api_key=self.openai_api_key)

    def get_openai_client(self) -> OpenAI:

        return self.open_ai_client or OpenAI(self.openai_api_key)

    def set_telethon_client(self, telethon_client: Any):
        self.bot.telethon_client = telethon_client

    def get_telethon_client(self) -> Any:
        return self.bot.telethon_client


_config_instance: Optional[Config] = None


def load_config() -> Config:
    global _config_instance
    if _config_instance is None:
        load_dotenv(override=True)
        _config_instance = Config()
    return _config_instance


def get_config() -> Config:
    if _config_instance is None:
        raise RuntimeError(
            "Config не инициализирован. Сначала вызовите load_config()."
        )
    return _config_instance
