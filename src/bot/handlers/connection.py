import logging

from aiogram import Router
from aiogram.types import BusinessConnection

logger = logging.getLogger(__name__)
router = Router()


@router.business_connection()
async def handle_business_connection(connection: BusinessConnection) -> None:
    logger.info(
        "business connection %s | conn=%s user=%s",
        "enabled" if connection.is_enabled else "disabled",
        connection.id,
        connection.user.id,
    )
