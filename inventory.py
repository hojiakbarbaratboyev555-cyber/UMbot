from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from datetime import datetime
from zoneinfo import ZoneInfo

from config import CURRENCY_NAME
from items import ITEMS
from rate_assets import get_item_hb_price

router = Router()

SELL_DISCOUNT_PERCENT = 10
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")


@router.message(Command("kurs"))
async def show_kurs(message: Message):
    lines = []

    for item in ITEMS:
        buy_price = await get_item_hb_price(item)
        sell_price = round(buy_price * (1 - SELL_DISCOUNT_PERCENT / 100), 4)

        lines.append(
            f"{item['emoji']}\n"
            f"Sotib olish: {buy_price} {CURRENCY_NAME}\n"
            f"Sotish: {sell_price} {CURRENCY_NAME}"
        )

    now = datetime.now(TASHKENT_TZ).strftime("%d.%m.%Y %H:%M")
    lines.append(f"Vaqt: {now}")

    text = "\n\n".join(lines)
    await message.answer(text)