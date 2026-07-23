from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime

from config import CURRENCY_NAME
from items import ITEMS
from rate_assets import get_item_hb_price
from keyboards import item_trade_kb

router = Router()

SELL_DISCOUNT_PERCENT = 10


@router.message(Command("kurs"))
async def show_kurs(message: Message):
    for item in ITEMS:
        buy_price = await get_item_hb_price(item)
        sell_price = round(buy_price * (1 - SELL_DISCOUNT_PERCENT / 100), 4)

        text = (
            f"{item['emoji']} <b>{item['label']}</b>\n\n"
            f"Real narx: {buy_price} {CURRENCY_NAME}\n"
            f"Sotish narxi: {sell_price} {CURRENCY_NAME}"
        )
        await message.answer(text, reply_markup=item_trade_kb(item["key"]))

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await message.answer(now)