from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from bot.config import Settings
from bot.handlers.business import (
    handle_business_message,
    handle_edited_business_message,
)
from bot.handlers.connection import handle_business_connection


def make_message():
    return SimpleNamespace(
        business_connection_id="conn1",
        chat=SimpleNamespace(id=42),
        message_id=7,
    )


async def test_business_message_marked_as_read():
    bot = AsyncMock()
    await handle_business_message(make_message(), bot)
    bot.read_business_message.assert_awaited_once_with(
        business_connection_id="conn1", chat_id=42, message_id=7
    )


async def test_api_error_is_logged_not_raised(caplog):
    bot = AsyncMock()
    bot.read_business_message.side_effect = RuntimeError("boom")
    await handle_business_message(make_message(), bot)
    assert "read failed" in caplog.text


async def test_edited_message_is_noop():
    await handle_edited_business_message(make_message())


async def test_connection_is_logged(caplog):
    connection = SimpleNamespace(
        id="conn1", user=SimpleNamespace(id=99), is_enabled=True
    )
    with caplog.at_level("INFO"):
        await handle_business_connection(connection)
    assert "conn=conn1" in caplog.text


def test_config_fails_fast_without_required_vars(monkeypatch):
    for var in ("BOT_TOKEN", "WEBHOOK_URL", "WEBHOOK_SECRET"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_config_rejects_empty_and_weak_values(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "")
    monkeypatch.setenv("WEBHOOK_URL", "https://example.com/webhook")
    monkeypatch.setenv("WEBHOOK_SECRET", "short")
    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    errors = {e["loc"][0] for e in exc_info.value.errors()}
    assert errors == {"bot_token", "webhook_secret"}
