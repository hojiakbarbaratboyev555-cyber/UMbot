import random
from datetime import datetime

import aiosqlite

from config import DB_PATH, CARD_LENGTH, HISTORY_LIMIT


# ============================================================
# INIT
# ============================================================

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            full_name TEXT,
            balance INTEGER NOT NULL DEFAULT 0,
            card_number TEXT UNIQUE NOT NULL,
            language TEXT NOT NULL DEFAULT 'uz',
            notifications INTEGER NOT NULL DEFAULT 1,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            amount INTEGER NOT NULL,
            sender_id INTEGER,
            receiver_id INTEGER,
            description TEXT,
            created_at TEXT NOT NULL
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS topup_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            photo_file_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )""")

        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""")

        await db.commit()


# ============================================================
# YORDAMCHI
# ============================================================

def _now():
    return datetime.now().isoformat(timespec="seconds")


async def _card_exists(db, card_number: str) -> bool:
    cur = await db.execute("SELECT 1 FROM users WHERE card_number = ?", (card_number,))
    return await cur.fetchone() is not None


async def generate_unique_card_number() -> str:
    async with aiosqlite.connect(DB_PATH) as db:
        while True:
            candidate = "".join(random.choices("0123456789", k=CARD_LENGTH))
            # yetakchi 0 bo'lsa ham muammo emas, chunki karta - matn (TEXT)
            if not await _card_exists(db, candidate):
                return candidate


# ============================================================
# USERS
# ============================================================

async def get_or_create_user(telegram_id: int, username: str, full_name: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        if row:
            await db.execute(
                "UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?",
                (username, full_name, telegram_id),
            )
            await db.commit()
            cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = await cur.fetchone()
            return dict(row)

    # Yangi foydalanuvchi - karta raqami generatsiya qilinadi (DB tashqarisida, deadlock bo'lmasligi uchun)
    card_number = await generate_unique_card_number()

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                """INSERT INTO users
                   (telegram_id, username, full_name, balance, card_number, language, notifications, created_at)
                   VALUES (?, ?, ?, 0, ?, 'uz', 1, ?)""",
                (telegram_id, username, full_name, card_number, _now()),
            )
            await db.commit()
        except aiosqlite.IntegrityError:
            # juda kam ehtimol bilan poyga holati - qayta urinamiz
            return await get_or_create_user(telegram_id, username, full_name)

        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row)


async def get_user(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_user_by_card(card_number: str):
    card_number = card_number.strip()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE card_number = ?", (card_number,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def update_balance(telegram_id: int, delta: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?", (delta, telegram_id)
        )
        await db.commit()


async def set_notifications(telegram_id: int, enabled: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET notifications = ? WHERE telegram_id = ?",
            (1 if enabled else 0, telegram_id),
        )
        await db.commit()


async def get_all_users():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users ORDER BY id DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ============================================================
# TRANSACTIONS
# ============================================================

async def log_transaction(tx_type: str, amount: int, sender_id=None, receiver_id=None, description=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO transactions (type, amount, sender_id, receiver_id, description, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (tx_type, amount, sender_id, receiver_id, description, _now()),
        )
        await db.commit()


async def get_last_transactions(telegram_id: int, limit: int = HISTORY_LIMIT):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """SELECT * FROM transactions WHERE sender_id = ? OR receiver_id = ?
               ORDER BY id DESC LIMIT ?""",
            (telegram_id, telegram_id, limit),
        )
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


# ============================================================
# TRANSFER (karta raqami orqali)
# ============================================================

async def transfer_um(sender_telegram_id: int, receiver_card: str, amount: int):
    if amount <= 0:
        return False, "Miqdor musbat bo'lishi kerak."

    sender = await get_user(sender_telegram_id)
    if not sender:
        return False, "Xatolik: yuboruvchi topilmadi."

    receiver = await get_user_by_card(receiver_card)
    if not receiver:
        return False, "Bunday karta raqami topilmadi."

    if receiver["telegram_id"] == sender_telegram_id:
        return False, "O'zingizga o'tkazma qila olmaysiz."

    if sender["balance"] < amount:
        return False, "Balansingizda yetarli UM yo'q."

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET balance = balance - ? WHERE telegram_id = ?",
            (amount, sender_telegram_id),
        )
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE telegram_id = ?",
            (amount, receiver["telegram_id"]),
        )
        await db.commit()

    await log_transaction("transfer", amount, sender_telegram_id, receiver["telegram_id"],
                           f"Karta: {receiver_card}")
    return True, receiver


