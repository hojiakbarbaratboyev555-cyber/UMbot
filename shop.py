from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery

import database as db
from config import ADMIN_ID, CURRENCY_NAME
from items import ITEMS
from rate_assets import get_item_hb_price
from keyboards import product_buy_kb, admin_order_kb, back_kb, item_trade_kb

router = Router()

SELL_DISCOUNT_PERCENT = 10  # sotish narxi xarid narxidan shuncha % kam


@router.message(F.text == "🛍 Do'kon")
async def show_shop(message: Message):
    products = await db.get_active_products()

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

    # Real aktivlarga bog'langan buyumlar
    for item in ITEMS:
        buy_price = await get_item_hb_price(item)
        sell_price = round(buy_price * (1 - SELL_DISCOUNT_PERCENT / 100), 4)

        text = (
            f"{item['emoji']} <b>{item['label']}</b>\n\n"
            f"<blockquote>Sotib olish narxi: {buy_price} {CURRENCY_NAME}\n"
            f"Sotish narxi: {sell_price} {CURRENCY_NAME}</blockquote>"
        )
        await message.answer(text, reply_markup=item_trade_kb(item["key"]))


@router.callback_query(F.data.startswith("buy:"))
async def buy_product(callback: CallbackQuery, bot: Bot):
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)

    if not product or not product["active"]:
        await callback.answer("Mahsulot mavjud emas.", show_alert=True)
        return

    price_hb = float(product["price"])
    user = await db.get_user(callback.from_user.id)

    if float(user["balance"]) < price_hb:
        await callback.answer("❌ Mablag' yetarli emas", show_alert=True)
        return

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
        f"Narx: {price_hb} {CURRENCY_NAME}"
    )
    await bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_order_kb(order["id"]))


@router.callback_query(F.data.startswith("buy_item:"))
async def buy_item(callback: CallbackQuery):
    item_key = callback.data.split(":", 1)[1]
    item = next((i for i in ITEMS if i["key"] == item_key), None)

    if not item:
        await callback.answer("Buyum mavjud emas.", show_alert=True)
        return

    price_hb = await get_item_hb_price(item)
    user = await db.get_user(callback.from_user.id)

    if float(user["balance"]) < price_hb:
        await callback.answer("❌ Mablag' yetarli emas", show_alert=True)
        return

    await db.update_balance(user["user_id"], -price_hb)
    await db.add_item_to_inventory(user["user_id"], item_key, 1)

    await callback.answer(f"✅ {item['emoji']} {item['label']} sotib olindi! (-{price_hb} {CURRENCY_NAME})", show_alert=True)


@router.callback_query(F.data.startswith("sell_item:"))
async def sell_item(callback: CallbackQuery):
    item_key = callback.data.split(":", 1)[1]
    item = next((i for i in ITEMS if i["key"] == item_key), None)

    if not item:
        await callback.answer("Buyum mavjud emas.", show_alert=True)
        return

    removed = await db.remove_item_from_inventory(callback.from_user.id, item_key, 1)
    if not removed:
        await callback.answer("❌ Sizda bu buyum yo'q.", show_alert=True)
        return

    buy_price = await get_item_hb_price(item)
    sell_price = round(buy_price * (1 - SELL_DISCOUNT_PERCENT / 100), 4)

    await db.update_balance(callback.from_user.id, sell_price)

    await callback.answer(f"✅ {item['emoji']} {item['label']} sotildi! (+{sell_price} {CURRENCY_NAME})", show_alert=True)