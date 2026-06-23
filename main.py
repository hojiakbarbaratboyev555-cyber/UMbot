import os
import asyncio
import logging

import aiosqlite
from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, Update, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart

# ───────── CONFIG ─────────
BOT_TOKEN = "8139143734:AAGAIrIxS_etgzNF92ADU36lVpiIUZ6bQ-k"
ADMIN_ID = 8223476380
ASOSIY_ID = -1003680334929
GROUP_ID = -1003881398546
WEBHOOK_HOST = "https://umbot-foen.onrender.com"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

DB = "bot.db"

logging.basicConfig(level=logging.INFO)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# ───────── DB ─────────
async def init_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0
        )
        """)
        await db.commit()

async def get_balance(user_id: int):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()

        if row:
            return row[0]

        await db.execute("INSERT INTO users(user_id,balance) VALUES(?,0)", (user_id,))
        await db.commit()
        return 0

async def change_balance(user_id: int, amount: float):
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        INSERT INTO users(user_id,balance) VALUES(?,?)
        ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
        """, (user_id, amount, amount))
        await db.commit()

# ───────── STATE ─────────
buy_state = {}
shop_state = {}

# ───────── START ─────────
@dp.message(CommandStart())
async def start(m: Message):
    await get_balance(m.from_user.id)
    await m.answer(f"Assalomu alaykum {m.from_user.full_name}")

# ───────── PROFIL ─────────
@dp.message(Command("profil"))
async def profil(m: Message):
    if m.chat.type != "private":
        return

    bal = await get_balance(m.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🅤🅜 sotib olish", callback_data="buy_um")]
    ])

    await m.answer(
        f"👤 {m.from_user.full_name}\nHisob: {bal} 🅤🅜",
        reply_markup=kb
    )

# ───────── SHOP ─────────
@dp.message(Command("shop"))
async def shop(m: Message):
    if m.chat.type != "private":
        return

    shop_state[m.from_user.id] = True

    text = (
        "🛒 DO‘KON NARXLARI\n\n"
        "🎟 Premium = 2 🅤🅜\nBu boʻlimda sizga 3 oylik premium taqdim etiladi\n\n"
        "⭐ 50ta Stars = 0.15 🅤🅜\nBunda siz 50ta starsni 0.15🅤🅜 ga almashtirasiz\n\n"
        "🪙 Bot puli = 0.07 🅤🅜\nBu boʻlimda Universal mafia botining shaxsiy pul birligiga almashtirasiz 🅤🅜 ni 10=0.07\n\n"
        "💎 Olmos = 0.01 🅤🅜\nHuddi shu botning olmos tizimi 1ta olmos 0.01🅤🅜\n\n"
        "🇺🇸 USA = 0.1 🅤🅜\n1ta Amerika telegram raqami 0.1🅤🅜\n\n\n"
        "──────────────────\n"
        "Bu yerda har bir maxsulot uchun ajratilgan raqamlar ularni kiriting va sovgʻalarga ega boʻling (Eslatma:Raqamni kiritishingiz bilan buyurtma qabul qilinadi bekor qilib boʻlmaydi!)\n📌 Tanlang:\n"
        "1 - Premium\n"
        "2 - Stars\n"
        "3 - Bot puli\n"
        "4 - Olmos\n"
        "5 - USA"
    )

    await m.answer(text)

# ───────── BUY UM ─────────
@dp.callback_query(F.data == "buy_um")
async def buy_um(c: CallbackQuery):
    buy_state[c.from_user.id] = "amount"
    await c.message.edit_text(
        "Siz oʻz hisobingizga 🅤🅜 sotib olmoqdasiz\n\n"
        "1🅤🅜 = 100000 soʻm\n"
        "minimum: 0.01\n"
        "Karta: 9860196619854934\n"
        "Egasi: M.N\n\n"
        "💰 Miqdorni kiriting"
    )
    await c.answer()

