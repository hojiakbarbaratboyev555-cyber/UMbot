from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import (
    CURRENCY_NAME,
    MIN_TOPUP_AMOUNT,
    PAYMENT_CARD_NUMBER,
    PAYMENT_CARD_OWNER,
    ADMIN_ID,
    HB_RATE_SUM,
)
from keyboards import earn_kb, admin_topup_kb, back_kb
from states import TopupStates

router = Router()


@router.message(F.text == "💵 Pul ishlash")
async def show_earn(message: Message):
    await message.answer(
        "Bu bo'lim orqali turli xil usulda pul ishlashingiz mumkin.",
        reply_markup=earn_kb(),
    )


@router.callback_query(F.data == "topup_start")
async def topup_start(callback: CallbackQuery, state: FSMContext):
    text = (
        f"Qabul qiluvchi:\n"
        f"Karta: {PAYMENT_CARD_NUMBER}\n"
        f"Ism: {PAYMENT_CARD_OWNER}\n"
        f"Min summa: {MIN_TOPUP_AMOUNT} {CURRENCY_NAME} "
        f"({int(MIN_TOPUP_AMOUNT * HB_RATE_SUM):,} so'm)\n\n"
        f"To'lov miqdorini kiriting"
    )
    await state.set_state(TopupStates.waiting_amount)
    await callback.message.answer(text, reply_markup=back_kb())
    await callback.answer()


@router.message(TopupStates.waiting_amount)
async def topup_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")

    try:
        amount = float(text)
    except ValueError:
        await message.answer("Noto'g'ri summa. Raqam kiriting:")
        return

    if amount < MIN_TOPUP_AMOUNT:
        await message.answer(f"Minimal miqdor {MIN_TOPUP_AMOUNT} {CURRENCY_NAME}. Qaytadan kiriting:")
        return

    await state.update_data(amount=amount)
    await state.set_state(TopupStates.waiting_screenshot)
    await message.answer("To'lovni amalga oshirib, chekni yuboring.")


@router.message(TopupStates.waiting_screenshot, F.photo)
async def topup_screenshot(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data["amount"]
    screenshot_file_id = message.photo[-1].file_id

    topup = await db.create_topup(message.from_user.id, amount, screenshot_file_id)
    await state.clear()

    await message.answer("24 soat ichida mablag' tushadi.")

    username = f"@{message.from_user.username}" if message.from_user.username else "—"
    caption = (
        f"💳 <b>Yangi to'lov</b>\n\n"
        f"Foydalanuvchi: {username}\n"
        f"Foydalanuvchi ID: {message.from_user.id}\n"
        f"Summa: {amount} {CURRENCY_NAME}"
    )
    await bot.send_photo(
        ADMIN_ID,
        photo=screenshot_file_id,
        caption=caption,
        reply_markup=admin_topup_kb(topup["id"]),
    )


@router.message(TopupStates.waiting_screenshot)
async def topup_screenshot_invalid(message: Message):
    await message.answer("Iltimos, chekning rasmini yuboring.")