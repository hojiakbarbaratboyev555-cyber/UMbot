from aiogram import Router, F
from aiogram.types import Message

from keyboards import support_kb

router = Router()


@router.message(F.text == "☎️ Qo'llab-quvvatlash")
async def show_support(message: Message):
    await message.answer(
        "Savollaringiz yoki muammolaringiz bo'lsa, admin bilan bog'laning:",
        reply_markup=support_kb(),
    )