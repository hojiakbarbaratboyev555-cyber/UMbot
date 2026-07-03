import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

import database as db
import keyboards as kb
from config import BOT_TOKEN, ADMIN_ID, WEBHOOK_URL, WEBHOOK_PATH, PORT
from states import TopupState, TransferState, BroadcastState
from utils import (
    format_money,
    format_date,
    parse_positive_int,
    is_valid_card,
    split_semicolon_args,
    transaction_line,
)

logging.basicConfig(level=logging.INFO)
router = Router()


def is_admin(telegram_id: int) -> bool:
    return ADMIN_ID != 0 and telegram_id == ADMIN_ID


# ============================================================
# /start
# ============================================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    await message.answer(
        "Assalomu alaykum! 👋 <b>UM Wallet</b> botiga xush kelibsiz.\n\n"
        f"💳 Sizning UM karta raqamingiz: <code>{user['card_number']}</code>\n\n"
        "🏠 Asosiy — profil va balans\n"
        "🛒 Do'kon — mahsulot xarid qilish\n"
        "💸 O'tkazma — boshqa foydalanuvchiga UM yuborish\n"
        "⚙️ Sozlamalar — profil sozlamalari\n\n"
        "Quyidagi menyudan tanlang 👇",
        parse_mode="HTML",
        reply_markup=kb.main_menu,
    )


@router.message(F.text == "❌ Bekor qilish")
async def cancel_any(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=kb.main_menu)


# ============================================================
# 🏠 ASOSIY (profil)
# ============================================================

@router.message(F.text == "🏠 Asosiy")
async def profile(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    text = (
        "👤 <b>Sizning profilingiz</b>\n\n"
        f"Ism: {user['full_name']}\n"
        f"Username: @{user['username'] or '—'}\n"
        f"Telegram ID: <code>{user['telegram_id']}</code>\n"
        f"💳 UM karta: <code>{user['card_number']}</code>\n"
        f"💰 Balans: <b>{format_money(user['balance'])} UM</b>\n"
        f"📅 Ro'yxatdan o'tgan: {format_date(user['created_at'])}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb.profile_inline())


@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery):
    txs = await db.get_last_transactions(callback.from_user.id)
    if not txs:
        await callback.message.answer("Hozircha tranzaksiyalar yo'q.")
        await callback.answer()
        return
    lines = ["📜 <b>So'nggi tranzaksiyalar</b> (oxirgi 20 ta):\n"]
    for tx in txs:
        lines.append(transaction_line(tx, callback.from_user.id))
    await callback.message.answer("\n".join(lines), parse_mode="HTML")
    await callback.answer()


# ============================================================
# ➕ UM sotib olish (screenshot orqali)
# ============================================================

@router.callback_query(F.data == "topup_start")
async def topup_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TopupState.waiting_amount)
    await callback.message.answer(
        "Qancha UM sotib olmoqchisiz? Miqdorni raqamda kiriting (masalan: 50000).",
        reply_markup=kb.cancel_menu,
    )
    await callback.answer()


@router.message(TopupState.waiting_amount)
async def topup_amount(message: Message, state: FSMContext):
    amount = parse_positive_int(message.text)
    if amount is None:
        await message.answer("Iltimos, musbat butun son kiriting.")
        return
    await state.update_data(amount=amount)
    await state.set_state(TopupState.waiting_screenshot)
    await message.answer(
        f"{format_money(amount)} UM uchun to'lov chekini (screenshot) rasm sifatida yuboring.",
        reply_markup=kb.cancel_menu,
    )


