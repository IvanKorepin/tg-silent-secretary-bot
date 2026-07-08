# tg-silent-secretary-bot

Telegram-бот в режиме Business Secretary: автоматически отмечает входящие сообщения как прочитанные в разрешённых чатах. Работает тихо — не пишет в чаты, не хранит данные на диске.

## Требования

- **Telegram Premium** у пользователя — режим Telegram Business доступен только подписчикам.
- Сервер с публичным IP и доменом (Telegram шлёт вебхуки только на HTTPS с валидным сертификатом).
- Docker + Docker Compose.
- Reverse proxy с TLS (Nginx или Caddy) на том же сервере.

## 1. Регистрация бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather) → `/newbot`.
2. Задайте имя (отображаемое) и username бота (должен оканчиваться на `bot`).
3. Сохраните выданный **токен** — это `BOT_TOKEN`.
4. **Включите Business Mode** — без этого шага business-апдейты не приходят вообще:
   `/mybots` → выберите бота → **Bot Settings** → **Business Mode** → **Turn on**.

## 2. Конфигурация

```sh
cp .env.example .env
```

| Переменная | Что указать |
|---|---|
| `BOT_TOKEN` | токен из BotFather |
| `WEBHOOK_URL` | публичный HTTPS-адрес вебхука, например `https://bot.example.com/webhook` |
| `WEBHOOK_SECRET` | случайная строка ≥16 символов: `openssl rand -hex 32` |
| `WEBHOOK_PATH` | путь, на котором слушает бот (default `/webhook`, должен совпадать с путём в `WEBHOOK_URL`) |
| `PORT` | порт aiohttp-сервера (default `8080`) |

`.env` в gitignore — не коммитьте его.

## 3. Reverse proxy (TLS)

Telegram требует HTTPS; TLS терминируется на прокси, до контейнера трафик идёт по HTTP.

**Caddy** (сертификат получит и обновит сам):

```
bot.example.com {
    reverse_proxy localhost:8080
}
```

**Nginx** (сертификат — через certbot: `certbot --nginx -d bot.example.com`):

```nginx
server {
    listen 443 ssl;
    server_name bot.example.com;

    ssl_certificate     /etc/letsencrypt/live/bot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.example.com/privkey.pem;

    location /webhook {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
    }
}
```

## 4. Запуск в Docker

```sh
docker compose up -d --build
docker compose logs -f
```

В логах должно появиться `webhook set: https://...`.

Обновление после изменения кода:

```sh
git pull && docker compose up -d --build
```

## 5. Регистрация вебхука

**Ничего делать не нужно** — бот сам вызывает `setWebhook` при каждом старте, передавая `WEBHOOK_URL`, `WEBHOOK_SECRET` и `allowed_updates` для business-апдейтов.

Проверить, что вебхук зарегистрирован:

```sh
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo" | python3 -m json.tool
```

Ожидаемо: `"url"` совпадает с `WEBHOOK_URL`, `"pending_update_count": 0`, `"allowed_updates"` содержит `business_message`. Поле `"last_error_message"` — первое место, куда смотреть при проблемах.

Снять вебхук (например, чтобы погонять бота на другом хосте):

```sh
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/deleteWebhook"
```

## 6. Подключение секретаря

На телефоне (в десктоп-клиентах раздела может не быть):

1. Telegram → **Настройки** → **Telegram Business** → **Чат-боты**.
2. Введите username бота, подключите.
3. Выберите чаты: разделы «Личные чаты» / исключения. Бот видит **только** разрешённые здесь чаты.

## 7. Проверка

Попросите кого-нибудь написать вам в разрешённый чат (или напишите себе со второго аккаунта):

- счётчик непрочитанных обнуляется сам;
- в `docker compose logs -f` появляется строка `✓ read | conn=... chat=... msg=...`.

## Troubleshooting

| Симптом | Причина |
|---|---|
| Нет апдейтов, `getWebhookInfo` без ошибок | Business Mode не включён в BotFather, или чат не разрешён в настройках TG Business |
| `last_error_message: SSL error` | Невалидный/самоподписанный сертификат на прокси |
| `last_error_message: Connection refused` | Контейнер не запущен или прокси указывает не на тот порт |
| Бот падает на старте с `ValidationError` | Не заполнены `BOT_TOKEN` / `WEBHOOK_URL` / `WEBHOOK_SECRET` (секрет — минимум 16 символов) |
| `401 Unauthorized` в логах Telegram-запросов | Неверный `BOT_TOKEN` |

## Разработка

```sh
uv sync
uv run pytest
```

Локальный запуск без публичного домена: `ngrok http 8080`, полученный URL — в `WEBHOOK_URL`, затем `uv run python -m bot.main`.

## Ограничения (MVP)

- Бот видит только новые сообщения (не историю) и только в чатах, разрешённых в TG Business UI.
- Ничего не хранится между перезапусками; пропущенные апдейты Telegram переотправит сам.
- Один инстанс — один пользователь.

Документация: `docs/BUSINESS_ANALYSIS.md`, `docs/SYSTEM_ANALYSIS.md`.
