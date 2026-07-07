# System Analysis — Telegram Silent Secretary Bot

**Версия:** 0.1  
**Дата:** 2026-07-06

---

## 1. Обзор системы

Бот работает как **Telegram Business Secretary** — подключается к аккаунту пользователя через Bot API и автоматически отмечает входящие сообщения как прочитанные во всех разрешённых чатах.

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Platform                      │
│                                                           │
│  User Account ──(Business Secretary)──► Bot              │
│       │                                  │               │
│  Allowed Chats                    business_message        │
│       │                            updates via           │
│  (channels, groups,               webhook POST           │
│   direct messages)                       │               │
└──────────────────────────────────────────│───────────────┘
                                           │
                                    HTTPS POST
                                           │
                          ┌────────────────▼──────────────┐
                          │        Bot Server              │
                          │                                │
                          │  Nginx/Caddy (TLS termination) │
                          │         │                      │
                          │  aiogram Webhook Handler       │
                          │         │                      │
                          │  BusinessMessageHandler        │
                          │         │                      │
                          │  readBusinessMessage() ────────┼──► Telegram API
                          │                                │
                          └────────────────────────────────┘
```

---

## 2. Компоненты

### 2.1 Webhook-сервер
- **Реализация:** встроенный `aiohttp` веб-сервер aiogram (`SimpleRequestHandler`)
- **Задача:** принимать POST-запросы от Telegram, проверять секрет, передавать апдейт в Dispatcher
- **Порт:** конфигурируемый (default: 8080)
- **TLS:** терминируется на уровне reverse proxy (Nginx / Caddy), до бота трафик идёт по HTTP

### 2.2 Dispatcher (aiogram)
- Центральный роутер апдейтов
- Регистрирует хэндлеры по типу апдейта
- Обрабатывает `business_connection`, `business_message`, `edited_business_message`

### 2.3 BusinessConnectionHandler
- Срабатывает при подключении/отключении пользователя через TG Business UI
- Логирует факт подключения (`business_connection_id`, `user_id`, `is_enabled`)
- В Фазе 2: хранит connection_id → user_id mapping

### 2.4 BusinessMessageHandler
- Срабатывает на каждый `business_message` апдейт
- Вызывает `bot.read_business_message(business_connection_id, chat_id, message_id)`
- Логирует результат

### 2.5 Config
- Загружается из переменных окружения через `pydantic-settings`
- Валидируется при старте; при отсутствии обязательных переменных — падает с ошибкой

---

## 3. Data Flow

### 3.1 Подключение пользователя

```
User → TG Settings → Assigns bot as Business Secretary
  └─► Telegram sends business_connection update to webhook
        └─► BusinessConnectionHandler logs: connected, user_id, connection_id
```

### 3.2 Входящее сообщение (основной сценарий)

```
Someone sends message to User in allowed chat
  └─► Telegram sends business_message update to webhook
        ├─► BusinessMessageHandler receives update
        ├─► Extracts: business_connection_id, chat.id, message.message_id
        ├─► Calls: bot.read_business_message(
        │       business_connection_id=...,
        │       chat_id=...,
        │       message_id=...
        │   )
        └─► Logs: "✓ read | conn={id} chat={id} msg={id}"
```

### 3.3 Edited message

```
Someone edits message in allowed chat
  └─► Telegram sends edited_business_message update
        └─► Тот же хэндлер — повторный вызов readBusinessMessage не нужен,
            но апдейт нужно принять (иначе Telegram будет ретраить)
