from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

import database as db
from config import WELCOME_STICKER_ID
from keyboards import main_menu_kb

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.get_or_create_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    if WELCOME_STICKER_ID:
        await message.answer_sticker(WELCOME_STICKER_ID)
    else:
        await message.answer("🏠"),
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "◀️ Ortga qaytish")
async def back_to_main(message: Message, state):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())