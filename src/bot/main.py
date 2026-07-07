import logging

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from bot.config import Settings
from bot.handlers import business, connection

ALLOWED_UPDATES = ["business_connection", "business_message", "edited_business_message"]


def main() -> None:
    config = Settings()
    logging.basicConfig(
        level=config.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    bot = Bot(token=config.bot_token)
    dp = Dispatcher()
    dp.include_routers(connection.router, business.router)

    async def on_startup(bot: Bot) -> None:
        # business updates are not delivered unless explicitly allowed
        await bot.set_webhook(
            url=config.webhook_url,
            secret_token=config.webhook_secret,
            allowed_updates=ALLOWED_UPDATES,
        )
        logging.getLogger(__name__).info("webhook set: %s", config.webhook_url)

    dp.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=config.webhook_secret
    ).register(app, path=config.webhook_path)
    setup_application(app, dp, bot=bot)
    web.run_app(app, host=config.host, port=config.port)


if __name__ == "__main__":
    main()
