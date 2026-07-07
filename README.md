# tg-silent-secretary-bot

Telegram-бот в режиме Business Secretary: автоматически отмечает входящие сообщения как прочитанные в разрешённых чатах. Работает тихо — не пишет в чаты, не хранит данные на диске.

## Требования

- Telegram Premium (для режима Telegram Business)
- Публичный хост с TLS (reverse proxy → порт 8080)

## Настройка

1. **Создать бота:** [@BotFather](https://t.me/BotFather) → `/newbot` → сохранить токен.
2. **Включить Business Mode:** в BotFather — `/mybots` → выбрать бота → *Business Mode* → включить. Без этого business-апдейты не приходят.
3. **Конфигурация:** `cp .env.example .env`, заполнить `BOT_TOKEN`, `WEBHOOK_URL` (публичный HTTPS-адрес), `WEBHOOK_SECRET` (случайная строка, например `openssl rand -hex 32`).
4. **Reverse proxy:** проксировать `WEBHOOK_URL` на `localhost:8080` (TLS терминируется на прокси).
5. **Запуск:** `docker compose up -d --build`. Бот сам вызовет `setWebhook` при старте.
6. **Подключить секретаря:** Telegram → Настройки → Telegram Business → Чат-боты → указать бота → выбрать чаты, которые он будет обрабатывать.

Проверка: отправьте сообщение в разрешённый чат — счётчик непрочитанных обнулится, в логах (`docker compose logs -f`) появится `✓ read`.

## Разработка

```sh
uv sync
uv run pytest
```

Локальный запуск: `uv run python -m bot.main` (нужен `.env` и публичный URL, например через `ngrok`).

## Ограничения (MVP)

- Бот видит только новые сообщения (не историю) и только в чатах, разрешённых в TG Business UI.
- Ничего не хранится между перезапусками; пропущенные апдейты Telegram переотправит сам.
- Один инстанс — один пользователь.

Документация: `docs/BUSINESS_ANALYSIS.md`, `docs/SYSTEM_ANALYSIS.md`.
