from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# from utils.get_pay_photo_attachment import get_pay_photo_attachment


# async def check_payments(bot: Bot):
#     api = get_api()
#     config = get_config()
#     payment_handler = config.bot.payment_handler
#     try:
#         payments = await api.get_payments()
#         # print(f"payments: {payments}")
#         for payment in payments:
#             order_id = int(payment["inv_id"])
#             new_status = payment["status"]
#             order = await get_order(order_id)

#             if order and order.status != new_status:
#                 await update_order_status(order_id, new_status)
#                 if new_status == "completed":
#                     await payment_handler.handle_payment(order)

#     except Exception as e:
#         print(f"Ошибка при проверке платежей: {e}")


# async def send_daily_message(bot: Bot):

#     all_users_ids = await get_all_users_ids()
#     reminder_photo = await get_pay_photo_attachment(
#         bot, "misk/navigation/every_day.png"
#     )

#     share_text = """Привет! Хочу индивидуальный прогноз 💫"""
#     encoded_text = urllib.parse.quote(share_text)

#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [
#                 InlineKeyboardButton(
#                     text="Получить личный прогноз",
#                     url=f"https://t.me/bulgarova_astrolog?text={encoded_text}",
#                 )
#             ]
#         ]
#     )

#     for user_id in all_users_ids:

#         today_message = "<i><b>Твой небесный ориентир дня 🌙</b>\n\n"
#         today_message += random.choice(text.text_messages)
#         today_message += "\n\nС любовью, астролог Инна Булгарова.</i>"

#         try:
#             await bot.send_photo(
#                 user_id,
#                 photo=reminder_photo.file_id.file_id,
#                 caption=today_message,
#                 parse_mode="HTML",
#                 reply_markup=keyboard,
#             )
#         except Exception as e:
#             print("BURDAAA 6", e)
#             pass


def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()

    trigger = IntervalTrigger(seconds=30)

    trigger_meta = CronTrigger(hour=12, minute=0, timezone="Europe/Moscow")
    daily_at_15 = CronTrigger(hour=15, minute=0, timezone="Europe/Moscow")
    daily_at_12 = CronTrigger(hour=12, minute=0, timezone="Europe/Moscow")
    daily_at_13 = CronTrigger(hour=13, minute=0, timezone="Europe/Moscow")
    daily_at_11 = CronTrigger(hour=11, minute=0, timezone="Europe/Moscow")
    daily_at_9 = CronTrigger(hour=9, minute=0, timezone="Europe/Moscow")
    four_minutes = IntervalTrigger(minutes=4)
    three_min = IntervalTrigger(minutes=3)
    five_min = IntervalTrigger(minutes=5)
    one_min = IntervalTrigger(minutes=1)
    two_min = IntervalTrigger(minutes=2)
    seven_min = IntervalTrigger(minutes=7)
    thirty_sec = IntervalTrigger(seconds=30)
    one_hour = IntervalTrigger(hours=1)
    fifteen_min = IntervalTrigger(minutes=15)
    thirty_min = IntervalTrigger(minutes=30)
    six_hours = IntervalTrigger(hours=6)
    # trigger = IntervalTrigger(minutes=2)
    # scheduler.add_job(check_payments, trigger, args=[bot])
    # scheduler.add_job(send_daily_message, trigger, args=[bot])
    # scheduler.add_job(send_daily_message, daily_at_9, args=[bot])

    return scheduler
