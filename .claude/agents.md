# Project Constitution

This document is the mandatory operating contract for every orchestrator and implementation agent working on this repository. Read it before making decisions, writing code, reviewing changes, or delegating work. If a task conflicts with this constitution, raise the conflict explicitly before proceeding.

## 0. Source Of Truth

`initial_statement.md` is the primary product statement for this project. `agents.md`, role configs, and task files must remain consistent with it. If implementation guidance conflicts with `initial_statement.md`, agents must stop and escalate the conflict to the orchestrator before coding.

## 1. Product Scope

The project is a Telegram bot for splitting restaurant, bar, and cafe receipts in a shared friend group chat. A user sends a receipt photo to the Telegram chat; that sender is treated as the payer. The system recognizes receipt items, lets other users enter only the quantities they consumed, calculates what each user owes the payer, maintains running balances across many bills, supports debtor-initiated debts without receipts, and tracks direct repayments.

The bot must optimize for:

- predictable behavior in group chats;
- transparent receipt items, quantities, debts, balances, and settlements;
- low-friction Telegram and Mini App flows;
- reliable receipt recognition fallback and validation;
- data integrity for money-related operations;
- simple deployment and operations.

The bot must not become a general accounting system. Keep the domain narrow: chats, users, receipts, bill items, user allocations, debtor-initiated manual debts, balances, and settlements.

Bills are editable until the payer finalizes them. Finalized bills move to the archive, are hidden from the active bill list, and become read-only while still affecting balances according to their accounting status.

## 2. Canonical Technology Stack

Until this file is intentionally revised, the canonical stack is:

- Language: Python 3.12+
- Telegram framework: aiogram 3.x
- HTTP API and Mini App backend: FastAPI
- Application model: async-first
- Database access: SQLAlchemy 2.x async ORM/Core
- Migrations: Alembic
- Runtime database: PostgreSQL
- Local/test database: SQLite is allowed only for tests and lightweight local checks when PostgreSQL is unavailable
- Configuration: pydantic-settings
- Validation/data models: Pydantic v2
- Receipt recognition: OpenRouter-compatible vision model client
- Dependency management: uv
- Tests: pytest, pytest-asyncio
- Linting/formatting: Ruff
- Type checking: mypy
- Containerization: Docker and Docker Compose
- CI: GitHub Actions when remote repository automation is introduced

Do not introduce a second framework, ORM, migration tool, or package manager without updating this constitution and documenting the reason.

## 3. Architectural Principles

The architecture is a modular monolith. One backend service and one database are enough for MVP, but code must be split into clear modules with strict dependency boundaries.

### Layers

1. Interface layer
   - Telegram handlers, routers, callback query handlers, command parsing, reply markup.
   - FastAPI routes for the Telegram Mini App and health checks.
   - Must not contain accounting, recognition, or persistence details.

2. Application/service modules
   - Bills, allocations, manual debts, settlements, and workflow coordination.
   - Coordinates repositories, transactions, recognition, validation, and accounting.

3. Accounting/domain module
   - Money calculations, quantity parsing, bill amount calculation, payer remainder rule, balance calculation, settlement application, transfer minimization, invariants, and domain errors.
   - Must be independent from Telegram, FastAPI, OpenRouter, SQLAlchemy sessions, environment variables, and external services.

4. Infrastructure and external integrations
   - Database models, repositories, migrations, OpenRouter client, logging setup, configuration loading, and operational adapters.
   - Depends on application/accounting contracts, not the other way around.

### Dependency Direction

Dependencies flow inward:

`telegram/miniapp -> bills/allocations/debts/settlements -> accounting`

`recognition -> common schemas only; it must not know Telegram chats, debts, or users`

`db/repositories -> service contracts/accounting models`

The accounting module must remain importable and testable without Telegram, FastAPI, database, OpenRouter, or network dependencies.

## 4. Expected Folder Structure

Use this structure unless there is a specific, documented reason to change it:

