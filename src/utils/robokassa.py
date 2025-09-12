import decimal
import hashlib
import json
from urllib import parse

import aiohttp

from config.config import load_config

config = load_config()
# URL для запросов к Робокассе
ROBOKASSA_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"


def calculate_signature(*args) -> str:
    """Create signature MD5."""
    formatted_args = []
    for i, arg in enumerate(args, 1):
        if i == 6:
            formatted_args.append(f"Shp_id={arg}")
        elif i == 7:
            formatted_args.append(f"Shp_id_game={arg}")
        else:
            formatted_args.append(str(arg))

    return hashlib.md5(":".join(formatted_args).encode()).hexdigest()


async def shorten_url(long_url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://tinyurl.com/api-create.php?url={long_url}"
        ) as response:
            return await response.text()


async def do_robocassa(
    user_id, amount, Inid, description, game_id, is_recurring=False
):
    return generate_payment_link(
        config.robokassa.LOGIN,
        # config.robokassa.TEST_PASSWORD1,
        config.robokassa.PASSWORD1,
        amount,
        Inid,
        description,
        # 1,
        0,
        user_id,
        game_id,
        is_recurring=is_recurring,
    )


def generate_payment_link(
    merchant_login: str,  # Merchant login
    merchant_password_1: str,  # Merchant password
    cost: decimal,  # Cost of goods, RU
    number: int,  # Invoice number
    description: str,  # Description of the purchase
    is_test=0,
    user_id=0,
    game_id=0,
    robokassa_payment_url="https://auth.robokassa.ru/Merchant/Index.aspx",
    is_recurring=False,
) -> str:
    """URL for redirection of the customer to the service."""

    # Создаем JSON для фискального чека
    receipt = {
        "items": [
            {
                "name": description,
                "quantity": 1,
                "sum": float(cost),
                "payment_method": "full_prepayment",
                "payment_object": "service",
                "tax": "none",
            }
        ],
        # 'sum'
    }
    # URL-кодируем Receipt для подписи
    encoded_receipt = parse.quote(json.dumps(receipt))

    signature = calculate_signature(
        merchant_login,
        cost,
        number,
        encoded_receipt,
        # receipt,  #
        merchant_password_1,
        user_id,
        game_id,
        # merchant_login, cost, number, merchant_password_1
    )
    # print(
    #     merchant_login, cost, number, merchant_password_1, is_test, signature
    # )
    data = {
        "MerchantLogin": merchant_login,
        "OutSum": cost,
        "InvoiceID": number,
        # "InvId": number,
        "Description": description,
        "SignatureValue": signature,
        "IsTest": is_test,
        "Receipt": encoded_receipt,
        "Recurring": "true" if is_recurring else "false",
        # "Receipt": json.dumps(receipt),
        "Shp_id": user_id,
        "Shp_id_game": game_id,
    }
    return f"{robokassa_payment_url}?{parse.urlencode(data)}"


# async def do_robocassa_recurrent():
#     pass


async def do_robocassa_recurent(
    user_id, amount, InvoiceID, description, previous_invoice_id, game_id=0
):
    """Выполнение рекуррентного платежа"""
    receipt = {
        "items": [
            {
                "name": description,
                "quantity": 1,
                "sum": float(amount),
                "payment_method": "full_prepayment",
                "payment_object": "service",
                "tax": "none",
            }
        ],
        # 'sum'
    }
    # URL-кодируем Receipt для подписи
    encoded_receipt = parse.quote(json.dumps(receipt))
    # Формируем данные для запроса
    signature = calculate_signature(
        config.robokassa.LOGIN,
        amount,
        InvoiceID,
        encoded_receipt,
        config.robokassa.PASSWORD1,
        user_id,
        game_id,
    )

    data = {
        "MerchantLogin": config.robokassa.LOGIN,
        "InvoiceID": InvoiceID,
        "PreviousInvoiceID": previous_invoice_id,
        "Description": description,
        "SignatureValue": signature,
        "OutSum": amount,
        "Receipt": encoded_receipt,
        "Shp_id": user_id,
        "Shp_id_game": game_id,
    }

    # Отправляем POST запрос
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://auth.robokassa.ru/Merchant/Recurring", data=data
        ) as response:
            response_text = await response.text()

            if response.status == 200 and response_text.startswith("OK"):
                return True
            else:
                print(f"Ошибка рекуррентного платежа: {response_text}")
                return False


def generate_recurring_payment_link(
    merchant_login: str,
    merchant_password_1: str,
    cost: decimal,
    number: int,
    description: str,
    previous_invoice_id: int,
    is_test=0,
    user_id=0,
    robokassa_payment_url="https://auth.robokassa.ru/Merchant/Recurring",
) -> str:
    """Генерация ссылки для повторного платежа."""
    signature = calculate_signature(
        merchant_login,
        cost,
        number,
        merchant_password_1,
        user_id,
    )

    data = {
        "MerchantLogin": merchant_login,
        "OutSum": cost,
        "InvoiceID": number,
        "PreviousInvoiceID": previous_invoice_id,
        "Description": description,
        "SignatureValue": signature,
        "IsTest": is_test,
        "Shp_id": user_id,
    }
    return f"{robokassa_payment_url}?{parse.urlencode(data)}"
