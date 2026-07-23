import asyncpg
import random
from config import DATABASE_URL, ADMIN_ID, ADMIN_ACCOUNT_NUMBER

pool: asyncpg.Pool | None = None


async def init_db():
    """Bazaga ulanish pool'ini yaratadi va jadvallarni tayyorlaydi."""
    global pool
    try:
        pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10)
    except Exception:
        # Ba'zi Render PostgreSQL instance'lari SSL talab qiladi
        pool = await asyncpg.create_pool(dsn=DATABASE_URL, min_size=1, max_size=10, ssl="require")

    async with pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                account_number CHAR(3) UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                username TEXT,
                balance NUMERIC(14, 2) NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                price NUMERIC(14, 2) NOT NULL,
                photo_file_id TEXT,
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                price NUMERIC(14, 2) NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending / approved / rejected
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS topups (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                amount NUMERIC(14, 2) NOT NULL,
                screenshot_file_id TEXT,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending / approved / rejected
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS withdrawals (
                id SERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                amount NUMERIC(14, 2) NOT NULL,
                card_number TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending / approved / rejected
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS inventory (
                user_id BIGINT NOT NULL REFERENCES users(user_id),
                item_key TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (user_id, item_key)
            );

            CREATE TABLE IF NOT EXISTS transfers (
                id SERIAL PRIMARY KEY,
                from_user_id BIGINT NOT NULL REFERENCES users(user_id),
                to_user_id BIGINT NOT NULL REFERENCES users(user_id),
                amount NUMERIC(14, 2) NOT NULL,
                commission NUMERIC(14, 2) NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """
        )

        # Eski bazalarda 'name' ustida unique cheklov bo'lmasligi mumkin — xavfsiz qo'shamiz
        try:
            await conn.execute(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'products_name_key'
                    ) THEN
                        ALTER TABLE products ADD CONSTRAINT products_name_key UNIQUE (name);
                    END IF;
                END $$;
                """
            )
        except Exception:
            pass  # Agar takrorlanuvchi nomlar bo'lsa, qo'lda tozalash kerak bo'ladi

        # Admin uchun maxsus 007 hisobini kafolatlash
        admin_exists = await conn.fetchval(
            "SELECT 1 FROM users WHERE user_id = $1", ADMIN_ID
        )
        if not admin_exists:
            # Agar 007 band bo'lsa (ehtimoli deyarli yo'q), baribir admin uchun ajratamiz
            await conn.execute(
                """
                INSERT INTO users (user_id, account_number, full_name, username, balance)
                VALUES ($1, $2, $3, $4, 0)
                ON CONFLICT (user_id) DO NOTHING
                """,
                ADMIN_ID, ADMIN_ACCOUNT_NUMBER, "Admin", "admin",
            )

    await sync_products_from_code()


async def sync_products_from_code():
    """products.py faylidagi PRODUCTS ro'yxatini bazaga sinxronlaydi.

    Ro'yxatdagi mahsulotlar qo'shiladi/yangilanadi (nomi bo'yicha).
    Ro'yxatda yo'q, lekin bazada mavjud mahsulotlar o'chirilmaydi — faqat
    'active=FALSE' qilinadi (chunki eski buyurtmalar shu mahsulotga bog'liq bo'lishi mumkin).
    """
    from products import PRODUCTS

    async with pool.acquire() as conn:
        current_names = [p["name"] for p in PRODUCTS]

        for p in PRODUCTS:
            await conn.execute(
                """
                INSERT INTO products (name, description, price, photo_file_id, active)
                VALUES ($1, $2, $3, $4, TRUE)
                ON CONFLICT (name) DO UPDATE SET
                    description = EXCLUDED.description,
                    price = EXCLUDED.price,
                    photo_file_id = EXCLUDED.photo_file_id,
                    active = TRUE
                """,
                p["name"], p.get("description"), p["price"], p.get("photo_file_id"),
            )

        if current_names:
            await conn.execute(
                "UPDATE products SET active = FALSE WHERE name != ALL($1::text[])",
                current_names,
            )
        else:
            await conn.execute("UPDATE products SET active = FALSE")


async def generate_unique_account_number(conn) -> str:
    """000-999 oralig'ida betakror 3 xonali hisob raqam generatsiya qiladi."""
    while True:
        number = f"{random.randint(0, 999):03d}"
        exists = await conn.fetchval(
            "SELECT 1 FROM users WHERE account_number = $1", number
        )
        if not exists:
            return number


async def get_or_create_user(user_id: int, full_name: str, username: str | None):
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE user_id = $1", user_id
        )
        if user:
            return user

        account_number = await generate_unique_account_number(conn)
        user = await conn.fetchrow(
            """
            INSERT INTO users (user_id, account_number, full_name, username, balance)
            VALUES ($1, $2, $3, $4, 0)
            RETURNING *
            """,
            user_id, account_number, full_name, username,
        )
        return user


async def get_user(user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)


async def get_user_by_account(account_number: str):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM users WHERE account_number = $1", account_number
        )


