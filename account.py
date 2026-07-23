from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from config import CURRENCY_NAME, MIN_TRANSFER_AMOUNT, TRANSFER_COMMISSION_PERCENT, ADMIN_ID
from items import format_inventory_table
from keyboards import account_kb, transfer_confirm_kb
from states import TransferStates

router = Router()


@router.message(F.text == "👤 Hisobim")
async def show_account(message: Message):
    user = await db.get_user(message.from_user.id)
    inventory = await db.get_user_inventory(message.from_user.id)

    text = (
        f"<blockquote>👤 Ism: {user['full_name']}\n"
        f"🔢 Hisob raqam: {user['account_number']}\n"
        f"💰 Balans: {user['balance']} {CURRENCY_NAME}</blockquote>\n\n"
        f"{format_inventory_table(inventory)}"
    )
    await message.answer(text, reply_markup=account_kb())


# ==================== O'TKAZMA ====================

@router.callback_query(F.data == "transfer_start")
async def transfer_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TransferStates.waiting_account_number)
    await callback.message.answer("<blockquote>⚖️Eslatma:Har bir oʻtkazma 10% komissiya oladi.\nMasalan:\nSiz 2HB oʻtkazasiz qabul qiluvchiga 1.8HB tushadi</blockquote>\n\nQabul qiluvchining hisob raqamini kiriting")
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
    await message.answer(f"<blockquote>Oʻtkazmoqchi boʻlgan miqdorni kiriting (min {MIN_TRANSFER_AMOUNT} {CURRENCY_NAME}):</blockquote>")


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
        f"<blockquote>📤 O'tkazma\n\n"
        f"ISM: {data['receiver_name']}\n"
        f"RAQAM: {data['receiver_account']}\n"
        f"Summa: {amount} {CURRENCY_NAME}\n\n"
        f"Hisobingiz: {user['balance']} {CURRENCY_NAME}</blockquote>\n\n"
        f"<blockquote>Agar rozi bo'lsangiz, tasdiqlash tugmasini bosing.</blockquote>"
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
    await callback.message.edit_text("<blockquote>✅ O'tkazma muvaffaqiyatli amalga oshirildi.</blockquote>")
    await callback.answer()

    try:
        await bot.send_message(
            receiver_id,
            f"<blockquote>💸 Hisobingizga {receiver_amount} {CURRENCY_NAME} tushdi.</blockquote>",
        )
    except Exception:
        pass


@router.callback_query(TransferStates.waiting_confirm, F.data == "transfer_cancel")
async def transfer_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("<blockquote>O'tkazma bekor qilindi.</blockquote>")
    await callback.answer()