```text
.
├── agents.md
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
├── .env.example
├── src/
│   └── split_bills_bot/
│       ├── __init__.py
│       ├── main.py
│       ├── config/
│       │   └── settings.py
│       ├── telegram/
│       │   ├── bot.py
│       │   ├── handlers/
│       │   │   ├── photo.py
│       │   │   ├── commands.py
│       │   │   └── callbacks.py
│       │   └── keyboards.py
│       ├── miniapp/
│       │   ├── routes.py
│       │   ├── schemas.py
│       │   ├── auth.py
│       │   ├── templates/
│       │   └── static/
│       ├── recognition/
│       │   ├── service.py
│       │   ├── openrouter_client.py
│       │   ├── prompts.py
│       │   ├── schemas.py
│       │   └── image_preprocessing.py
│       ├── bills/
│       │   ├── service.py
│       │   ├── schemas.py
│       │   └── ports.py
│       ├── allocations/
│       │   ├── service.py
│       │   ├── parser.py
│       │   ├── schemas.py
│       │   └── ports.py
│       ├── debts/
│       │   ├── service.py
│       │   ├── schemas.py
│       │   └── ports.py
│       ├── accounting/
│       │   ├── calculator.py
│       │   ├── balance.py
│       │   ├── settlement.py
│       │   └── schemas.py
│       ├── settlements/
│       │   ├── service.py
│       │   ├── ports.py
│       │   └── schemas.py
│       ├── db/
│       │   ├── repositories/
│       │   ├── session.py
│       │   └── models.py
│       └── common/
│           ├── money.py
│           ├── errors.py
│           └── logging.py
├── migrations/
│   ├── env.py
│   └── versions/
└── tests/
    ├── unit/
    ├── integration/
    ├── recognition/
    └── fixtures/
```

If a new top-level folder is added, document its purpose in the README or in a dedicated architecture note.

## 5. Naming Rules

### Files and Directories

- Python packages and modules: `snake_case`.
- Test files: `test_<subject>.py`.
- Alembic migration files: keep Alembic revision prefix and use descriptive snake_case slugs.
- Configuration examples: `.env.example`, never `.env`.
- Documentation files: lowercase kebab-case or conventional uppercase names such as `README.md`.
- Docker files: `Dockerfile`, `docker-compose.yml`, and optional `docker-compose.override.yml`.

### Python Symbols

- Classes: `PascalCase`.
- Functions, methods, variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Async functions should describe the action, not the mechanism: `create_bill`, `submit_allocations`, `get_balance`, `suggest_settlements`.
- Repository interfaces should end with `Repository`.
- Application services should end with `Service`.
- Telegram handlers should end with `_handler` when exported as functions.
- Recognition schemas should use names such as `RecognizedBill` and `RecognizedBillItem`.

### Database Names

- Tables: plural snake_case, for example `bills`, `bill_items`, `chat_members`.
- Columns: snake_case.
- Foreign keys: `<entity>_id`.
- Timestamp columns: `created_at`, `updated_at`, and explicit domain timestamps such as `settled_at`.

## 6. Accounting And Domain Rules

Money-related logic must be deterministic and test-covered.

- Never use binary floating point for money.
- Use `Decimal` or integer minor units.
- Store currency explicitly where relevant.
- Keep rounding rules centralized.
- Users enter quantities, not money.
- Supported quantity inputs are integers, decimals, and fractions such as `3`, `0.5`, `2/6`, and `1/6`.
- Empty value or `0` means the user did not consume that item.
- For every item, the sum of all explicit allocations, including payer allocations, must not exceed
  the receipt item quantity.
- Payer allocations reserve item quantity for other participants but do not create self-debt.
- The payer owns all unallocated remainder. No debt is created from the payer to themselves.
- Bill debts are derived from allocated quantities multiplied by normalized unit prices.
- Running balances must net debts across many bills and confirmed settlements.
- Debts without receipts must be created only by the debtor, never by a creditor claiming another user owes them money.
- Manual debts affect balances immediately after creation because the debtor is the actor recording their own obligation.
- Pending and rejected settlements must not affect balances.
- Debtor-reported repayments require recipient confirmation.
- Recipient-reported repayments are confirmed immediately because the debtor is not harmed by debt
  forgiveness.
- Settlement suggestions should minimize transfers without hiding balances.
- Domain errors must be explicit and user-messageable by the application layer.

Telegram user IDs, chat IDs, and message IDs are transport identifiers. Do not treat them as domain entities by themselves.

## 7. Configuration and Secrets

- Runtime configuration must be read from environment variables through a typed settings object.
- Commit `.env.example` with safe placeholders.
- Never commit `.env`, bot tokens, production database URLs, user data exports, or chat dumps.
- Configuration validation should fail fast at startup.
- Local defaults may exist only when they are safe and obvious.
- Required production-facing variables include `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`, `DATABASE_URL`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `APP_BASE_URL`, and `DEFAULT_CURRENCY`.

## 8. Runtime Modes