@router.message(TopupState.waiting_screenshot, F.photo)
async def topup_screenshot(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    amount = data["amount"]
    photo_file_id = message.photo[-1].file_id

    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    request_id = await db.create_topup_request(message.from_user.id, amount, photo_file_id)
    await state.clear()
    await message.answer(
        "✅ So'rovingiz qabul qilindi va admin ko'rib chiqishi uchun yuborildi. "
        "Tasdiqlangach balansingiz avtomatik to'ldiriladi.",
        reply_markup=kb.main_menu,
    )

    if ADMIN_ID:
        caption = (
            "🆕 <b>UM to'ldirish so'rovi</b>\n\n"
            f"Foydalanuvchi: {user['full_name']}\n"
            f"Username: @{user['username'] or '—'}\n"
            f"Telegram ID: <code>{user['telegram_id']}</code>\n"
            f"💳 Karta: <code>{user['card_number']}</code>\n"
            f"Miqdor: <b>{format_money(amount)} UM</b>"
        )
        await bot.send_photo(
            ADMIN_ID,
            photo=photo_file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb.admin_topup_inline(request_id),
        )


@router.message(TopupState.waiting_screenshot)
async def topup_screenshot_invalid(message: Message):
    await message.answer("Iltimos, to'lov chekini rasm (screenshot) shaklida yuboring.")


@router.callback_query(F.data.startswith("topupok_"))
async def topup_approve(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    request_id = int(callback.data.split("_")[1])
    req = await db.get_topup_request(request_id)
    if not req or req["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.update_balance(req["telegram_id"], req["amount"])
    await db.log_transaction("topup", req["amount"], None, req["telegram_id"], "UM sotib olindi")
    await db.set_topup_status(request_id, "approved")

    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n✅ <b>Tasdiqlandi</b>", parse_mode="HTML"
    )
    try:
        await bot.send_message(
            req["telegram_id"],
            f"✅ {format_money(req['amount'])} UM hisobingizga muvaffaqiyatli qo'shildi!",
        )
    except Exception:
        pass
    await callback.answer("Tasdiqlandi")


@router.callback_query(F.data.startswith("topupno_"))
async def topup_reject(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q.", show_alert=True)
        return
    request_id = int(callback.data.split("_")[1])
    req = await db.get_topup_request(request_id)
    if not req or req["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await db.set_topup_status(request_id, "rejected")
    await callback.message.edit_caption(
        caption=(callback.message.caption or "") + "\n\n❌ <b>Rad etildi</b>", parse_mode="HTML"
    )
    try:
        await bot.send_message(
            req["telegram_id"], f"❌ {format_money(req['amount'])} UM so'rovingiz rad etildi."
        )
    except Exception:
        pass
    await callback.answer("Rad etildi")


# ============================================================
# 🛒 DO'KON
# ============================================================

@router.message(F.text == "🛒 Do'kon")
async def shop(message: Message):
    products = await db.get_active_products()
    if not products:
        await message.answer("Hozircha do'konda mahsulot yo'q.")
        return
    await message.answer(
        "🛒 <b>Do'kon</b>\n\nMahsulotni tanlang:", parse_mode="HTML",
        reply_markup=kb.shop_inline(products),
    )


@router.callback_query(F.data.startswith("buy_"))
async def shop_buy_select(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = await db.get_product(product_id)
    if not product or not product["active"]:
        await callback.answer("Mahsulot topilmadi.", show_alert=True)
        return
    text = (
        f"<b>{product['name']}</b>\n{product['description'] or ''}\n\n"
        f"Narxi: <b>{format_money(product['price'])} UM</b>"
    )
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb.confirm_buy_inline(product_id))
    await callback.answer()


@router.callback_query(F.data.startswith("confirmbuy_"))
async def shop_buy_confirm(callback: CallbackQuery, bot: Bot):
    product_id = int(callback.data.split("_")[1])
    ok, result = await db.buy_product(callback.from_user.id, product_id)
    if ok:
        await callback.message.edit_text(f"✅ «{result['name']}» muvaffaqiyatli sotib olindi!")
        if ADMIN_ID:
            user = await db.get_user(callback.from_user.id)
            try:
                await bot.send_message(
                    ADMIN_ID,
                    "🛒 <b>Yangi xarid</b>\n\n"
                    f"Foydalanuvchi: {user['full_name']} (@{user['username'] or '—'})\n"
                    f"Mahsulot: {result['name']}\n"
                    f"Narx: {format_money(result['price'])} UM",
                    parse_mode="HTML",
                )
            except Exception:
                pass
    else:
        await callback.message.edit_text(f"❌ {result}")
    await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery):
    await callback.message.edit_text("Bekor qilindi.")
    await callback.answer()


# ============================================================
# 💸 O'TKAZMA (karta raqami orqali)
# ============================================================

@router.message(F.text == "💸 O'tkazma")
async def transfer_start(message: Message, state: FSMContext):
    await state.set_state(TransferState.waiting_card)
    await message.answer(
        "Qabul qiluvchining 6 xonali UM karta raqamini kiriting.",
        reply_markup=kb.cancel_menu,
    )


@router.message(TransferState.waiting_card)
async def transfer_card(message: Message, state: FSMContext):
    card = message.text.strip()
    if not is_valid_card(card):
        await message.answer("Karta raqami 6 ta raqamdan iborat bo'lishi kerak. Qayta kiriting.")
        return
    receiver = await db.get_user_by_card(card)
    if not receiver:
        await message.answer("Bunday karta raqami topilmadi. Qayta tekshirib kiriting.")
        return
    if receiver["telegram_id"] == message.from_user.id:
        await message.answer("O'zingizga o'tkazma qila olmaysiz. Boshqa karta kiriting.")
        return
    await state.update_data(receiver_card=card, receiver_telegram_id=receiver["telegram_id"],
                             receiver_name=receiver["full_name"])
    await state.set_state(TransferState.waiting_amount)
    await message.answer(f"Qabul qiluvchi: {receiver['full_name']}\n\nQancha UM o'tkazmoqchisiz?")


@router.message(TransferState.waiting_amount)
async def transfer_amount(message: Message, state: FSMContext):
    amount = parse_positive_int(message.text)
    if amount is None:
        await message.answer("Iltimos, musbat butun son kiriting.")
        return
    sender = await db.get_user(message.from_user.id)
    if sender["balance"] < amount:
        await message.answer(
            f"Balansingizda yetarli UM yo'q. Joriy balans: {format_money(sender['balance'])} UM.",
            reply_markup=kb.main_menu,
        )
        await state.clear()
        return
    data = await state.get_data()
    await state.update_data(amount=amount)
    await state.set_state(TransferState.confirming)
    await message.answer(
        f"Tasdiqlaysizmi?\n\n"
        f"👤 Qabul qiluvchi: {data['receiver_name']} ({data['receiver_card']})\n"
        f"💰 Miqdor: {format_money(amount)} UM",
        reply_markup=kb.confirm_transfer_inline(),
    )


@router.callback_query(TransferState.confirming, F.data == "transfer_confirm")
async def transfer_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    ok, result = await db.transfer_um(callback.from_user.id, data["receiver_card"], data["amount"])
    await state.clear()
    if ok:
        await callback.message.edit_text("✅ O'tkazma muvaffaqiyatli amalga oshirildi.")
        try:
            sender = await db.get_user(callback.from_user.id)
            await bot.send_message(
                result["telegram_id"],
                f"💸 Sizga {format_money(data['amount'])} UM keldi "
                f"({sender['full_name']} dan, karta {sender['card_number']}).",
            )
        except Exception:
            pass
    else:
        await callback.message.edit_text(f"❌ {result}")
    await callback.answer()


# ============================================================
# ⚙️ SOZLAMALAR
# ============================================================

@router.message(F.text == "⚙️ Sozlamalar")
async def settings(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    text = (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"Username: @{user['username'] or '—'}\n"
        f"Til: O'zbekcha\n"
        f"Bildirishnoma: {'yoqilgan ✅' if user['notifications'] else 'o‘chirilgan ❌'}\n"
        f"💳 UM karta: <code>{user['card_number']}</code>\n"
        f"Telegram ID: <code>{user['telegram_id']}</code>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb.settings_inline(bool(user["notifications"])))


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    new_state = not bool(user["notifications"])
    await db.set_notifications(callback.from_user.id, new_state)
    await callback.message.edit_reply_markup(reply_markup=kb.settings_inline(new_state))
    await callback.answer("Bildirishnoma yoqildi ✅" if new_state else "Bildirishnoma o'chirildi ❌")


# ============================================================
# ADMIN: MAHSULOTLAR
# ============================================================

@router.message(Command("addproduct"))
async def admin_add_product(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    parts = split_semicolon_args(command.args or "", 3)
    if not parts:
        await message.answer("Format: /addproduct Nomi; Narxi; Tavsifi")
        return
    name, price_str, description = parts[0], parts[1], parts[2]
    price = parse_positive_int(price_str)
    if price is None:
        await message.answer("Narx musbat butun son bo'lishi kerak.")
        return
    await db.add_product(name, price, description)
    await message.answer(f"✅ Mahsulot qo'shildi: {name} — {format_money(price)} UM")


@router.message(Command("editproduct"))
async def admin_edit_product(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    parts = split_semicolon_args(command.args or "", 4)
    if not parts:
        await message.answer("Format: /editproduct ID; Nomi; Narxi; Tavsifi")
        return
    id_str, name, price_str, description = parts[0], parts[1], parts[2], parts[3]
    if not id_str.isdigit():
        await message.answer("ID butun son bo'lishi kerak.")
        return
    price = parse_positive_int(price_str)
    if price is None:
        await message.answer("Narx musbat butun son bo'lishi kerak.")
        return
    ok = await db.edit_product(int(id_str), name, price, description)
    await message.answer("✅ Mahsulot yangilandi." if ok else "❌ Bunday ID topilmadi.")


@router.message(Command("deleteproduct"))
async def admin_delete_product(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Format: /deleteproduct ID")
        return
    ok = await db.delete_product(int(command.args.strip()))
    await message.answer("✅ Mahsulot o'chirildi." if ok else "❌ Bunday ID topilmadi.")


@router.message(Command("setprice"))
async def admin_set_price(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    parts = split_semicolon_args(command.args or "", 2)
    if not parts or not parts[0].isdigit():
        await message.answer("Format: /setprice ID; YangiNarx")
        return
    price = parse_positive_int(parts[1])
    if price is None:
        await message.answer("Narx musbat butun son bo'lishi kerak.")
        return
    ok = await db.set_product_price(int(parts[0]), price)
    await message.answer("✅ Narx yangilandi." if ok else "❌ Bunday ID topilmadi.")


@router.message(Command("enableproduct"))
async def admin_enable_product(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Format: /enableproduct ID")
        return
    ok = await db.toggle_product(int(command.args.strip()), True)
    await message.answer("✅ Mahsulot yoqildi." if ok else "❌ Bunday ID topilmadi.")


@router.message(Command("disableproduct"))
async def admin_disable_product(message: Message, command: CommandObject):
    if not is_admin(message.from_user.id):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Format: /disableproduct ID")
        return
    ok = await db.toggle_product(int(command.args.strip()), False)
    await message.answer("✅ Mahsulot o'chirildi (nofaol)." if ok else "❌ Bunday ID topilmadi.")


# ============================================================
# ADMIN: BALANS BOSHQARUVI
# ============================================================

@router.message(Command("addbalance"))
async def admin_add_balance_cmd(message: Message, command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    parts = split_semicolon_args(command.args or "", 2)
    if not parts or not parts[0].isdigit():
        await message.answer("Format: /addbalance TelegramID; Miqdor")
        return
    amount = parse_positive_int(parts[1])
    if amount is None:
        await message.answer("Miqdor musbat butun son bo'lishi kerak.")
        return
    telegram_id = int(parts[0])
    ok, msg = await db.admin_add_balance(telegram_id, amount)
    await message.answer(f"✅ {format_money(amount)} UM qo'shildi." if ok else f"❌ {msg}")
    if ok:
        try:
            await bot.send_message(telegram_id, f"✅ Hisobingizga {format_money(amount)} UM qo'shildi.")
        except Exception:
            pass


@router.message(Command("removebalance"))
async def admin_remove_balance_cmd(message: Message, command: CommandObject, bot: Bot):
    if not is_admin(message.from_user.id):
        return
    parts = split_semicolon_args(command.args or "", 2)
    if not parts or not parts[0].isdigit():
        await message.answer("Format: /removebalance TelegramID; Miqdor")
        return
    amount = parse_positive_int(parts[1])
    if amount is None:
        await message.answer("Miqdor musbat butun son bo'lishi kerak.")
        return
    telegram_id = int(parts[0])
    ok, msg = await db.admin_remove_balance(telegram_
