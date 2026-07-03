from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ---------- Asosiy pastki menyu ----------
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🏠 Asosiy"), KeyboardButton(text="🛒 Do'kon")],
        [KeyboardButton(text="💸 O'tkazma"), KeyboardButton(text="⚙️ Sozlamalar")],
    ],
    resize_keyboard=True,
)

cancel_menu = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
    resize_keyboard=True,
)


def profile_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ UM sotib olish", callback_data="topup_start")],
            [InlineKeyboardButton(text="📜 Tarix", callback_data="history")],
        ]
    )


def shop_inline(products):
    buttons = [
        [InlineKeyboardButton(text=f"{p['name']} — {p['price']} UM", callback_data=f"buy_{p['id']}")]
        for p in products
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_buy_inline(product_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Sotib olish", callback_data=f"confirmbuy_{product_id}"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action"),
        ]]
    )


def admin_topup_inline(request_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"topupok_{request_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"topupno_{request_id}"),
        ]]
    )


def confirm_transfer_inline():
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="transfer_confirm"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_action"),
        ]]
    )


def settings_inline(notifications_enabled: bool):
    label = "🔕 Bildirishnomani o'chirish" if notifications_enabled else "🔔 Bildirishnomani yoqish"
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data="toggle_notifications")]]
)
      
