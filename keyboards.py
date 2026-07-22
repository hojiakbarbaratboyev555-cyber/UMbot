from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import SUPPORT_URL, CURRENCY_NAME


# --- Asosiy menyu (3 tugma) ---
def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Do'kon"), KeyboardButton(text="👤 𝗛𝗶𝘀𝗼𝗯𝗶𝗺")],
            [KeyboardButton(text="☎️ 𝗤𝗼ʼ𝗹𝗹𝗮𝗯-𝗾𝘂𝘃𝘃𝗮𝘁𝗹𝗮𝘀𝗵")],
        ],
        resize_keyboard=True,
    )


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ 𝗢𝗿𝗾𝗮𝗴𝗮")]],
        resize_keyboard=True,
    )


# --- Do'kon: mahsulot ostidagi inline tugma ---
def product_buy_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Sotib olish", callback_data=f"buy:{product_id}")]
        ]
    )


# --- Do'kon: buyum (item) ostidagi inline tugma ---
def item_buy_kb(item_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Sotib olish", callback_data=f"buy_item:{item_key}")]
        ]
    )


# --- Admin uchun buyurtma tasdiqlash tugmalari ---
def admin_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅", callback_data=f"order_approve:{order_id}"),
                InlineKeyboardButton(text="❌", callback_data=f"order_reject:{order_id}"),
            ],
            [InlineKeyboardButton(text="✉️ Xabar yuborish", callback_data=f"order_msg:{order_id}")],
        ]
    )


# --- Hisobim bo'limi (faqat O'tkazish) ---
def account_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔁 O'tkazish", callback_data="transfer_start")],
        ]
    )


# --- O'tkazma tasdiqlash ---
def transfer_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="transfer_confirm"),
                InlineKeyboardButton(text="◀️ 𝗢𝗿𝗾𝗮𝗴𝗮", callback_data="transfer_cancel"),
            ]
        ]
    )


# --- Qo'llab-quvvatlash ---
def support_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔗 Admin bilan bog'lanish", url=SUPPORT_URL)]]
    )
