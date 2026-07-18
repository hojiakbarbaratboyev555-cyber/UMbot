from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import (
    CURRENCY_NAME,
    MIN_TRANSFER_AMOUNT,
    TRANSFER_COMMISSION_PERCENT,
    ADMIN_ID,
    HB_RATE_SUM,
    MIN_TOPUP_AMOUNT,
    PAYMENT_CARD_NUMBER,
    PAYMENT_CARD_OWNER,
    MIN_WITHDRAW_AMOUNT,
    WITHDRAW_COMMISSION_PERCENT,
)
from keyboards import account_kb, transfer_confirm_kb, admin_topup_kb, admin_withdraw_kb, back_kb
from states import TransferStates, TopupStates, WithdrawStates

router = Router()


@router.message(F.text == "👤 Hisobim")
async def show_account(message: Message):
    user = await db.get_user(message.from_user.id)
    balance_sum = int(float(user["balance"]) * HB_RATE_SUM)

    text = (
        f"👤 Ism: {user['full_name']}\n"
        f"🔢 Hisob raqam: {user['account_number']}\n"
        f"💰 Balans: {user['balance']} {CURRENCY_NAME} (≈ {balance_sum:,} so'm)"
    )
    await message.answer(text, reply_markup=account_kb())


# ==================== O'TKAZMA ====================

@router.callback_query(F.data == "transfer_start")
async def transfer_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TransferStates.waiting_account_number)
    await callback.message.answer("Qabul qiluvchining hisob raqamini kiriting:")
    await callback.answer()


@router.message(TransferStates.waiting_account_number)
async def transfer_account_number(message: Message, state: FSMContext):
    text = message.text.strip()

    if not text.isdigit() or len(text) != 3:
        await message.answer(
            "Noto'g'ri format. Hisob raqami aynan 3 xonali son bo'lishi kerak (masalan: 022)."
        )
        return

    receiver = await db.get_user_by_account(text)
    if not receiver:
        await message.answer("Bunday hisob raqam topilmadi. Qaytadan kiriting:")
        return

    if receiver["user_id"] == message.from_user.id:
        await message.answer("O'zingizga o'tkazma qila olmaysiz. Boshqa hisob raqam kiriting:")
        return

    await state.update_data(receiver_account=text, receiver_id=receiver["user_id"], receiver_name=receiver["full_name"])
    await state.set_state(TransferStates.waiting_amount)
    await message.answer(f"Summani kiriting (min {MIN_TRANSFER_AMOUNT} {CURRENCY_NAME}):")


@router.message(TransferStates.waiting_amount)
async def transfer_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")

    try:
        amount = float(text)
    except ValueError:
        await message.answer("Noto'g'ri summa. Raqam kiriting:")
        return

    if amount < MIN_TRANSFER_AMOUNT:
        await message.answer(f"Minimal o'tkazma miqdori {MIN_TRANSFER_AMOUNT} {CURRENCY_NAME}. Qaytadan kiriting:")
        return

    user = await db.get_user(message.from_user.id)
    if float(user["balance"]) < amount:
        await message.answer("❌ Mablag' yetarli emas. Qaytadan summa kiriting:")
        return

    data = await state.get_data()
    await state.update_data(amount=amount)
    await state.set_state(TransferStates.waiting_confirm)

    text_out = (
        f"📤 O'tkazma\n\n"
        f"ISM: {data['receiver_name']}\n"
        f"RAQAM: {data['receiver_account']}\n"
        f"Summa: {amount} {CURRENCY_NAME}\n\n"
        f"Hisobingiz: {user['balance']} {CURRENCY_NAME}\n\n"
        f"Agar rozi bo'lsangiz, tasdiqlash tugmasini bosing."
    )
    await message.answer(text_out, reply_markup=transfer_confirm_kb())


@router.callback_query(TransferStates.waiting_confirm, F.data == "transfer_confirm")
async def transfer_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data["amount"]
    receiver_id = data["receiver_id"]

    sender = await db.get_user(callback.from_user.id)
    if float(sender["balance"]) < amount:
        await callback.answer("❌ Mablag' yetarli emas", show_alert=True)
        await state.clear()
        return

    commission = round(amount * TRANSFER_COMMISSION_PERCENT / 100, 2)
    receiver_amount = round(amount - commission, 2)

    await db.update_balance(callback.from_user.id, -amount)
    await db.update_balance(receiver_id, receiver_amount)
    await db.update_balance(ADMIN_ID, commission)
    await db.create_transfer(callback.from_user.id, receiver_id, amount, commission)

    await state.clear()
    await callback.message.edit_text("✅ O'tkazma muvaffaqiyatli amalga oshirildi.")
    await callback.answer()

    try:
        await bot.send_message(
            receiver_id,
            f"💸 Hisobingizga {receiver_amount} {CURRENCY_NAME} tushdi.",
        )
    except Exception:
        pass


