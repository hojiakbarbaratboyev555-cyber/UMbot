import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Render "Web Service" avtomatik RENDER_EXTERNAL_URL beradi.
# Agar boshqa hostingda bo'lsangiz, WEBHOOK_URL ni qo'lda kiriting.
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = "/webhook"
PORT = int(os.getenv("PORT", "8080"))

DB_PATH = os.getenv("DB_PATH", "um_bot.db")

CARD_PREFIX = ""  # kerak bo'lsa karta raqami oldiga prefiks qo'shish mumkin
CARD_LENGTH = 6

HISTORY_LIMIT = 20
