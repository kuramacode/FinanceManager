# FinanceManager
A web application for personal finance tracking: incomes, expenses, categories, and current balance.

> Stack: **Flask + SQLAlchemy + SQLite + Jinja2 + Flask-Login**

---

## Features

- User registration and login
- Income/expense transaction tracking
- Category-based transactions (with emoji)
- Dashboard with:
  - total income
  - total expenses
  - current balance
  - latest transactions
- Transaction filtering by type (`all`, `income`, `expense`)

---

## Pages / Routes

Current app routes:

- `/` — landing page
- `/register` — user registration
- `/login` — authentication
- `/dashboard` — finance dashboard
- `/transactions` — list/create transactions
- `/logout` — logout

---

## Tech Stack

- Python 3.10+
- Flask
- Flask-SQLAlchemy
- Flask-Login
- Jinja2
- SQLite
- unittest

---

## Quick Start

### 1) Clone the repository

```bash
git clone <your-repo-url>
cd FinanceManager
```

### 2) Create and activate a virtual environment

**Linux / macOS**
```bash
python -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-key
```

> SQLite database is created automatically at `instance/users.db`.

### 5) Run the app

```bash
python app.py
```

Open: `http://127.0.0.1:5000`

---

## Testing

Run all tests:

```bash
python -m unittest discover -s tests -v
```

---

## VS Code debug troubleshooting (Windows)

If VS Code fails to start debugging with:

`AttributeError: module 'sys' has no attribute 'real_prefix'`

this is usually caused by a mismatch between the selected Python interpreter and
the environment that `debugpy` expects.

### Fix checklist

1. Select the project virtual environment in VS Code:
   - `Ctrl+Shift+P` → **Python: Select Interpreter** → choose `.venv\Scripts\python.exe`.
2. Recreate the virtual environment (if needed):

   ```powershell
   rmdir /s /q .venv
   py -3 -m venv .venv
   .venv\Scripts\python -m pip install --upgrade pip
   .venv\Scripts\python -m pip install -r requirements.txt
   ```

3. Ensure no local file is shadowing Python stdlib modules:
   - there should be no `sys.py` in your workspace.
4. Update the Python extension in VS Code and restart the editor.
5. If the issue persists, pin `debugpy` in your environment and try again:

   ```powershell
   .venv\Scripts\python -m pip install "debugpy>=1.8.0"
   ```

---

## Project Structure

```text
FinanceManager/
├── app.py
├── config.py
├── models.py
├── requirements.txt
├── templates/
├── static/
├── utils/
└── tests/
```

---

## Data Models

### `User`
- `id`
- `username` (unique)
- `email` (unique)
- `password` (hashed)

### `Transactions`
- `id`
- `amount`
- `date`
- `description`
- `user_id` (FK -> users.id)
- `category_id` (FK -> categories.id)
- `type` (`income` or `expense`)

### `Categories`
- `id`
- `name`
- `user_id` (FK -> users.id)
- `emoji`

---

## Roadmap

- [ ] REST API (JSON endpoints)
- [ ] Transaction pagination
- [ ] CSV export
- [ ] Income/expense charts
- [ ] Docker setup
- [ ] CI (GitHub Actions)
- [ ] AI integration
- [ ] Analytics
- [ ] Categories and Budget systems
