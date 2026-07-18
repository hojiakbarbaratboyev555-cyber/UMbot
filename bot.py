import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

import database as db
from config import (
    BOT_TOKEN,
    WEBHOOK_PATH,
    WEBHOOK_URL,
    WEBAPP_HOST,
    WEBAPP_PORT,
)
import start, shop, account, earn, support, admin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())

    # Admin router birinchi bo'lishi kerak, chunki u faqat ADMIN_ID uchun filtrlangan
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(shop.router)
    dp.include_router(account.router)
    dp.include_router(earn.router)
    dp.include_router(support.router)

    return dp


async def on_startup(bot: Bot):
    await db.init_db()
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook o'rnatildi: {WEBHOOK_URL}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    if db.pool:
        await db.pool.close()


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN environment o'zgaruvchisi topilmadi (.env faylini tekshiring)")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    if WEBHOOK_URL:
        # --- Render (production): webhook rejimi ---
        app = web.Application()

        async def health_check(request):
            return web.Response(text="OK")

        app.router.add_get("/", health_check)

        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)
    else:
        # --- Lokal test: polling rejimi ---
        async def _run_polling():
            await on_startup(bot)
            try:
                await dp.start_polling(bot)
            finally:
                await on_shutdown(bot)

        asyncio.run(_run_polling())


if __name__ == "__main__":
    main()