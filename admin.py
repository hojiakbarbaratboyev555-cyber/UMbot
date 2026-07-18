from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

import database as db
from config import ADMIN_ID, CURRENCY_NAME
from states import AdminMessageStates

router = Router()
router.callback_query.filter(F.from_user.id == ADMIN_ID)
router.message.filter(F.from_user.id == ADMIN_ID)


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


# ---------- To'lovlar (Pul kiritish) ----------

@router.callback_query(F.data.startswith("topup_approve:"))
async def topup_approve(callback: CallbackQuery, bot: Bot):
    topup_id = int(callback.data.split(":")[1])
    topup = await db.get_topup(topup_id)

    if not topup or topup["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_topup_status(topup_id, "approved")
    await db.update_balance(topup["user_id"], topup["amount"])

    await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ Tasdiqlandi")
    await callback.answer("Tasdiqlandi")

    await bot.send_message(
        topup["user_id"],
        f"✅ Hisobingizga {topup['amount']} {CURRENCY_NAME} qo'shildi.",
    )


@router.callback_query(F.data.startswith("topup_reject:"))
async def topup_reject(callback: CallbackQuery, bot: Bot):
    topup_id = int(callback.data.split(":")[1])
    topup = await db.get_topup(topup_id)

    if not topup or topup["status"] != "pending":
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_topup_status(topup_id, "rejected")
    await callback.message.edit_caption(caption=callback.message.caption + "\n\n❌ Rad etildi")
    await callback.answer("Rad etildi")

    await bot.send_message(topup["user_id"], "❌ To'lovingiz tasdiqlanmadi.")


# ---------- Pul chiqarish ----------

@router.callback_query(F.data.startswith("withdraw_approve:"))
async def withdraw_approve(callback: CallbackQuery, bot: Bot):
    withdrawal_id = int(callback.data.split(":")[1])
    withdrawal = await db.get_withdrawal(withdrawal_id)

    if not withdrawal or withdrawal["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_withdrawal_status(withdrawal_id, "approved")

    if callback.message.caption:
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ Tasdiqlandi")
    else:
        await callback.message.edit_text(callback.message.text + "\n\n✅ Tasdiqlandi")
    await callback.answer("Tasdiqlandi")

    await bot.send_message(withdrawal["user_id"], "✅ Pul tushdi.")


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