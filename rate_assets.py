"""
6 ta buyumning real vaqtdagi narxini oladi (Bitcoin, Oltin, Tesla, Google, TON, SpaceX)
va items.py'dagi formulaga (op/factor) qarab HB'ga aylantiradi.

Natijalar qisqa vaqt (2 daqiqa) keshlanadi - API'ga ortiqcha murojaat bo'lmasligi uchun.
Agar API ishlamay qolsa, items.py'dagi fallback_usd qiymati ishlatiladi.
"""

import time
import logging
import aiohttp

logger = logging.getLogger(__name__)

_cache = {}  # item_key -> (usd_price, timestamp)
CACHE_TTL_SECONDS = 120


async def _fetch_coingecko(coin_id: str) -> float:
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": coin_id, "vs_currencies": "usd"},
        ) as resp:
            data = await resp.json()
            return float(data[coin_id]["usd"])


async def _fetch_yahoo(ticker: str) -> float:
    timeout = aiohttp.ClientTimeout(total=8)
    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        ) as resp:
            data = await resp.json()
            return float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])


async def get_asset_price_usd(item: dict) -> float:
    """Aktivning joriy narxini USD'da qaytaradi (keshlangan yoki yangi)."""
    key = item["key"]
    now = time.time()

    if key in _cache and (now - _cache[key][1]) < CACHE_TTL_SECONDS:
        return _cache[key][0]

    try:
        if item["source"] == "coingecko":
            price = await _fetch_coingecko(item["id"])
        else:
            price = await _fetch_yahoo(item["id"])
        _cache[key] = (price, now)
        return price
    except Exception as e:
        logger.warning(f"{key} narxini olishda xato, fallback ishlatilmoqda: {e}")
        return _cache[key][0] if key in _cache else item["fallback_usd"]


async def get_item_hb_price(item: dict) -> float:
    """Aktivning joriy narxini HB'ga aylantirib qaytaradi (op/factor bo'yicha)."""
    usd_price = await get_asset_price_usd(item)
    if item["op"] == "div":
        return round(usd_price / item["factor"], 4)
    else:
        return round(usd_price * item["factor"], 4)