async def update_balance(user_id: int, delta):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET balance = balance + $1 WHERE user_id = $2",
            delta, user_id,
        )


async def get_active_products():
    async with pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM products WHERE active = TRUE ORDER BY id"
        )


async def get_product(product_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM products WHERE id = $1", product_id)


async def create_order(user_id: int, product_id: int, price):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO orders (user_id, product_id, price, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING *
            """,
            user_id, product_id, price,
        )


async def update_order_status(order_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE orders SET status = $1 WHERE id = $2", status, order_id
        )


async def get_order(order_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM orders WHERE id = $1", order_id)


async def create_topup(user_id: int, amount, screenshot_file_id: str):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO topups (user_id, amount, screenshot_file_id, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING *
            """,
            user_id, amount, screenshot_file_id,
        )


async def update_topup_status(topup_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE topups SET status = $1 WHERE id = $2", status, topup_id
        )


async def get_topup(topup_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM topups WHERE id = $1", topup_id)


async def create_transfer(from_user_id: int, to_user_id: int, amount, commission):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO transfers (from_user_id, to_user_id, amount, commission)
            VALUES ($1, $2, $3, $4)
            RETURNING *
            """,
            from_user_id, to_user_id, amount, commission,
        )


async def create_withdrawal(user_id: int, amount, card_number: str):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO withdrawals (user_id, amount, card_number, status)
            VALUES ($1, $2, $3, 'pending')
            RETURNING *
            """,
            user_id, amount, card_number,
        )


async def update_withdrawal_status(withdrawal_id: int, status: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE withdrawals SET status = $1 WHERE id = $2", status, withdrawal_id
        )


async def get_withdrawal(withdrawal_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM withdrawals WHERE id = $1", withdrawal_id)


async def add_item_to_inventory(user_id: int, item_key: str, qty: int = 1):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO inventory (user_id, item_key, quantity)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id, item_key) DO UPDATE SET quantity = inventory.quantity + $3
            """,
            user_id, item_key, qty,
        )


async def remove_item_from_inventory(user_id: int, item_key: str, qty: int = 1) -> bool:
    """Buyumni inventardan ayiradi. Yetarli bo'lmasa False qaytaradi."""
    async with pool.acquire() as conn:
        current = await conn.fetchval(
            "SELECT quantity FROM inventory WHERE user_id = $1 AND item_key = $2",
            user_id, item_key,
        )
        if not current or current < qty:
            return False
        await conn.execute(
            "UPDATE inventory SET quantity = quantity - $3 WHERE user_id = $1 AND item_key = $2",
            user_id, item_key, qty,
        )
        return True


async def get_user_inventory(user_id: int) -> dict:
    """{item_key: quantity} ko'rinishida, faqat quantity > 0 bo'lganlarni qaytaradi."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT item_key, quantity FROM inventory WHERE user_id = $1 AND quantity > 0",
            user_id,
        )
        return {r["item_key"]: r["quantity"] for r in rows}