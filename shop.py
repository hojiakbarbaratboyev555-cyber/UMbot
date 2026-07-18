from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

import database as db
from config import ADMIN_ID, CURRENCY_NAME
from keyboards import product_buy_kb, admin_order_kb, back_kb

router = Router()


@router.message(F.text == "🛍 Do'kon")
async def show_shop(message: Message):
    products = await db.get_active_products()

    if not products:
        await message.answer("Hozircha mahsulotlar mavjud emas.")
        return

    await message.answer("Mahsulotlar ro'yxati:", reply_markup=back_kb())

    for p in products:
        caption = (
            f"<b>{p['name']}</b>\n\n"
            f"{p['description'] or ''}\n\n"
            f"💰 Narxi: {p['price']} {CURRENCY_NAME}"
        )
        if p["photo_file_id"]:
            await message.answer_photo(
                photo=p["photo_file_id"],
                caption=caption,
                reply_markup=product_buy_kb(p["id"]),
            )
        else:
            await message.answer(caption, reply_markup=product_buy_kb(p["id"]))


@router.callback_query(F.data.startswith("buy:"))
async def buy_product(callback: CallbackQuery, bot: Bot):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)

    if not product or not product["active"]:
        await callback.answer("Mahsulot mavjud emas.", show_alert=True)
        return

    user = await db.get_user(callback.from_user.id)

    if user["balance"] < product["price"]:
        await callback.answer("❌ Mablag' yetarli emas", show_alert=True)
        return

    # Mablag'ni darhol yechib qo'yamiz (tasdiqlanmasa ham qaytmaydi)
    await db.update_balance(user["user_id"], -product["price"])
    order = await db.create_order(user["user_id"], product["id"], product["price"])

    await callback.message.answer(
        "✅ Xarid muvaffaqiyatli amalga oshirildi. Natijani kuting."
    )
    await callback.answer()

    username = f"@{callback.from_user.username}" if callback.from_user.username else "—"
    admin_text = (
        f"🛒 <b>Yangi buyurtma</b>\n\n"
        f"Mahsulot: {product['name']}\n"
        f"Foydalanuvchi: {username}\n"
        f"Foydalanuvchi ID: {user['user_id']}\n"
        f"Narx: {product['price']} {CURRENCY_NAME}"
    )
    await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_order_kb(order["id"]))