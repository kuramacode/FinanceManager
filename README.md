# FinanceManager

FinanceManager is a Flask web application for personal finance tracking. It helps manage income, expenses, transfers, accounts, categories, budgets, exchange rates, analytics, and optional AI-powered financial insights.

> Stack: **Flask 3 + SQLAlchemy + SQLite + Jinja2 + Flask-Login + OpenRouter AI (optional)**

## Features

- User registration, login, logout, and protected finance pages.
- Transaction management for `income`, `expense`, and `transfer` operations.
- Account management with balances, currency, status, type, subtitle, note, and emoji.
- Category management for income, expense, and transfer categories.
- Budget management with limits, periods, category links, progress, and status detection.
- Dashboard with period filters, income/expense totals, balance, latest transactions, accounts, budgets, and short insights.
- Transaction history timeline with search, type filters, grouping, summaries, and pagination.
- Analytics page built from real transactions, categories, accounts, budgets, and available currencies.
- Currency page with NBU exchange-rate data and conversion support.
- Internationalization for English and Ukrainian UI text.
- Optional AI assistant actions for dashboard, transactions, budgets, accounts, analytics, history, categories, and currency pages.
- JSON API for categories, accounts, budgets, currency conversion, and AI actions.

## Pages And Routes

Main UI:

- `/` - public landing page.
- `/register` - user registration.
- `/login` - user authentication.
- `/logout` - logout.
- `/dashboard` - finance dashboard.
- `/transactions` - create, update, delete, filter, and summarize transactions.
- `/history` - transaction history timeline.
- `/analytics` - analytics view.
- `/accounts` - account management page.
- `/budgets` - budget management page.
- `/category` - category management page.
- `/currency` - exchange-rate and currency page.
- `/language/<language>` - language switch endpoint.

JSON API:

- `GET /api/convert?from=USD&to=UAH&amount=10`
- `GET /api/category`
- `POST /api/category`
- `PUT /api/category/<category_id>`
- `DELETE /api/category/<category_id>`
- `GET /api/accounts`
- `POST /api/accounts`
- `PUT /api/accounts/<account_id>`
- `DELETE /api/accounts/<account_id>`
- `GET /api/budgets`
- `POST /api/budgets`
- `PUT /api/budgets/<budget_id>`
- `DELETE /api/budgets/<budget_id>`
- `GET /api/ai/expense-analysis`
- `POST /api/ai/actions/<action_id>`

Most API routes require an authenticated user session.

## Tech Stack

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Jinja2
- SQLite
- Requests
- Pydantic
- python-dotenv
- unittest

## Quick Start

### 1. Clone The Repository

```bash
git clone <your-repo-url>
cd FinanceManager
```

### 2. Create And Activate A Virtual Environment

Linux / macOS:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

The current local workspace also has an `env/` virtual environment. New setups can use either `env/` or `.venv/`; keep the chosen folder out of git.

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create `.env` in the project root or `app/.env`. Both locations are loaded.

Minimum local config:

```env
SECRET_KEY=change-me
```

Optional database override:

```env
SQLALCHEMY_DATABASE_URI=sqlite:///users.db
```

or:

```env
DATABASE_URL=sqlite:///users.db
```

If no database URL is provided, the app uses:

```text
instance/users.db
```

Optional AI config:

```env
OPENROUTER_API_KEY=your-openrouter-key
OPENROUTER_MODEL=inclusionai/ling-2.6-flash:free
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
AI_TIMEOUT_SECONDS=60
AI_MAX_COMPLETION_TOKENS=800
AI_TEMPERATURE=0.2
OPENROUTER_SITE_URL=http://127.0.0.1:5000
OPENROUTER_APP_TITLE=Finance Manager
```

AI features are optional. Without `OPENROUTER_API_KEY`, the core finance app still runs, but AI endpoints cannot call the provider.

### 5. Run The App

```bash
python run.py
```

Open:

```text
http://127.0.0.1:5000
```

The Flask app is created through `app.create_app()`. On startup it ensures the SQLite directory exists and runs `db.create_all()`.

## Seed Data

Seed supported currencies:

```bash
python -m app.utils.seed_currencies
```

Import NBU exchange rates for configured currencies:

```bash
python -m app.utils.seed_exchange_rates_nbu --start 2026-03-21 --end 2026-04-21
```

The exchange-rate importer calls the public NBU API and writes rates into the configured SQLite database.

## Testing

Run all tests:

```bash
python -m unittest discover -s tests -v
```

The tests create isolated temporary SQLite databases instead of using `instance/users.db`.

## Project Structure

```text
FinanceManager/
|-- run.py
|-- requirements.txt
|-- README.md
|-- app/
|   |-- __init__.py              # app factory, blueprints, extensions
|   |-- config.py                # dotenv and database configuration
|   |-- ai/                      # AI config, provider client, prompts, actions
|   |-- api/                     # JSON API and AI API routes
|   |-- auth/                    # login/logout routes
|   |-- register/                # registration routes
|   |-- main/                    # landing and language routes
|   |-- content/
|   |   |-- lead/                # dashboard, transactions, history, analytics
|   |   |-- money/               # accounts and budgets pages
|   |   `-- manage/              # categories and currency pages
|   |-- models/                  # SQLAlchemy models
|   |-- services/                # domain services
|   |-- clients/                 # external clients, including NBU
|   |-- i18n/                    # translations and language helpers
|   |-- static/                  # CSS and browser scripts
|   |-- templates/               # Jinja templates
|   `-- utils/                   # database, periods, formatting, seed scripts
|-- instance/
|   `-- users.db                 # local SQLite database, generated locally
`-- tests/
```

## Data Model Overview

- `User` - registered application users.
- `Transactions` - income, expense, and transfer records.
- `Categories` - user-scoped transaction categories with emoji, description, type, and built-in flag.
- `Accounts` - user accounts with balances, currency, status, type, subtitle, and note.
- `Budget` - budget limits with period dates and currency.
- `BudgetCategory` - links budgets to categories.
- `Currency` - supported currencies.
- `ExchangeRate` - historical rates, currently seeded from NBU.

## Notes For Development

- The app uses an application factory: import `create_app` from `app`.
- Blueprints are registered in `app/__init__.py`.
- Local SQLite files live in `instance/`.
- Root `.env` and `app/.env` are both supported.
- Keep secrets, virtual environments, generated databases, caches, and logs out of git.
- Some existing source comments/text may still contain mojibake from older encoding issues; README is updated to clean UTF-8 text.

