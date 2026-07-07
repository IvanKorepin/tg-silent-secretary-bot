import logging

from aiogram import Bot, Router
from aiogram.types import Message

logger = logging.getLogger(__name__)
router = Router()


@router.business_message()
async def handle_business_message(message: Message, bot: Bot) -> None:
    try:
        await bot.read_business_message(
            business_connection_id=message.business_connection_id,
            chat_id=message.chat.id,
            message_id=message.message_id,
        )
        logger.info(
            "✓ read | conn=%s chat=%s msg=%s",
            message.business_connection_id,
            message.chat.id,
            message.message_id,
        )
    except Exception:
        # NF-03: log and keep going, never crash the update loop.
        # CancelledError is BaseException on py3.8+, so shutdown passes through.
        logger.exception(
            "read failed | conn=%s chat=%s msg=%s",
            message.business_connection_id,
            message.chat.id,
            message.message_id,
        )


@router.edited_business_message()
async def handle_edited_business_message(message: Message) -> None:
    # accept the update so Telegram stops retrying; no action needed
    pass
