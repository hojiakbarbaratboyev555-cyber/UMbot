import os
from dotenv import load_dotenv

load_dotenv()

# --- Bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN")

# --- Webhook (Render) ---
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # masalan: https://sizning-app.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8000))  # Render avtomatik PORT beradi

# --- Database (Render PostgreSQL) ---
DATABASE_URL = os.getenv("DATABASE_URL")  # Render'dagi Internal/External Database URL

# --- Admin ---
ADMIN_ID = int(os.getenv("ADMIN_ID", "8223476380"))
ADMIN_ACCOUNT_NUMBER = "007"

# --- Havolalar ---
SUPPORT_URL = os.getenv("SUPPORT_URL", "https://t.me/your_admin_username")

# --- To'lov rekvizitlari (Pul kiritish bo'limi) ---
PAYMENT_CARD_NUMBER = os.getenv("PAYMENT_CARD_NUMBER", "0000 0000 0000 0000")
PAYMENT_CARD_OWNER = os.getenv("PAYMENT_CARD_OWNER", "M.N")

# --- Valyuta sozlamalari ---
CURRENCY_NAME = "⌁𝗛𝗕⌁"
HB_RATE_SUM = 30_000  # 1 ⌁𝗛𝗕⌁ = 30 000 so'm (qat'iy kurs)

MIN_TRANSFER_AMOUNT = 0.05
TRANSFER_COMMISSION_PERCENT = 10  # %

MIN_TOPUP_AMOUNT = 0.1
MIN_WITHDRAW_AMOUNT = 0.5
WITHDRAW_COMMISSION_PERCENT = 10  # %

# --- Start stiker (file_id) ---
WELCOME_STICKER_ID = os.getenv("WELCOME_STICKER_ID", "")