- Local development uses aiogram polling by default.
- Production uses Telegram webhooks served through FastAPI.
- Webhook requests must validate `TELEGRAM_WEBHOOK_SECRET`.
- Polling must not be used in production unless the orchestrator explicitly approves an operational exception.

## 9. Persistence and Migrations

- All schema changes must go through Alembic migrations.
- Do not mutate database schema from application startup code.
- Repository methods should expose domain-oriented operations, not raw ORM leakage.
- Transactions belong in the application/service layer or a dedicated unit-of-work abstraction.
- Database models may use SQLAlchemy, but domain entities must not inherit from ORM base classes.
- MVP data model must cover `users`, `chats`, `chat_members`, `bills`, `bill_items`, `bill_item_allocations`, `manual_debts`, and `settlements`.
- `ledger_entries` is optional for MVP; balances may be calculated from bill item allocations, manual debts, and confirmed settlements.
- Repository contracts live in feature modules as `ports.py` files.
- Concrete SQLAlchemy repository adapters live under `src/split_bills_bot/db/repositories/`.
- Canonical bill statuses are `recognized`, `needs_manual_review`, and `manually_accepted`.
- `recognized` and `manually_accepted` bills affect balances.
- `needs_manual_review` bills do not affect balances.
- A bill exits `needs_manual_review` through manual correction, payer manual acceptance, or a later recognition retry that produces validated totals.
- Finalized bills are archived/read-only but keep their existing accounting status for balance inclusion.

## 10. Receipt Adjustment Accounting

Receipt adjustments include tax, service fee, discount, and payable-total rounding differences.

MVP accounting rule:

- Bill item allocations first produce each participant's base item amount.
- If receipt-level tax, service fee, or discount values are available and validated, distribute them proportionally by each participant's base item amount, including the payer's implicit remainder.
- Service fee and tax are positive adjustments.
- Discount is a negative adjustment.
- Rounding differences between allocated adjusted shares and the bill total are assigned to the payer.
- Total validation tolerance is `max(1 minor currency unit, 0.5% of bill total)`.
- If recognition produces inconsistent totals beyond that tolerance, mark the bill as `needs_manual_review`; such a bill must not affect balances until corrected, manually accepted, or re-recognized successfully.

## 11. Telegram And Mini App Rules

- Handlers should be thin.
- Use routers grouped by workflow or command area.
- Keep keyboards and callback data builders near the bot layer.
- Callback payloads must be versioned or structured enough to survive future changes.
- User-facing text should be centralized enough to support future localization.
- Avoid long blocking work inside update handlers.
- Log operational details, but never log secrets or full private user messages unless explicitly needed for debugging and sanitized.
- Telegram photo handlers identify the payer from the message sender.
- Receipt photo flow must post a parsed bill summary with a `Fill mine` / `Заполнить мое` button.
- The Mini App is responsible for showing a bill form, validating Telegram WebApp init data, identifying the current user, and submitting allocations.
- The Mini App must not calculate final debts itself.
- The Mini App exposes payer-only bill finalization. Finalized bills must be shown read-only and must not accept allocation submissions.
- MVP includes a minimal Mini App UI, implemented as server-rendered or static assets under `src/split_bills_bot/miniapp/templates/` and `src/split_bills_bot/miniapp/static/`.
- MVP Telegram commands include `/start`, `/help`, `/balance`, `/bills`, `/bill <id>`, `/owe @user amount`, `/paid @user amount`, and `/received @user amount`.
- `/start` should show menu buttons for the main command flows, including prompted `I owe`, `I paid`, and `I received` inputs that accept the next message as user and amount without repeating the command name.
- After a `/start` menu button is handled, the bot should delete the handled menu message when Telegram allows it, so group chats do not accumulate obsolete menu messages.
- `/owe @user amount` records that the command sender owes the target user money. It must not support creditor-created debt claims.
- `/paid` user resolution must prefer Telegram mention entities, then reply-to-user flow, then username as a convenience fallback.
- `/owe` user resolution follows the same mention, reply-to-user, then username fallback order.
- Ambiguous or unresolved repayment recipients must be rejected.
- `/paid @user amount` uses the chat default currency unless an explicit supported currency is provided.
- `/received @user amount` uses the chat default currency unless an explicit supported currency is
  provided and creates a confirmed settlement from the mentioned user to the command sender.

## 12. Recognition Rules

