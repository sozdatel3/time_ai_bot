from db.db import Base, get_engine

from .ai_promo import AiPromo
from .asto_info import AstroInfo
from .first_mes import FirstMes
from .old_workflow.ab_group import ABGroup
from .old_workflow.abonement_promo import AbonementPromo
from .old_workflow.big_mes import BigMes
from .old_workflow.broadcast import Broadcast
from .old_workflow.certificate import Certificate
from .old_workflow.coupons import Coupon
from .old_workflow.links import BotLink
from .old_workflow.permanent_broadcast import (
    PermanentBroadcast,
    PermanentBroadcastStatus,
)
from .old_workflow.person_button import PersonButton
from .old_workflow.price_for_group import PriceForGroup
from .old_workflow.question import Question
from .old_workflow.useful_material import UsefulMaterial
from .old_workflow.yoga_tap import YogaTap
from .order import Order, create_initial_order
from .price import Price
from .user import User


async def init_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        await create_initial_order()
    except Exception as e:
        print(e)
