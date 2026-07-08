# Telegram Silent Secretary Bot

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![aiogram](https://img.shields.io/badge/aiogram-3.x-2CA5E0)
![Docker](https://img.shields.io/badge/docker-compose-2496ED)

A Telegram bot running in **Business Secretary** mode that automatically marks incoming messages as read in the chats you allow. It works silently: never posts to chats, never sends notifications, and stores nothing on disk.

Subscribed to dozens of channels and chats you never actually read? This bot clears the unread-counter noise for you.

## How it works

```
Telegram → HTTPS → reverse proxy (TLS) → aiohttp:8080 (aiogram) → readBusinessMessage()
```

You assign the bot as a secretary in Telegram Business settings and pick the chats it may see. Telegram delivers each incoming message to the bot's webhook, and the bot immediately marks it as read.

- `business_message` → `readBusinessMessage()`, logged to stdout
- `edited_business_message` → accepted as a no-op (so Telegram stops retrying)
- `business_connection` → connect/disconnect logging
- API errors are logged and never crash the process

## Requirements

- **Telegram Premium** — Business mode is only available to Premium subscribers
- A server with a public IP and a domain (Telegram only delivers webhooks over HTTPS with a valid certificate)
- Docker + Docker Compose
- A reverse proxy with TLS (Nginx or Caddy) on the same host

## Quick start

```sh
git clone https://github.com/IvanKorepin/tg-silent-secretary-bot.git
cd tg-silent-secretary-bot
cp .env.example .env   # fill in BOT_TOKEN, WEBHOOK_URL, WEBHOOK_SECRET
docker compose up -d --build
```

The steps below walk through everything the `.env` needs.

## Deployment

### 1. Register the bot in Telegram

1. Open [@BotFather](https://t.me/BotFather) → `/newbot`.
2. Choose a display name and a username (must end with `bot`).
3. Save the **token** — this is your `BOT_TOKEN`.
4. **Enable Business Mode** — without this step no business updates are delivered at all:
   `/mybots` → select the bot → **Bot Settings** → **Business Mode** → **Turn on**.

### 2. Configure

```sh
cp .env.example .env
```

| Variable | Value |
|---|---|
| `BOT_TOKEN` | token from BotFather |
| `WEBHOOK_URL` | public HTTPS webhook address, e.g. `https://bot.example.com/webhook` |
| `WEBHOOK_SECRET` | random string, ≥16 chars: `openssl rand -hex 32` |
| `WEBHOOK_PATH` | path the bot listens on (default `/webhook`, must match the path in `WEBHOOK_URL`) |
| `PORT` | aiohttp server port (default `8080`) |

`.env` is gitignored — never commit it.

### 3. Reverse proxy (TLS)

Telegram requires HTTPS; TLS terminates at the proxy, traffic to the container goes over plain HTTP.

**Caddy** (obtains and renews the certificate automatically):

```
bot.example.com {
    reverse_proxy localhost:8080
}
```

**Nginx** (certificate via certbot: `certbot --nginx -d bot.example.com`):

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

### 4. Run with Docker

```sh
docker compose up -d --build
docker compose logs -f
```

The logs should show `webhook set: https://...`.

To update after a code change:

```sh
git pull && docker compose up -d --build
```

### 5. Webhook registration

**Nothing to do manually** — the bot calls `setWebhook` on every startup, passing `WEBHOOK_URL`, `WEBHOOK_SECRET`, and the `allowed_updates` list required for business updates.

Verify the webhook is registered:

```sh
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo" | python3 -m json.tool
```

Expected: `"url"` matches `WEBHOOK_URL`, `"pending_update_count": 0`, and `"allowed_updates"` contains `business_message`. The `"last_error_message"` field is the first place to look when something is off.

Remove the webhook (e.g. to run the bot from another host):

```sh
curl -s "https://api.telegram.org/bot<BOT_TOKEN>/deleteWebhook"
```

### 6. Connect the secretary

On your phone (the section may be missing in desktop clients):

1. Telegram → **Settings** → **Telegram Business** → **Chatbots**.
2. Enter the bot's username and connect it.
3. Choose the chats: private chats / exclusions. The bot only ever sees the chats allowed here.

### 7. Verify

Ask someone to message you in an allowed chat (or message yourself from a second account):

- the unread counter clears on its own;
- `docker compose logs -f` shows a `✓ read | conn=... chat=... msg=...` line.

## Troubleshooting

| Symptom | Cause |
|---|---|
| No updates, `getWebhookInfo` shows no errors | Business Mode is off in BotFather, or the chat is not allowed in Telegram Business settings |
| `last_error_message: SSL error` | Invalid or self-signed certificate on the proxy |
| `last_error_message: Connection refused` | Container is down or the proxy points to the wrong port |
| Bot exits on startup with `ValidationError` | `BOT_TOKEN` / `WEBHOOK_URL` / `WEBHOOK_SECRET` missing (secret must be ≥16 chars) |
| `401 Unauthorized` in Telegram API responses | Wrong `BOT_TOKEN` |

## Development

```sh
uv sync
uv run pytest
```

Local run without a public domain: `ngrok http 8080`, put the resulting URL into `WEBHOOK_URL`, then `uv run python -m bot.main`.

Project layout:

```
src/bot/
├── main.py               # entry point: webhook server startup
├── config.py             # pydantic-settings, fail-fast validation
└── handlers/
    ├── business.py       # business_message + edited_business_message
    └── connection.py     # business_connection logging
tests/
└── test_handlers.py
```

## Limitations

- Due to Bot API restrictions, the bot only sees **new** messages (no history) and only in chats explicitly allowed in the Telegram Business UI.
- Nothing is persisted between restarts; updates missed while the bot is down are redelivered by Telegram.
- One instance serves one user (MVP).

## Roadmap

- **Phase 1 (current):** silent mark-as-read, single user, self-hosted
- **Phase 2:** AI-generated chat digests delivered to your private chat with the bot
- **Phase 3:** multi-user SaaS with persistent sessions
