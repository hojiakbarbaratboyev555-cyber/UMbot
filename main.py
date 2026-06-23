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

# ───────── START ─────────
@dp.message(CommandStart())
async def start(m: Message):
    await get_balance(m.from_user.id)
    await m.answer("👋 UM Bot ishlayapti")

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

    bal = await get_balance(m.from_user.id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Do‘kon", callback_data="shop")]
    ])

    await m.answer(
        f"Hisob: {bal} 🅤🅜",
        reply_markup=kb
    )

@dp.callback_query(F.data == "shop")
async def shop_open(c: CallbackQuery):

    await c.answer()  # 🔥 FIX (MUHIM)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎟 Premium = 2 🅤🅜", callback_data="p1")],
        [InlineKeyboardButton(text="⭐ Stars = 0.15", callback_data="p2")],
        [InlineKeyboardButton(text="🪙 Bot puli = 0.07", callback_data="p3")],
        [InlineKeyboardButton(text="💎 Olmos = 0.01", callback_data="p4")],
        [InlineKeyboardButton(text="🇺🇸 USA = 0.1", callback_data="p5")]
    ])

    await c.message.edit_text(
        "🛒 DO‘KON",
        reply_markup=kb
    )

# ───────── BUY UM ─────────
@dp.callback_query(F.data == "buy_um")
async def buy_um(c: CallbackQuery):
    buy_state[c.from_user.id] = "amount"
    await c.message.edit_text("💰 Miqdor kiriting (min 0.01)")

# ───────── AMOUNT ─────────
@dp.message(F.text)
async def amount_handler(m: Message):
    if m.from_user.id not in buy_state:
        return

    if buy_state[m.from_user.id] != "amount":
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
    print("RECEIPT TRIGGERED")  # 🔥 DEBUG FIX

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

# ───────── APPROVE ─────────
@dp.callback_query(F.data.startswith("ok_"))
async def ok(c: CallbackQuery):

    await c.answer()  # 🔥 FIX

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

    await c.answer()  # 🔥 FIX

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
        f"💸 Transfer\n{m.from_user.full_name} ➝ {m.reply_to_message.from_user.full_name}\n{amount} 🅤🅜"
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
