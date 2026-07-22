from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config import CURRENCY_NAME
from items import ITEMS
from rate_assets import get_item_hb_price
from keyboards import item_buy_kb
from datetime import datetime

router = Router()


@router.message(Command("kurs"))
async def show_kurs(message: Message):
    for item in ITEMS:
        price_hb = await get_item_hb_price(item)
        text = f"{item['emoji']} <b>{item['label']}</b>\n\n💰 Narxi: {price_hb} {CURRENCY_NAME}"
        await message.answer(text, reply_markup=item_buy_kb(item["key"]))

    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    await message.answer(now)