from datetime import datetime


def format_money(amount: int) -> str:
    """1000000 -> 1 000 000"""
    return f"{amount:,}".replace(",", " ")


def format_date(iso_string: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_string)
        return dt.strftime("%d.%m.%Y %H:%M")
    except (ValueError, TypeError):
        return iso_string or "—"


def parse_positive_int(text: str):
    """Matnni musbat butun songa aylantiradi, xato bo'lsa None qaytaradi."""
    text = text.strip().replace(" ", "")
    if not text.isdigit():
        return None
    value = int(text)
    if value <= 0:
        return None
    return value


def is_valid_card(text: str) -> bool:
    text = text.strip()
    return text.isdigit() and len(text) == 6


def split_semicolon_args(raw: str, expected_parts: int):
    """'nomi; narxi; tavsifi' kabi argumentlarni ajratadi."""
    parts = [p.strip() for p in raw.split(";")]
    if len(parts) < expected_parts:
        return None
    return parts


def transaction_line(tx: dict, viewer_telegram_id: int) -> str:
    """Bitta tranzaksiyani odam o'qiy oladigan qatorga aylantiradi."""
    amount = format_money(tx["amount"])
    date = format_date(tx["created_at"])
    t = tx["type"]

    if t == "transfer":
        if tx["sender_id"] == viewer_telegram_id:
            return f"➖ {amount} UM — o'tkazma yuborildi ({date})"
        return f"➕ {amount} UM — o'tkazma qabul qilindi ({date})"
    if t == "purchase":
        return f"🛒 -{amount} UM — {tx['description']} ({date})"
    if t == "topup":
        return f"➕ {amount} UM — hisob to'ldirildi ({date})"
    if t == "admin_add":
        return f"➕ {amount} UM — admin qo'shdi ({date})"
    if t == "admin_remove":
        return f"➖ {amount} UM — admin yechdi ({date})"
    return f"{amount} UM — {t} ({date})"
      
