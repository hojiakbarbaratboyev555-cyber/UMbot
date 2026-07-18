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
                name TEXT NOT NULL,
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