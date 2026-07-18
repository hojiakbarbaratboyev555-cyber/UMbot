from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

import database as db
from config import ADMIN_ID, CURRENCY_NAME
from rate import get_hb_rate_sum
from keyboards import product_buy_kb, admin_order_kb, back_kb

router = Router()


@router.message(F.text == "🛍 Do'kon")
async def show_shop(message: Message):
    products = await db.get_active_products()

    if not products:
        await message.answer("Hozircha mahsulotlar mavjud emas.")
        return

    rate = await get_hb_rate_sum()

    await message.answer("Mahsulotlar ro'yxati:", reply_markup=back_kb())

    for p in products:
        price_sum = float(p["price"])
        price_hb = round(price_sum / rate, 4) if rate else 0

        caption = (
            f"<b>{p['name']}</b>\n\n"
            f"{p['description'] or ''}\n\n"
            f"💰 Narxi: {price_sum:,.0f} so'm (≈ {price_hb} {CURRENCY_NAME})"
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

    # Xarid vaqtidagi ENG joriy TON kursi bo'yicha qayta hisoblaymiz
    rate = await get_hb_rate_sum()
    price_sum = float(product["price"])
    price_hb = round(price_sum / rate, 4) if rate else 0

    user = await db.get_user(callback.from_user.id)

    if float(user["balance"]) < price_hb:
        await callback.answer("❌ Mablag' yetarli emas", show_alert=True)
        return

    # Mablag'ni darhol yechib qo'yamiz (tasdiqlanmasa ham qaytmaydi)
    await db.update_balance(user["user_id"], -price_hb)
    order = await db.create_order(user["user_id"], product["id"], price_hb)

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
        f"Narx: {price_sum:,.0f} so'm ({price_hb} {CURRENCY_NAME} yechildi)"
    )
    await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_order_kb(order["id"]))