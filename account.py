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


@router.message(F.text == "👤 𝗛𝗶𝘀𝗼𝗯𝗶𝗺")
async def show_account(message: Message):
    user = await db.get_user(message.from_user.id)
    balance_sum = int(float(user["balance"]) * HB_RATE_SUM)

    text = (
        f"👤𝗜𝘀𝗺: {user['full_name']}\n\n"
        f"💳𝗛𝗶𝘀𝗼𝗯 𝗿𝗮𝗾𝗮𝗺: {user['account_number']}\n"
        f"💰𝗕𝗮𝗹𝗮𝗻𝘀: {user['balance']} {CURRENCY_NAME} (≈ {balance_sum:,} so'm)"
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
        await message.answer("❌ 𝗛𝗶𝘀𝗼𝗯𝗶𝗻𝗴𝗶𝘇𝗱𝗮 𝗺𝗮𝗯𝗹𝗮𝗴ʼ 𝘆𝗲𝘁𝗮𝗿𝗹𝗶 𝗲𝗺𝗮𝘀:")
        return

    data = await state.get_data()
    await state.update_data(amount=amount)
    await state.set_state(TransferStates.waiting_confirm)

    text_out = (
        f"📤𝗢ʼ𝘁𝗸𝗮𝘇𝗺𝗮\n\n"
        f"👔𝗜𝘀𝗺: {data['receiver_name']}\n"
        f"💳𝗛𝗶𝘀𝗼𝗯 𝗿𝗮𝗾𝗮𝗺𝗶: {data['receiver_account']}\n"
        f"Summa: {amount} {CURRENCY_NAME}\n\n"
        f"💰𝗛𝗶𝘀𝗼𝗯𝗶𝗻𝗴𝗶𝘇: {user['balance']} {CURRENCY_NAME}\n\n"
        f"𝗠𝗮ʼ𝗹𝘂𝗺𝗼𝘁𝗹𝗮𝗿 𝘁𝗼ʼ𝗴ʼ𝗿𝗶𝗹𝗶𝗴𝗶𝗻𝗶 𝘁𝗮𝘀𝗱𝗶𝗾𝗹𝗮𝗻𝗴."
    )
    await message.answer(text_out, reply_markup=transfer_confirm_kb())


@router.callback_query(TransferStates.waiting_confirm, F.data == "transfer_confirm")
async def transfer_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data["amount"]
    receiver_id = data["receiver_id"]

    sender = await db.get_user(callback.from_user.id)
    if float(sender["balance"]) < amount:
        await callback.answer("❌ 𝗛𝗶𝘀𝗼𝗯𝗶𝗻𝗴𝗶𝘇𝗱𝗮 𝗺𝗮𝗯𝗹𝗮𝗴ʼ 𝘆𝗲𝘁𝗮𝗿𝗹𝗶 𝗲𝗺𝗮𝘀", show_alert=True)
        await state.clear()
        return

    commission = round(amount * TRANSFER_COMMISSION_PERCENT / 100, 2)
    receiver_amount = round(amount - commission, 2)

    await db.update_balance(callback.from_user.id, -amount)
    await db.update_balance(receiver_id, receiver_amount)
    await db.update_balance(ADMIN_ID, commission)
    await db.create_transfer(callback.from_user.id, receiver_id, amount, commission)

    await state.clear()
    await callback.message.edit_text("✅ 𝗠𝘂𝘃𝗮𝗳𝗳𝗮𝗾𝗶𝘆𝗮𝘁𝗹𝗶 𝗮𝗺𝗮𝗹𝗴𝗮 𝗼𝘀𝗵𝗶𝗿𝗶𝗹𝗱𝗶")
    await callback.answer()

    try:
        await bot.send_message(
            receiver_id,
            f"💸 𝗛𝗶𝘀𝗼𝗯𝗶𝗻𝗴𝗶𝘇 {receiver_amount} {CURRENCY_NAME}𝗴𝗮 𝘁𝗼ʼ𝗹𝗱𝗶𝗿𝗶𝗹𝗱𝗶.",
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
        f"📬𝗤𝗮𝗯𝘂𝗹 𝗾𝗶𝗹𝘂𝘃𝗰𝗵𝗶:\n"
        f"💳𝗞𝗮𝗿𝘁𝗮: {PAYMENT_CARD_NUMBER}\n"
        f"🤵𝗜𝘀𝗺: {PAYMENT_CARD_OWNER}\n"
        f"⬇️𝗠𝗶𝗻 𝘀𝘂𝗺𝗺𝗮: {MIN_TOPUP_AMOUNT} {CURRENCY_NAME} ({min_sum:,} 𝘀𝘂𝗺)\n\n"
        f"𝗤𝗮𝗻𝗰𝗵𝗮 𝘁𝗼ʼ𝗹𝗮𝗺𝗼𝗾𝗰𝗵𝗶 𝗯𝗼ʼ𝗹𝘀𝗮𝗻𝗴𝗶𝘇 {CURRENCY_NAME}𝗱𝗮 𝘆𝗼𝘇𝗶𝗻𝗴"
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
        await message.answer(f"𝗠𝗶𝗻𝗶𝗺𝘂𝗺 𝗾𝗶𝘆𝗺𝗮𝘁 {MIN_TOPUP_AMOUNT} {CURRENCY_NAME}. 𝗤𝗮𝘆𝘁𝗮𝗱𝗮𝗻 𝗸𝗶𝗿𝗶𝘁𝗶𝗻𝗴 𝘆𝗼𝗸𝗶 /start 𝗯𝗼𝘀𝗶𝗻𝗴:")
        return

    await state.update_data(amount=amount)
    await state.set_state(TopupStates.waiting_screenshot)
    await message.answer("𝗧𝗼ʼ𝗹𝗼𝘃𝗻𝗶 𝗮𝗺𝗮𝗹𝗴𝗮 𝗼𝘀𝗵𝗶𝗿𝗴𝗮𝗻𝗱𝗮𝗻 𝘀𝗼ʼ𝗻𝗴 𝗰𝗵𝗲𝗰𝗸 𝗿𝗮𝘀𝗺𝗶𝗻𝗶 𝘆𝘂𝗯𝗼𝗿𝗶𝗻𝗴.")


@router.message(TopupStates.waiting_screenshot, F.photo)
async def topup_screenshot(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data["amount"]
    screenshot_file_id = message.photo[-1].file_id

    topup = await db.create_topup(message.from_user.id, amount, screenshot_file_id)
    await state.clear()

    await message.answer("⏳ 𝗛𝗶𝘀𝗼𝗯𝗶𝗻𝗴𝗶𝘇 24 𝘀𝗼𝗮𝘁 𝗶𝗰𝗵𝗶𝗱𝗮 𝘁𝗼ʼ𝗹𝗱𝗶𝗿𝗶𝗹𝗮𝗱𝗶.")

    username = f"@{message.from_user.username}" if message.from_user.username else "—"
    caption = (
        f"💳 <b>𝗬𝗮𝗻𝗴𝗶 𝘁𝗼ʼ𝗹𝗼𝘃</b>\n\n"
        f"𝗙𝗼𝘆𝗱𝗮𝗹𝗮𝗻𝘂𝘃𝗰𝗵𝗶: {username}\n"
        f"𝗜𝗗si: {message.from_user.id}\n"
        f"𝗠𝗶𝗾𝗱𝗼𝗿: {amount} {CURRENCY_NAME}"
    )
    await bot.send_photo(
        ADMIN_ID,
        photo=screenshot_file_id,
        caption=caption,
        reply_markup=admin_topup_kb(topup["id"]),
    )


@router.message(TopupStates.waiting_screenshot)
async def topup_screenshot_invalid(message: Message):
    await message.answer("𝗖𝗵𝗲𝗸 𝗿𝗮𝘀𝗺𝗶𝗻𝗶 𝘆𝘂𝗯𝗼𝗿𝗶𝗻𝗴")


# ==================== PUL CHIQARISH ====================

@router.callback_query(F.data == "withdraw_start")
async def withdraw_start(callback: CallbackQuery, state: FSMContext):
    text = (
        f"𝗠𝗶𝗻𝗶𝗺𝘂𝗺: {MIN_WITHDRAW_AMOUNT} {CURRENCY_NAME}\n"
        f"𝗞𝗼𝗺𝗶𝘀𝘀𝗶𝘆𝗮: {WITHDRAW_COMMISSION_PERCENT}%\n\n"
        f"𝗞𝗮𝗿𝘁𝗮 𝗿𝗮𝗾𝗮𝗺𝗶𝗻𝗴𝗶𝘇𝗻𝗶 𝗸𝗶𝗿𝗶𝘁𝗻𝗴 (16 xonali, faqat so'mda ishlaydigan karta):"
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