```

---

## 4. Структура проекта

```
tg-silent-secretary-bot/
│
├── src/
│   └── bot/
│       ├── __init__.py
│       ├── main.py               # точка входа: запуск webhook-сервера
│       ├── config.py             # pydantic-settings конфиг
│       ├── handlers/
│       │   ├── __init__.py
│       │   ├── business.py       # business_message + edited_business_message
│       │   └── connection.py     # business_connection
│       └── middlewares/          # зарезервировано (Фаза 2: rate limit, логирование)
│           └── __init__.py
│
├── tests/
│   └── test_handlers.py          # юнит-тесты хэндлеров
│
├── .env.example                  # шаблон переменных окружения
├── pyproject.toml                # зависимости + метаданные (uv / pip)
├── Dockerfile
├── docker-compose.yml
├── BUSINESS_ANALYSIS.md
└── SYSTEM_ANALYSIS.md
```

---

## 5. Конфигурация

Все параметры передаются через переменные окружения. Значения с `*` — обязательные.

| Переменная | Тип | Default | Описание |
|---|---|---|---|
| `BOT_TOKEN` * | str | — | Токен бота от @BotFather |
| `WEBHOOK_URL` * | str | — | Публичный URL вебхука (e.g. `https://myhost.com/bot`) |
| `WEBHOOK_SECRET` * | str | — | Секрет для верификации запросов от Telegram |
| `WEBHOOK_PATH` | str | `/webhook` | Путь на котором принимаются апдейты |
| `HOST` | str | `0.0.0.0` | Адрес для aiohttp сервера |
| `PORT` | int | `8080` | Порт для aiohttp сервера |
| `LOG_LEVEL` | str | `INFO` | Уровень логирования |

### .env.example
```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET=your-random-secret-here
WEBHOOK_PATH=/webhook
HOST=0.0.0.0
PORT=8080
LOG_LEVEL=INFO
```

---

## 6. Зависимости

```toml
[project]
name = "tg-silent-secretary-bot"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "aiogram>=3.7,<4.0",       # Telegram Bot API framework
    "pydantic-settings>=2.0",  # конфиг из env
    "aiohttp>=3.9",            # webhook сервер (входит в aiogram)
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "aiogram[dev]>=3.7",       # тестовые утилиты aiogram
]
```

---

## 7. Ключевые паттерны aiogram

### Регистрация Business-хэндлеров

```python
from aiogram import Router
from aiogram.types import BusinessMessage, BusinessConnection

router = Router()

@router.business_message()
async def handle_business_message(message: BusinessMessage, bot: Bot):
    await bot.read_business_message(
        business_connection_id=message.business_connection_id,
        chat_id=message.chat.id,
        message_id=message.message_id,
    )

@router.edited_business_message()
async def handle_edited_business_message(message: BusinessMessage):
    pass  # принимаем апдейт, действий не требуется
```

### Запуск webhook

```python
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot, secret_token=config.webhook_secret).register(
    app, path=config.webhook_path
)
setup_application(app, dp, bot=bot)
web.run_app(app, host=config.host, port=config.port)
```

---

## 8. Деплой

```
Internet
   │
   ▼ :443 (HTTPS)
Nginx / Caddy
   │  TLS termination
   │  proxy_pass → localhost:8080
   ▼ :8080 (HTTP)
aiohttp (aiogram webhook server)
   │
   └── Docker container
```

### Минимальный docker-compose.yml

```yaml
services:
  bot:
    build: .
    restart: unless-stopped
    env_file: .env
    ports:
      - "8080:8080"
```

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY src/ ./src/
CMD ["python", "-m", "bot.main"]
```

---

## 9. Ограничения и допущения

- Бот не хранит никаких данных между перезапусками (in-memory, MVP).
- При рестарте бота уже доставленные business_message апдейты, полученные пока бот был офлайн, Telegram **переотправит** — это нормальное поведение webhook.
- Один инстанс бота — один пользователь (MVP). Для multi-user нужен persistent storage для `business_connection_id → user_id`.
- Rate limit Telegram Bot API: 30 запросов/сек общий, 1 запрос/сек на чат. `readBusinessMessage` не имеет явного лимита в документации, но throttling обязателен при высокой нагрузке.

---

## 10. Фаза 2 — расширения (для справки)

| Компонент | Что добавится |
|---|---|
| `BufferService` | In-memory буфер сообщений по `chat_id` с TTL (по умолчанию 24ч, настраиваемый) |
| `SummaryService` | Батч-запрос к Claude API, форматирование дайджеста |
| `NotificationHandler` | Отправка summary в личный чат пользователя с ботом |
| `SettingsHandler` | Команды `/summary on|off`, `/period 12h` через обычный Bot API |
| Storage | SQLite или Postgres для персистентности сессий и настроек |
