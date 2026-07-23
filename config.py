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

# --- Hisob to'ldirish ---
TOPUP_TEXT = "Hisobingizni to'ldirish boʻlimiga xush kelibsiz\n\n<blockquote>1000💵 = 1【𝗛𝗕】\n1💎 = 1.5【𝗛𝗕】</blockquote>\n<blockquote>Pastdagi Guruh tugmasi orqali oʻtib @chiyx profiliga toʻlovni amalga oshirib 【𝗛𝗕】uchun deb yozing adminlar hisobingizga pullarni yuborishadi.</blockquote>\n\n Qandaydur muammolar boʻlsa shu guruhda ham hal qilishingiz mumkin"
TOPUP_URL = "https://t.me/+BCK5dEstaGYzNDk1"

# --- Valyuta sozlamalari ---
# HB hech qanday so'm/pul qiymatiga ega emas - sof ichki ball.
# Faqat admin tomonidan /grant buyrug'i orqali beriladi.
CURRENCY_NAME = "【𝗛𝗕】"

MIN_TRANSFER_AMOUNT = 0.01
TRANSFER_COMMISSION_PERCENT = 10  # %

# --- Start stiker (file_id) ---
WELCOME_STICKER_ID = os.getenv("WELCOME_STICKER_ID", "")