# ============================================================
# PRODUCTS (do'kon)
# ============================================================

async def add_product(name: str, price: int, description: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO products (name, description, price, active, created_at) VALUES (?, ?, ?, 1, ?)",
            (name, description, price, _now()),
        )
        await db.commit()


async def edit_product(product_id: int, name: str, price: int, description: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM products WHERE id = ?", (product_id,))
        if not await cur.fetchone():
            return False
        await db.execute(
            "UPDATE products SET name = ?, price = ?, description = ? WHERE id = ?",
            (name, price, description, product_id),
        )
        await db.commit()
        return True


async def delete_product(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM products WHERE id = ?", (product_id,))
        if not await cur.fetchone():
            return False
        await db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        await db.commit()
        return True


async def toggle_product(product_id: int, active: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM products WHERE id = ?", (product_id,))
        if not await cur.fetchone():
            return False
        await db.execute(
            "UPDATE products SET active = ? WHERE id = ?", (1 if active else 0, product_id)
        )
        await db.commit()
        return True


async def set_product_price(product_id: int, price: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT 1 FROM products WHERE id = ?", (product_id,))
        if not await cur.fetchone():
            return False
        await db.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
        await db.commit()
        return True


async def get_active_products():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products WHERE active = 1 ORDER BY id DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_all_products():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products ORDER BY id DESC")
        rows = await cur.fetchall()
        return [dict(r) for r in rows]


async def get_product(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def buy_product(telegram_id: int, product_id: int):
    product = await get_product(product_id)
    if not product or not product["active"]:
        return False, "Mahsulot mavjud emas."

    user = await get_user(telegram_id)
    if not user:
        return False, "Foydalanuvchi topilmadi."

    if user["balance"] < product["price"]:
        return False, "Balansingizda yetarli UM yo'q."

    await update_balance(telegram_id, -product["price"])
    await log_transaction("purchase", product["price"], telegram_id, None, product["name"])
    return True, product


# ============================================================
# TOPUP REQUESTS (UM sotib olish)
# ============================================================

async def create_topup_request(telegram_id: int, amount: int, photo_file_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """INSERT INTO topup_requests (telegram_id, amount, photo_file_id, status, created_at)
               VALUES (?, ?, ?, 'pending', ?)""",
            (telegram_id, amount, photo_file_id, _now()),
        )
        await db.commit()
        return cur.lastrowid


async def get_topup_request(request_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM topup_requests WHERE id = ?", (request_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_topup_status(request_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE topup_requests SET status = ? WHERE id = ?", (status, request_id))
        await db.commit()


# ============================================================
# ADMIN BALANS BOSHQARUVI
# ============================================================

async def admin_add_balance(telegram_id: int, amount: int):
    user = await get_user(telegram_id)
    if not user:
        return False, "Foydalanuvchi topilmadi."
    await update_balance(telegram_id, amount)
    await log_transaction("admin_add", amount, None, telegram_id, "Admin tomonidan qo'shildi")
    return True, "OK"


async def admin_remove_balance(telegram_id: int, amount: int):
    user = await get_user(telegram_id)
    if not user:
        return False, "Foydalanuvchi topilmadi."
    if user["balance"] < amount:
        return False, "Foydalanuvchi balansi yetarli emas."
    await update_balance(telegram_id, -amount)
    await log_transaction("admin_remove", amount, telegram_id, None, "Admin tomonidan yechildi")
    return True, "OK"


# ============================================================
# STATISTIKA
# ============================================================

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM users")
        users_count = (await cur.fetchone())[0]

        cur = await db.execute("SELECT COALESCE(SUM(balance), 0) FROM users")
        total_balance = (await cur.fetchone())[0]

        cur = await db.execute("SELECT COUNT(*) FROM transactions")
        tx_count = (await cur.fetchone())[0]

        cur = await db.execute("SELECT COUNT(*) FROM products WHERE active = 1")
        active_products = (await cur.fetchone())[0]

        cur = await db.execute("SELECT COUNT(*) FROM topup_requests WHERE status = 'pending'")
        pending_topups = (await cur.fetchone())[0]

        return {
            "users_count": users_count,
            "total_balance": total_balance,
            "tx_count": tx_count,
            "active_products": active_products,
            "pending_topups": pending_topups,
        }
        