@router.callback_query(TransferStates.waiting_confirm, F.data == "transfer_cancel")
async def transfer_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("O'tkazma bekor qilindi.")
    await callback.answer()


# ==================== PUL KIRITISH ====================

@router.callback_query(F.data == "topup_start")
async def topup_start(callback: CallbackQuery, state: FSMContext):
    min_sum = int(MIN_TOPUP_AMOUNT * HB_RATE_SUM)
    text = (
        f"Qabul qiluvchi:\n"
        f"Karta: {PAYMENT_CARD_NUMBER}\n"
        f"Ism: {PAYMENT_CARD_OWNER}\n"
        f"Min summa: {MIN_TOPUP_AMOUNT} {CURRENCY_NAME} ({min_sum:,} so'm)\n\n"
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


# ==================== PUL CHIQARISH ====================

@router.callback_query(F.data == "withdraw_start")
async def withdraw_start(callback: CallbackQuery, state: FSMContext):
    text = (
        f"Min: {MIN_WITHDRAW_AMOUNT} {CURRENCY_NAME}\n"
        f"Komissiya: {WITHDRAW_COMMISSION_PERCENT}%\n\n"
        f"Pulni chiqarmoqchi bo'lgan karta raqamingizni kiriting (16 xonali, faqat so'mda ishlaydigan karta):"
    )
    await state.set_state(WithdrawStates.waiting_card)
    await callback.message.answer(text, reply_markup=back_kb())
    await callback.answer()


@router.message(WithdrawStates.waiting_card)
async def withdraw_card(message: Message, state: FSMContext):
    card = message.text.strip().replace(" ", "")

    if not card.isdigit() or len(card) != 16:
        await message.answer(
            "Noto'g'ri format. Karta raqami aynan 16 xonali son bo'lishi kerak. Qaytadan kiriting:"
        )
        return

    await state.update_data(card_number=card)
    await state.set_state(WithdrawStates.waiting_amount)
    await message.answer(f"Yechmoqchi bo'lgan summani {CURRENCY_NAME} da kiriting (min: {MIN_WITHDRAW_AMOUNT}):")


@router.message(WithdrawStates.waiting_amount)
async def withdraw_amount(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip().replace(",", ".")

    try:
        amount = float(text)
    except ValueError:
        await message.answer("Noto'g'ri summa. Raqam kiriting:")
        return

    if amount < MIN_WITHDRAW_AMOUNT:
        await message.answer(f"Minimal miqdor {MIN_WITHDRAW_AMOUNT} {CURRENCY_NAME}. Qaytadan kiriting:")
        return

    user = await db.get_user(message.from_user.id)
    if float(user["balance"]) < amount:
        await message.answer("❌ Mablag' yetarli emas. Qaytadan summa kiriting:")
        return

    data = await state.get_data()
    card_number = data["card_number"]

    # Summa hisobdan darhol yechiladi
    await db.update_balance(message.from_user.id, -amount)
    withdrawal = await db.create_withdrawal(message.from_user.id, amount, card_number)

    await state.clear()
    await message.answer("24 soat ichida to'lov qilinadi.")

    payout_sum = int(amount * HB_RATE_SUM * (1 - WITHDRAW_COMMISSION_PERCENT / 100))
    username = f"@{message.from_user.username}" if message.from_user.username else "—"
    admin_text = (
        f"💸 <b>Yangi pul chiqarish so'rovi</b>\n\n"
        f"Foydalanuvchi: {username}\n"
        f"Foydalanuvchi ID: {message.from_user.id}\n"
        f"Summa: {amount} {CURRENCY_NAME}\n"
        f"Karta: {card_number}\n"
        f"To'lanadigan summa (komissiyadan keyin): {payout_sum:,} so'm"
    )
    await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_withdraw_kb(withdrawal["id"]))