- Recognition is responsible for image preprocessing, OpenRouter API calls, prompt management, model-output validation, and receipt item normalization.
- Recognition must return a structured `RecognizedBill` object.
- Recognition must know nothing about Telegram chats, debts, balances, or users.
- Recognition code must not import from `bills`, `allocations`, `settlements`, `telegram`, `miniapp`, or `db` modules. It may read `bills/schemas.py` only as compatibility context during development.
- Store raw model output for traceability.
- Handle invalid model responses, empty receipt items, failed OpenRouter requests, and low-confidence results explicitly.
- Before live recognition is fully connected, the project must support manual/dev bill creation for deterministic testing.

## 13. Testing Policy

Every non-trivial change needs an appropriate test.

Minimum expectations:

- Accounting calculations and quantity parser: unit tests.
- Bills, allocations, and settlements services: unit tests with fake repositories or integration tests where persistence matters.
- Repositories and migrations: integration tests.
- Telegram handlers and Mini App routes: tests for routing, parsing, authorization, and validation behavior.
- Recognition: schema validation tests, saved raw JSON examples, and fixture-based tests without live API calls.

Tests must be deterministic. Avoid tests that depend on real Telegram APIs, wall-clock time, external networks, or production databases.

## 14. Code Quality Rules

- Prefer small modules with clear responsibility.
- Prefer explicit types at public boundaries.
- Avoid global mutable state.
- Avoid broad exception swallowing.
- Keep comments rare and useful; explain why, not what obvious code does.
- Avoid premature abstractions, but preserve layer boundaries.
- Do not add dependencies for small utilities that Python or the existing stack already handles.
- When adding a dependency, document why it is needed in the change summary or PR description.

## 15. Agent Workflow

Project agent roles are declared in `.codex/agents/`. These configuration files define ownership, allowed read scope, restricted write scope, responsibilities, constraints, and acceptance criteria for each specialized contributor.

Agent handoff reports must be written to `.codex/handoffs/` using the template in `.codex/handoffs/README.md`. Later agents must treat these handoffs as part of their required context.

Current declared roles:

- `domain-engineer.yaml`: accounting entities, money logic, quantity parsing, balances, and settlement minimization.
- `application-engineer.yaml`: bills, allocations, settlements use cases, DTOs, ports, and service orchestration.
- `bot-interface-engineer.yaml`: Telegram handlers, routers, keyboards, and conversation flows.
- `miniapp-engineer.yaml`: FastAPI Mini App routes, schemas, WebApp authentication, and allocation form backend.
- `recognition-engineer.yaml`: receipt image preprocessing, OpenRouter client, prompts, model-output validation, and normalization.
- `persistence-engineer.yaml`: database models, repositories, migrations, and data integrity.
- `platform-engineer.yaml`: project setup, configuration, Docker, CI, logging, and operations.
- `qa-engineer.yaml`: test strategy, regression coverage, fixtures, and verification.
- `technical-writer.yaml`: bilingual Russian and English project documentation based on verified work from other agents.

Every agent must:

1. Read `initial_statement.md` before modifying the repository.
2. Read `agents.md` before modifying the repository.
3. Read its own role configuration from `.codex/agents/` before modifying the repository.
4. Inspect existing code before designing a change.
5. Keep changes scoped to the assigned task and role ownership.
6. Avoid reverting or overwriting unrelated work.
7. Preserve architecture boundaries.
8. Add or update tests when behavior changes.
9. Run the narrowest meaningful verification command before reporting completion.
10. Report changed files, verification results, and unresolved risks.

The orchestrator must:

- split work into tasks with clear ownership of files or modules;
- avoid assigning overlapping write scopes to parallel agents;
- validate agent output against this constitution;
- reject changes that bypass the domain/application/infrastructure separation;
- keep this file updated when architectural decisions intentionally change.

## 16. Review and Acceptance Criteria

A change is acceptable only when:

- it satisfies the requested behavior;
- it follows the folder and naming rules;
- domain logic remains independent from Telegram and persistence;
- migrations are present for schema changes;
- tests cover meaningful new behavior;
- lint/type/test commands pass or failures are explicitly explained;
- no secrets or local-only files are committed;
- documentation is updated when setup, commands, or architecture change.

## 17. Change Control

This constitution is allowed to evolve, but changes must be intentional.

When changing this file:

- explain why the rule changed;
- keep existing project code and documentation consistent with the new rule;
- avoid weakening architectural boundaries for short-term convenience;
- treat stack changes as major decisions requiring explicit justification.
