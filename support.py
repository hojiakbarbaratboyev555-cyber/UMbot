from aiogram import Router, F
from aiogram.types import Message

from config import TOPUP_TEXT
from keyboards import support_kb, topup_kb

router = Router()


@router.message(F.text == "🆘 Qo'llab-quvvatlash")
async def show_support(message: Message):
    await message.answer(
        "Savollaringiz yoki muammolaringiz bo'lsa, admin bilan bog'laning:",
        reply_markup=support_kb(),
    )


@router.message(F.text == "💳 Hisob to'ldirish")
async def show_topup(message: Message):
    await message.answer(TOPUP_TEXT, reply_markup=topup_kb())