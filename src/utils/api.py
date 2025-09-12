import asyncio
import logging
from functools import wraps
from typing import Optional

import aiohttp
from pydantic import BaseModel

from config.config import Config

logger = logging.getLogger(__name__)


class PrePaymentData(BaseModel):
    inv_id: str
    user_id: str
    amount: int
    currency: str = "RUB"
    custom_fields: dict = {}


def log_api_call(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):

        method_name = func.__name__

        try:
            response = await func(*args, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Ошибка при вызове {method_name}: {str(e)}")
            raise

    return wrapper


class API:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.api_url
        self.session = None

    async def initialize(self):
        self.session = aiohttp.ClientSession()
        await self.send_bot_info()

    async def close(self):
        if self.session:
            await self.session.close()

    @log_api_call
    async def send_bot_info(self):
        url = f"{self.base_url}/init/{self.config.bot.id}"
        data = {
            "bot_name": self.config.bot.name,
            "password2": self.config.robokassa.PASSWORD2,
        }
        async with self.session.post(url, json=data) as response:
            if response.status != 200:
                raise Exception(
                    f"Не удалось инициализировать бота: {await response.text()}"
                )
            return await response.json()

    @log_api_call
    async def send_payment_info(
        self, inv_id: str, user_id: str, amount: int, custom_fields: dict = {}
    ):
        url = f"{self.base_url}/pre_payment/{self.config.bot.id}"
        payment_data = PrePaymentData(
            inv_id=inv_id,
            user_id=user_id,
            amount=amount,
            custom_fields=custom_fields,
        )
        async with self.session.post(
            url, json=payment_data.model_dump()
        ) as response:
            if response.status != 200:
                raise Exception(
                    f"Не удалось отправить информацию о платеже: {await response.text()}"
                )
            return await response.json()

    # @log_api_call
    async def get_db(self, secret: str):
        url = f"{self.base_url}/get_database"
        params = {"secret_key": secret}
        async with self.session.get(url, params=params) as response:
            if response.status != 200:
                raise Exception(
                    f"Не удалось получить базу данных: {await response.text()}"
                )
            return await response.read()

    @log_api_call
    async def get_payments(self):
        url = f"{self.base_url}/payments/{self.config.bot.id}"
        # url = f"{self.base_url}/payments/8087924646"
        headers = {"Authorization": f"Bearer {self.config.bot.api_token}"}
        async with self.session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(
                    f"Не удалось получить список оплат: {await response.text()}"
                )
            return await response.json()

    @log_api_call
    async def get_game_summary_url(
        self, game, max_retries: int = 3
    ) -> Optional[str]:
        """Get game summary page URL with retry logic."""
        store_url = f"{self.base_url}/api/store-game"

        game_data = {
            "user_id": game.user_id,
            "sphere": game.sphere,
            "request": game.request,
            "moves": game.moves,
            "is_active": game.is_active,
            "sixes_count": game.sixes_count,
            "request_history": game.request_history,
            "created_at": game.created_at.isoformat(),
            "updated_at": game.updated_at.isoformat(),
            "id": game.id,
            "position": game.position,
            "in_game": game.in_game,
            "never_ask_sphere": game.never_ask_sphere,
            "paid": game.paid,
            "position_history": game.position_history,
            "coupon_link": game.coupon_link,
        }

        for attempt in range(max_retries):
            try:
                # Увеличиваем timeout для операций
                timeout = aiohttp.ClientTimeout(
                    total=30
                )  # 30 секунд общий timeout

                async with self.session.post(
                    store_url, json=game_data, timeout=timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to store game data: {error_text}"
                        )
                        raise Exception(
                            f"Failed to store game data: {error_text}"
                        )

                    # Читаем весь ответ сразу
                    result = await response.json()

                    if not result or "summary_url" not in result:
                        raise ValueError("Invalid response format")

                    return f"{self.base_url}{result['summary_url']}"

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(
                    f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}"
                )
                if (
                    attempt == max_retries - 1
                ):  # Если это была последняя попытка
                    raise
                await asyncio.sleep(
                    1 * (attempt + 1)
                )  # Увеличиваем задержку с каждой попыткой

                # Проверяем состояние сессии и пересоздаем при необходимости
                if self.session.closed:
                    logger.info("Recreating closed session")
                    self.session = aiohttp.ClientSession()

    @log_api_call
    async def get_pre_game_summary_url(
        self, game, max_retries: int = 3
    ) -> Optional[str]:
        """Get game summary page URL with retry logic."""
        store_url = f"{self.base_url}/api/store-game"

        game_data = {
            "user_id": game.user_id,
            "sphere": game.sphere,
            "request": game.request,
            "moves": game.moves,
            "is_active": game.is_active,
            "sixes_count": game.sixes_count,
            "request_history": game.request_history,
            "created_at": game.created_at.isoformat(),
            "updated_at": game.updated_at.isoformat(),
            "id": game.id,
            "position": game.position,
            "in_game": game.in_game,
            "never_ask_sphere": game.never_ask_sphere,
            "paid": game.paid,
            "position_history": game.position_history,
            "coupon_link": game.coupon_link,
        }

        for attempt in range(max_retries):
            try:
                # Увеличиваем timeout для операций
                timeout = aiohttp.ClientTimeout(
                    total=30
                )  # 30 секунд общий timeout

                async with self.session.post(
                    store_url, json=game_data, timeout=timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(
                            f"Failed to store game data: {error_text}"
                        )
                        raise Exception(
                            f"Failed to store game data: {error_text}"
                        )

                    # Читаем весь ответ сразу
                    result = await response.json()

                    if not result or "summary_url" not in result:
                        raise ValueError("Invalid response format")

                    try:
                        changed_url = result["summary_url"].replace(
                            "game-summary", "pre-game-summary"
                        )
                    except Exception as e:
                        logger.error(f"Error changing URL: {e}")
                        changed_url = result["summary_url"]

                    return f"{self.base_url}{changed_url}"

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.error(
                    f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}"
                )
                if (
                    attempt == max_retries - 1
                ):  # Если это была последняя попытка
                    raise
                await asyncio.sleep(
                    1 * (attempt + 1)
                )  # Увеличиваем задержку с каждой попыткой

                # Проверяем состояние сессии и пересоздаем при необходимости
                if self.session.closed:
                    logger.info("Recreating closed session")
                    self.session = aiohttp.ClientSession()


api: API = None


def get_api() -> API:
    if api is None:
        raise RuntimeError(
            "API не инициализирован. Сначала вызовите init_api()."
        )
    return api


def init_api(config: Config):
    global api
    api = API(config)
    return api