# ───────── AMOUNT (FIXED) ─────────
@dp.message(F.text)
async def amount_handler(m: Message):
    if m.from_user.id not in buy_state:
        return

    if buy_state[m.from_user.id] != "amount":
        return

    # shop 1-5 bilan konflikt bo‘lmasligi uchun
    if m.text in ["1", "2", "3", "4", "5"]:
        return

    try:
        amount = float(m.text)
    except:
        return await m.answer("❌ Son kiriting")

    if amount < 0.01:
        return await m.answer("❌ Min 0.01 🅤🅜")

    buy_state[m.from_user.id] = amount
    await m.answer("📸 Chek yuboring")

# ───────── RECEIPT ─────────
@dp.message(F.photo)
async def receipt(m: Message):
    if m.from_user.id not in buy_state:
        return

    amount = buy_state[m.from_user.id]
    del buy_state[m.from_user.id]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"ok_{m.from_user.id}_{amount}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"no_{m.from_user.id}")
        ]
    ])

    await bot.send_photo(
        GROUP_ID,
        m.photo[-1].file_id,
        caption=f"🧾 To‘lov\nUser: {m.from_user.full_name}\nID: {m.from_user.id}\n{amount} 🅤🅜",
        reply_markup=kb
    )

    await m.answer("⏳ Tekshiruvga yuborildi")

# ───────── SHOP ITEMS (FIXED) ─────────
@dp.message(F.text.in_(["1", "2", "3", "4", "5"]))
async def shop_numbers(m: Message):
    if m.chat.type != "private":
        return

    if not shop_state.get(m.from_user.id):
        return

    data = {
        "1": "🎟 3 oylik Premium\nNarx: 2🅤🅜",
        "2": "⭐ 50 Stars\nNarx: 0.15🅤🅜",
        "3": "🪙 10k Bot puli\nNarx: 0.07🅤🅜",
        "4": "💎 1ta Olmos\nNarx: 0.01🅤🅜",
        "5": "🇺🇸 USA tg \nNarx: 0.1🅤🅜"
    }

    await m.answer(data[m.text])

# ───────── APPROVE ─────────
@dp.callback_query(F.data.startswith("ok_"))
async def ok(c: CallbackQuery):
    await c.answer()

    _, uid, amount = c.data.split("_")

    await change_balance(int(uid), float(amount))

    await bot.send_message(
        int(uid),
        f"Haridingiz tasdiqlandi ✅\n+{amount} 🅤🅜"
    )

    await c.message.edit_reply_markup()

# ───────── REJECT ─────────
@dp.callback_query(F.data.startswith("no_"))
async def no(c: CallbackQuery):
    await c.answer()

    uid = int(c.data.split("_")[1])

    await bot.send_message(uid, "Haridingiz tasdiqlanmadi ❌")

    await c.message.edit_reply_markup()

# ───────── /ma ─────────
@dp.message(Command("ma"))
async def ma(m: Message):
    if m.chat.id != ASOSIY_ID:
        return

    if not m.reply_to_message:
        return await m.reply("❌ Reply qiling")

    try:
        amount = float(m.text.split()[1])
    except:
        return await m.reply("❌ Miqdor kiriting")

    if amount < 0.0001:
        return await m.reply("❌ Min 0.0001")

    sender = m.from_user.id
    receiver = m.reply_to_message.from_user.id

    s_bal = await get_balance(sender)

    if s_bal < amount:
        return await m.reply("❌ Yetarli balans yo‘q")

    await change_balance(sender, -amount)
    await change_balance(receiver, amount)

    await m.reply(
        f"💸 O‘tkazma\n{m.from_user.full_name} ➝ {m.reply_to_message.from_user.full_name}\n{amount} 🅤🅜"
    )

# ───────── WEBHOOK ─────────
@app.on_event("startup")
async def startup():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)

@app.post(WEBHOOK_PATH)
async def webhook(req: Request):
    data = await req.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"ok": True}

@app.get("/")
async def home():
    return {"status": "running"}

# ───────── RUN ─────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
