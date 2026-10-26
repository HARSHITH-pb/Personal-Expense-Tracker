
# Personal Expense Tracker

A web-based expense tracking application built with Python and FastAPI to help users record expenses, monitor daily spending, and manage monthly budgets.

## Features

- Add and delete expense transactions.
- Record expenses by date, category, and amount.
- View transactions for a selected date.
- Set a custom daily spending limit.
- Set a custom monthly spending limit.
- Track spending using circular budget progress indicators.
- View daily totals and monthly spending summaries.
- Highlight individual transactions above ₹10,000 with a DANGER alert.
- Store expense records locally using SQLite.
- Responsive dashboard for desktop and mobile browsers.

## Technology Stack

- **Backend:** Python, FastAPI
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite
- **Validation:** Pydantic
- **Server:** Uvicorn

## Project Structure

```text
expense-tracker-api/
├── main.py
├── main_updated.py
├── expenses.db
├── requirements.txt
├── .gitignore
├── start_tracker.bat
└── .venv/
```

Note: Do not upload `.venv/` or your local `expenses.db` file to a public repository. Keep `main_updated.py` only if you need it as a backup.

## Installation

### 1. Clone or download the project

Open the project folder in Visual Studio Code.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the Application

Start the development server:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Open the application in your browser:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

Alternatively, run `start_tracker.bat` on Windows if you have created the startup script.

## Budget Tracking

The dashboard supports separate daily and monthly spending limits. Users can adjust these limits based on their needs.

- **Daily budget:** Tracks spending against the selected day's limit.
- **Monthly budget:** Tracks spending against the selected month's limit.
- **Transaction alert:** Individual expenses greater than ₹10,000 are marked DANGER.

## Database

Expense transactions and budget settings are stored in a local SQLite database named `expenses.db`.

Back up this file regularly to protect your records.

## Future Improvements

- Expense charts and spending trends.
- Export reports to CSV or Excel.
- Search and filter by category.
- User authentication and secure access.
- Cloud database and public deployment.

## Author

Harshith Pabboju

GitHub: https://github.com/HARSHITH-pb

LinkedIn: https://www.linkedin.com/in/harshith-pabboju-1b1375351
