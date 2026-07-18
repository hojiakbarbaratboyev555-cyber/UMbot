"""
⌁𝗛𝗕⌁ narxini TON'ning real bozor narxiga bog'lash.

1 ⌁𝗛𝗕⌁ = 1 TON (so'm ekvivalenti bo'yicha).
TON narxi CoinGecko'dan (USD), so'ngra USD/UZS kursi orqali so'mga o'giriladi.
Natija qisqa vaqt keshlanadi — ortiqcha API so'rovlarining oldini olish uchun.
"""

import time
import logging
import aiohttp

from config import HB_RATE_SUM as FALLBACK_RATE_SUM

logger = logging.getLogger(__name__)

_cache = {"rate": None, "ts": 0.0}
CACHE_TTL_SECONDS = 60

TON_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"
USD_UZS_URL = "https://open.er-api.com/v6/latest/USD"


async def get_hb_rate_sum() -> float:
    """1 ⌁𝗛𝗕⌁ ning joriy narxini so'mda qaytaradi (TON narxiga teng)."""
    now = time.time()

    if _cache["rate"] is not None and (now - _cache["ts"]) < CACHE_TTL_SECONDS:
        return _cache["rate"]

    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                TON_PRICE_URL,
                params={"ids": "the-open-network", "vs_currencies": "usd"},
            ) as resp:
                ton_data = await resp.json()
                ton_usd = float(ton_data["the-open-network"]["usd"])

            async with session.get(USD_UZS_URL) as resp:
                fx_data = await resp.json()
                usd_uzs = float(fx_data["rates"]["UZS"])

        rate = round(ton_usd * usd_uzs, 2)
        _cache["rate"] = rate
        _cache["ts"] = now
        return rate

    except Exception as e:
        logger.warning(f"TON kursini olishda xato, fallback ishlatilmoqda: {e}")
        # API ishlamay qolsa — oxirgi bilingan kursni, bo'lmasa standart qiymatni qaytaramiz
        return _cache["rate"] if _cache["rate"] is not None else FALLBACK_RATE_SUM