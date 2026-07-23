from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

import database as db
from keyboards import main_menu_kb

router = Router()

WELCOME_EMOJI = '<tg-emoji emoji-id="5282843764451195532">👾</tg-emoji>'


@router.message(CommandStart())
async def cmd_start(message: Message):
    await db.get_or_create_user(
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    await message.answer(WELCOME_EMOJI)

    await message.answer(
        "Assalomu alaykum! Xush kelibsiz. Quyidagi menyudan kerakli bo'limni tanlang:",
        reply_markup=main_menu_kb(),
    )


@router.message(F.text == "◀️ Ortga qaytish")
async def back_to_main(message: Message, state):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=main_menu_kb())


# VAQTINCHA: premium emoji ID'sini aniqlash uchun.
# Kerakli premium emojini shu botga yuboring - u ID'sini qaytaradi.
# Ishlatib bo'lgach, shu handlerni o'chirib tashlang.
def _has_custom_emoji(message: Message) -> bool:
    return bool(message.entities) and any(e.type == "custom_emoji" for e in message.entities)


@router.message(F.func(_has_custom_emoji))
async def get_emoji_id_debug(message: Message):
    for entity in message.entities:
        if entity.type == "custom_emoji":
            await message.answer(f"ID: {entity.custom_emoji_id}")
            return
