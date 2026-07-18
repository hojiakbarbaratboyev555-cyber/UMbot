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
            [KeyboardButton(text="🛍 Do'kon"), KeyboardButton(text="👤 Hisobim")],
            [KeyboardButton(text="☎️ Qo'llab-quvvatlash")],
        ],
        resize_keyboard=True,
    )


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Ortga qaytish")]],
        resize_keyboard=True,
    )


# --- Do'kon: mahsulot ostidagi inline tugma ---
def product_buy_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Sotib olish", callback_data=f"buy:{product_id}")]
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


# --- Hisobim bo'limi ---
def account_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💳 Pul kiritish", callback_data="topup_start"),
                InlineKeyboardButton(text="💸 Pul chiqarish", callback_data="withdraw_start"),
            ],
            [InlineKeyboardButton(text="🔁 O'tkazish", callback_data="transfer_start")],
        ]
    )


# --- O'tkazma tasdiqlash ---
def transfer_confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="transfer_confirm"),
                InlineKeyboardButton(text="◀️ Ortga", callback_data="transfer_cancel"),
            ]
        ]
    )


# --- Admin uchun to'lov (topup) tasdiqlash ---
def admin_topup_kb(topup_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅", callback_data=f"topup_approve:{topup_id}"),
                InlineKeyboardButton(text="❌", callback_data=f"topup_reject:{topup_id}"),
            ]
        ]
    )


# --- Admin uchun pul chiqarish tasdiqlash ---
def admin_withdraw_kb(withdrawal_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅", callback_data=f"withdraw_approve:{withdrawal_id}")]
        ]
    )


# --- Qo'llab-quvvatlash ---
def support_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔗 Admin bilan bog'lanish", url=SUPPORT_URL)]]
    )