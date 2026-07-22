# Do'kondagi 6 ta buyum - real aktivlar narxiga bog'langan, real vaqtda o'zgaradi.
#
#   key      - ICHKI nom (unique, bazada shunday saqlanadi, o'zgartirmang)
#   emoji    - ko'rinadigan belgi
#   label    - ko'rinadigan nom
#   source   - narx manbai: "coingecko" (kripto) yoki "yahoo" (aksiya/metall)
#   id       - shu manbadagi aktiv identifikatori
#   op       - "div" (bo'lish) yoki "mul" (ko'paytirish)
#   factor   - necha marta bo'linadi/ko'paytiriladi
#   fallback_usd - API ishlamay qolsa ishlatiladigan taxminiy USD narx

ITEMS = [
    {"key": "bitcoin", "emoji": "🏆", "label": "BITCOIN", "source": "coingecko", "id": "bitcoin", "op": "div", "factor": 1000, "fallback_usd": 64500},
    {"key": "oltin",   "emoji": "🍇", "label": "OLTIN",   "source": "yahoo",     "id": "GC=F",     "op": "div", "factor": 100,  "fallback_usd": 4017},
    {"key": "tesla",   "emoji": "🍎", "label": "TESLA",   "source": "yahoo",     "id": "TSLA",     "op": "div", "factor": 10,   "fallback_usd": 380},
    {"key": "google",  "emoji": "🔪", "label": "GOOGLE",  "source": "yahoo",     "id": "GOOGL",    "op": "div", "factor": 10,   "fallback_usd": 346.77},
    {"key": "ton",     "emoji": "🥄", "label": "TON",     "source": "coingecko", "id": "the-open-network", "op": "mul", "factor": 10, "fallback_usd": 1.58},
    {"key": "spacex",  "emoji": "✏️", "label": "SPACEX",  "source": "yahoo",     "id": "SPCX",     "op": "div", "factor": 10,   "fallback_usd": 123.99},
]


def format_inventory_table(inventory: dict) -> str:
    """Foydalanuvchining aktivlarini 2 ustunli jadval ko'rinishida formatlaydi."""
    lines = ["$Aktivlar$\n"]
    for i in range(0, len(ITEMS), 2):
        left = ITEMS[i]
        left_qty = inventory.get(left["key"], 0)
        row = f"{left['emoji']} - {left_qty} ta"

        if i + 1 < len(ITEMS):
            right = ITEMS[i + 1]
            right_qty = inventory.get(right["key"], 0)
            row += f"       {right['emoji']} - {right_qty} ta"

        lines.append(row)

    return "\n".join(lines)