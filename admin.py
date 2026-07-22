from aiogram import Router, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_ID, CURRENCY_NAME
from states import AdminMessageStates

router = Router()
router.callback_query.filter(F.from_user.id == ADMIN_ID)
router.message.filter(F.from_user.id == ADMIN_ID)


# ---------- HB berish (yagona manba - admin qo'lda beradi) ----------

@router.message(Command("grant"))
async def grant_balance(message: Message, command: CommandObject, bot: Bot):
    if not command.args:
        await message.answer("Format: /grant <hisob_raqami> <miqdor>\nMasalan: /grant 022 5")
        return

    parts = command.args.split()
    if len(parts) != 2:
        await message.answer("Format: /grant <hisob_raqami> <miqdor>\nMasalan: /grant 022 5")
        return

    account_number, amount_text = parts

    if not account_number.isdigit() or len(account_number) != 3:
        await message.answer("Hisob raqami 3 xonali bo'lishi kerak (masalan: 022).")
        return

    try:
        amount = float(amount_text)
    except ValueError:
        await message.answer("Miqdor noto'g'ri. Raqam kiriting.")
        return

    user = await db.get_user_by_account(account_number)
    if not user:
        await message.answer("Bunday hisob raqamli foydalanuvchi topilmadi.")
        return

    await db.update_balance(user["user_id"], amount)
    await message.answer(f"✅ {account_number} raqamiga {amount} {CURRENCY_NAME} berildi.")

    try:
        await bot.send_message(user["user_id"], f"💰 Hisobingizga {amount} {CURRENCY_NAME} qo'shildi.")
    except Exception:
        pass


# ---------- Buyurtmalar (Do'kon) ----------

@router.callback_query(F.data.startswith("order_approve:"))
async def order_approve(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    order = await db.get_order(order_id)

    if not order or order["status"] != "pending":
        await callback.answer("Bu buyurtma allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_order_status(order_id, "approved")
    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ Tasdiqlandi")
    else:
        await callback.message.edit_text(callback.message.text + "\n\n✅ Tasdiqlandi")
    await callback.answer("Tasdiqlandi")

    await bot.send_message(order["user_id"], "✅ Sizning buyurtmangiz tasdiqlandi.")


@router.callback_query(F.data.startswith("order_reject:"))
async def order_reject(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split(":")[1])
    order = await db.get_order(order_id)

    if not order or order["status"] != "pending":
        await callback.answer("Bu buyurtma allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_order_status(order_id, "rejected")
    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Rad etildi")
    else:
        await callback.message.edit_text(callback.message.text + "\n\n❌ Rad etildi")
    await callback.answer("Rad etildi")

    await bot.send_message(order["user_id"], "❌ Sizning buyurtmangiz tasdiqlanmadi.")


@router.callback_query(F.data.startswith("order_msg:"))
async def order_msg_start(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split(":")[1])
    order = await db.get_order(order_id)

    if not order:
        await callback.answer("Buyurtma topilmadi.", show_alert=True)
        return

    await state.set_state(AdminMessageStates.waiting_message)
    await state.update_data(target_user_id=order["user_id"])
    await callback.message.answer("Foydalanuvchiga yuboriladigan xabarni yozing (istalgan turda):")
    await callback.answer()


# ---------- Adminning erkin xabari foydalanuvchiga ----------

@router.message(AdminMessageStates.waiting_message)
async def order_msg_send(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_user_id = data["target_user_id"]

    await bot.copy_message(
        chat_id=target_user_id,
        from_chat_id=message.chat.id,
        message_id=message.message_id,
    )
    await state.clear()
    await message.answer("Xabar yuborildi.")