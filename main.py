from contextlib import asynccontextmanager
from datetime import date
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

DB_FILE = "expenses.db"
DANGER_AMOUNT = 10000


def connect_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def setup_db():
    with connect_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL,
                expense_date TEXT NOT NULL,
                description TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                budget_type TEXT PRIMARY KEY CHECK(budget_type IN ('daily', 'monthly')),
                amount REAL NOT NULL CHECK(amount > 0)
            )
        """)
        # Default limits are created only once. Change them in the dashboard.
        conn.execute(
            "INSERT OR IGNORE INTO budgets (budget_type, amount) VALUES ('daily', 3000)"
        )
        conn.execute(
            "INSERT OR IGNORE INTO budgets (budget_type, amount) VALUES ('monthly', 50000)"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_db()
    yield


app = FastAPI(title="Personal Expense Tracker", lifespan=lifespan)


class ExpenseInput(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0, allow_inf_nan=False)
    category: str = Field(min_length=1, max_length=50)
    expense_date: date
    description: str | None = Field(default=None, max_length=300)


class BudgetInput(BaseModel):
    amount: float = Field(gt=0, allow_inf_nan=False)


def serialize(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "amount": row["amount"],
        "category": row["category"],
        "expense_date": row["expense_date"],
        "description": row["description"],
        "danger": row["amount"] > DANGER_AMOUNT,
    }


PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Personal Expense Tracker</title>
<style>
:root { --navy:#172554; --blue:#2563eb; --green:#16a34a; --orange:#d97706; --red:#dc2626; }
* { box-sizing:border-box; }
body { margin:0; background:#f3f6fb; color:#182230; font-family:Arial,sans-serif; }
header { background:var(--navy); color:white; padding:24px 6%; }
header h1 { margin:0 0 6px; font-size:28px; }
header p { margin:0; color:#dbeafe; }
main { max-width:1150px; margin:25px auto; padding:0 16px 35px; }
.panel,.card { background:white; border-radius:14px; padding:20px; box-shadow:0 3px 15px #15294b0c; }
h2,h3 { margin-top:0; }
label { display:block; font-size:13px; font-weight:600; margin:12px 0 6px; }
input,select { width:100%; padding:11px; border:1px solid #cbd5e1; border-radius:8px; font-size:14px; background:white; }
button { border:0; border-radius:8px; padding:11px 14px; cursor:pointer; font-weight:700; }
.primary { background:var(--blue); color:white; }
.secondary { background:#e2e8f0; color:#172554; }
.danger-btn { background:#fee2e2; color:#991b1b; }
.cards { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; margin-bottom:18px; }
.card span { color:#64748b; font-size:13px; }
.card h2 { margin:10px 0 0; font-size:25px; overflow-wrap:anywhere; }
.trackers { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; margin-bottom:18px; }
.tracker-card { display:flex; align-items:center; gap:18px; }
.gauge { width:150px; height:150px; flex:0 0 150px; position:relative; }
.gauge svg { width:100%; height:100%; transform:rotate(-90deg); }
.gauge circle { fill:none; stroke-width:12; }
.gauge .track { stroke:#e5e7eb; }
.gauge .progress { stroke:var(--green); stroke-linecap:round; transition:stroke-dashoffset .3s; }
.gauge .progress.warn { stroke:var(--orange); }
.gauge .progress.over { stroke:var(--red); }
.gauge-center { position:absolute; inset:0; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; }
.gauge-center strong { font-size:20px; }
.gauge-center small { color:#64748b; font-size:11px; margin-top:4px; }
.tracker-info { min-width:0; }
.tracker-info h3 { margin:0 0 8px; }
.tracker-info p { margin:6px 0; font-size:13px; color:#475569; overflow-wrap:anywhere; }
.status { display:inline-block; border-radius:999px; padding:5px 8px; font-size:11px; font-weight:bold; background:#dcfce7; color:#166534; }
.status.warn { background:#fef3c7; color:#92400e; }
.status.over { background:#fee2e2; color:#991b1b; }
.layout { display:grid; grid-template-columns:320px 1fr; gap:18px; align-items:start; }
form .primary { width:100%; margin-top:16px; }
.filter-row { display:grid; grid-template-columns:1fr 1fr auto; gap:10px; align-items:end; margin-bottom:14px; }
.table-wrap { overflow-x:auto; }
table { width:100%; border-collapse:collapse; min-width:650px; }
th,td { text-align:left; padding:11px 8px; border-bottom:1px solid #e2e8f0; font-size:13px; }
th { color:#64748b; }
.alert { color:#b91c1c; background:#fee2e2; padding:5px 7px; border-radius:6px; font-weight:bold; font-size:11px; white-space:nowrap; }
.empty { color:#64748b; padding:20px 0; }
#message { font-size:13px; margin-top:10px; }
.history { margin-top:18px; }
.history-row { display:grid; grid-template-columns:1fr auto auto; gap:15px; padding:11px 0; border-bottom:1px solid #e2e8f0; font-size:13px; }
.muted { color:#64748b; }
@media(max-width:800px) {
 .cards { grid-template-columns:1fr; }
 .trackers { grid-template-columns:1fr; }
 .layout { grid-template-columns:1fr; }
 .tracker-card { gap:12px; }
 .gauge { width:125px; height:125px; flex-basis:125px; }
 .filter-row { grid-template-columns:1fr; }
 header { padding:22px; }
}
</style>
</head>
<body>
<header>
  <h1>Spending Tracker</h1>
  <p>Track expenses by date, set your own budgets, and spot high-value transactions.</p>
</header>
<main>
  <section class="cards">
    <div class="card"><span>Spending on selected day</span><h2 id="dayTotal">₹0.00</h2></div>
    <div class="card"><span>Spending in selected month</span><h2 id="monthTotal">₹0.00</h2></div>
    <div class="card"><span>Transactions over ₹10,000</span><h2 id="dangerCount">0</h2></div>
  </section>

  <section class="trackers">
    <div class="panel tracker-card">
      <div class="gauge">
        <svg viewBox="0 0 120 120" aria-label="Daily budget progress">
          <circle class="track" cx="60" cy="60" r="48"></circle>
          <circle class="progress" id="dailyProgress" cx="60" cy="60" r="48"></circle>
        </svg>
        <div class="gauge-center"><strong id="dailyPercent">0%</strong><small>DAILY LIMIT</small></div>
      </div>
      <div class="tracker-info">
        <h3>Daily budget</h3>
        <p>Spent: <strong id="dailySpent">₹0.00</strong></p>
        <p>Remaining: <strong id="dailyRemaining">₹0.00</strong></p>
        <span id="dailyStatus" class="status">ON TRACK</span>
        <label for="dailyBudget">Set daily limit (₹)</label>
        <input id="dailyBudget" type="number" min="1" step="1" value="3000">
        <button class="primary" id="saveDaily" type="button" style="margin-top:8px">Save daily limit</button>
      </div>
    </div>
    <div class="panel tracker-card">
      <div class="gauge">
        <svg viewBox="0 0 120 120" aria-label="Monthly budget progress">
          <circle class="track" cx="60" cy="60" r="48"></circle>
          <circle class="progress" id="monthlyProgress" cx="60" cy="60" r="48"></circle>
        </svg>
        <div class="gauge-center"><strong id="monthlyPercent">0%</strong><small>MONTHLY LIMIT</small></div>
      </div>
      <div class="tracker-info">
        <h3>Monthly budget</h3>
        <p>Spent: <strong id="monthlySpent">₹0.00</strong></p>
        <p>Remaining: <strong id="monthlyRemaining">₹0.00</strong></p>
        <span id="monthlyStatus" class="status">ON TRACK</span>
        <label for="monthlyBudget">Set monthly limit (₹)</label>
        <input id="monthlyBudget" type="number" min="1" step="1" value="50000">
        <button class="primary" id="saveMonthly" type="button" style="margin-top:8px">Save monthly limit</button>
      </div>
    </div>
  </section>

  <section class="layout">
    <div class="panel">
      <h3>Add an expense</h3>
      <form id="expenseForm">
        <label for="title">Expense name</label>
        <input id="title" maxlength="100" placeholder="e.g. Groceries" required>
        <label for="amount">Amount (₹)</label>
        <input id="amount" type="number" min="0.01" step="0.01" placeholder="e.g. 450" required>
        <label for="category">Category</label>
        <select id="category" required>
          <option>Food</option><option>Travel</option><option>Shopping</option>
          <option>Bills</option><option>Education</option><option>Health</option>
          <option>Entertainment</option><option>Other</option>
        </select>
        <label for="expenseDate">Transaction date</label>
        <input id="expenseDate" type="date" required>
        <label for="description">Notes (optional)</label>
        <input id="description" maxlength="300" placeholder="Add a note">
        <button class="primary" type="submit">+ Add expense</button>
        <div id="message" role="status"></div>
      </form>
    </div>

    <div>
      <div class="panel">
        <h3>Date-wise transactions</h3>
        <div class="filter-row">
          <div><label for="filterDate">Choose date</label><input id="filterDate" type="date"></div>
          <div><label for="filterMonth">Choose month</label><input id="filterMonth" type="month"></div>
          <button class="secondary" id="todayBtn" type="button">Today</button>
        </div>
        <p class="muted" id="filterSummary">Showing transactions for selected date.</p>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Expense</th><th>Category</th><th>Date</th><th>Amount</th><th>Alert</th><th>Action</th></tr></thead>
            <tbody id="expenseRows"></tbody>
          </table>
        </div>
        <p id="empty" class="empty" hidden>No transactions for this date. Choose another date or add an expense.</p>
      </div>
      <div class="panel history">
        <h3>Daily totals in selected month</h3>
        <div id="dailyHistory"></div>
      </div>
    </div>
  </section>
</main>
<script>
const $ = id => document.getElementById(id);
const today = new Date();
const localToday = new Date(today.getTime() - today.getTimezoneOffset() * 60000).toISOString().slice(0,10);
$('expenseDate').value = localToday;
$('filterDate').value = localToday;
$('filterMonth').value = localToday.slice(0,7);
const money = value => '₹' + Number(value || 0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = 'Request failed';
    try { const body = await response.json(); detail = body.detail || detail; } catch {}
    throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  if (response.status === 204) return null;
  return response.json();
}

function setGauge(prefix, spent, limit) {
  const safeLimit = Number(limit) || 1;
  const percent = spent / safeLimit * 100;
  const shownPercent = Math.round(percent);
  const circle = $(prefix + 'Progress');
  const circumference = 2 * Math.PI * 48;
  circle.style.strokeDasharray = circumference;
  circle.style.strokeDashoffset = circumference * (1 - Math.min(percent,100)/100);
  circle.classList.toggle('warn', percent >= 80 && percent <= 100);
  circle.classList.toggle('over', percent > 100);
  $(prefix + 'Percent').textContent = shownPercent + '%';
  $(prefix + 'Spent').textContent = money(spent);
  $(prefix + 'Remaining').textContent = money(Math.max(0, safeLimit - spent));
  const status = $(prefix + 'Status');
  status.className = 'status' + (percent > 100 ? ' over' : percent >= 80 ? ' warn' : '');
  status.textContent = percent > 100 ? 'OVER LIMIT' : percent >= 80 ? 'NEAR LIMIT' : 'ON TRACK';
}

async function loadDashboard() {
  try {
    const selectedDate = $('filterDate').value || localToday;
    const selectedMonth = $('filterMonth').value || localToday.slice(0,7);
    const [daySummary, monthSummary, budgets, dailyRows, expenses] = await Promise.all([
      request('/summary?day=' + encodeURIComponent(selectedDate)),
      request('/summary?month=' + encodeURIComponent(selectedMonth)),
      request('/budgets'),
      request('/daily-totals?month=' + encodeURIComponent(selectedMonth)),
      request('/expenses?day=' + encodeURIComponent(selectedDate))
    ]);
    $('dayTotal').textContent = money(daySummary.total_spent);
    $('monthTotal').textContent = money(monthSummary.total_spent);
    $('dangerCount').textContent = monthSummary.danger_count;
    $('dailyBudget').value = budgets.daily;
    $('monthlyBudget').value = budgets.monthly;
    setGauge('daily', daySummary.total_spent, budgets.daily);
    setGauge('monthly', monthSummary.total_spent, budgets.monthly);
    $('filterSummary').textContent = 'Showing ' + selectedDate + ' · Daily total: ' + money(daySummary.total_spent);

    const tbody = $('expenseRows');
    tbody.replaceChildren();
    $('empty').hidden = expenses.length !== 0;
    for (const expense of expenses) {
      const row = document.createElement('tr');
      for (const value of [expense.title, expense.category, expense.expense_date, money(expense.amount)]) {
        const cell = document.createElement('td');
        cell.textContent = value;
        row.appendChild(cell);
      }
      const alertCell = document.createElement('td');
      if (expense.danger) {
        const alert = document.createElement('span');
        alert.className = 'alert';
        alert.textContent = 'DANGER';
        alertCell.appendChild(alert);
      } else {
        alertCell.textContent = '—';
      }
      row.appendChild(alertCell);
      const actionCell = document.createElement('td');
      const button = document.createElement('button');
      button.className = 'danger-btn';
      button.textContent = 'Delete';
      button.addEventListener('click', () => deleteExpense(expense.id));
      actionCell.appendChild(button);
      row.appendChild(actionCell);
      tbody.appendChild(row);
    }

    const history = $('dailyHistory');
    history.replaceChildren();
    if (!dailyRows.length) {
      history.textContent = 'No expenses recorded for this month yet.';
      history.className = 'muted';
    } else {
      history.className = '';
      for (const item of dailyRows) {
        const row = document.createElement('div');
        row.className = 'history-row';
        const day = document.createElement('span');
        day.textContent = item.expense_date;
        const count = document.createElement('span');
        count.className = 'muted';
        count.textContent = item.transaction_count + ' transaction(s)';
        const total = document.createElement('strong');
        total.textContent = money(item.total);
        row.append(day, count, total);
        history.appendChild(row);
      }
    }
  } catch (error) {
    $('message').textContent = 'Could not load dashboard: ' + error.message;
  }
}

$('expenseForm').addEventListener('submit', async event => {
  event.preventDefault();
  $('message').textContent = 'Saving...';
  const data = {
    title: $('title').value.trim(),
    amount: Number($('amount').value),
    category: $('category').value,
    expense_date: $('expenseDate').value,
    description: $('description').value.trim() || null
  };
  try {
    await request('/expenses', {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)
    });
    $('message').textContent = data.amount > 10000
      ? 'Expense saved. DANGER: this single transaction exceeds ₹10,000.'
      : 'Expense added successfully!';
    $('filterDate').value = data.expense_date;
    $('filterMonth').value = data.expense_date.slice(0,7);
    $('form')?.reset();
    $('title').value = '';
    $('amount').value = '';
    $('description').value = '';
    await loadDashboard();
  } catch (error) {
    $('message').textContent = 'Could not save: ' + error.message;
  }
});

async function saveBudget(type, inputId) {
  const amount = Number($(inputId).value);
  if (!Number.isFinite(amount) || amount <= 0) {
    $('message').textContent = 'Enter a budget greater than zero.';
    return;
  }
  try {
    await request('/budgets/' + type, {
      method:'PUT', headers:{'Content-Type':'application/json'}, body:JSON.stringify({amount})
    });
    $('message').textContent = (type === 'daily' ? 'Daily' : 'Monthly') + ' limit saved.';
    await loadDashboard();
  } catch (error) {
    $('message').textContent = 'Could not save budget: ' + error.message;
  }
}
$('saveDaily').addEventListener('click', () => saveBudget('daily','dailyBudget'));
$('saveMonthly').addEventListener('click', () => saveBudget('monthly','monthlyBudget'));
$('filterDate').addEventListener('change', loadDashboard);
$('filterMonth').addEventListener('change', loadDashboard);
$('todayBtn').addEventListener('click', () => {
  $('filterDate').value = localToday;
  $('filterMonth').value = localToday.slice(0,7);
  loadDashboard();
});

async function deleteExpense(id) {
  if (!confirm('Delete this expense?')) return;
  try {
    await request('/expenses/' + id, {method:'DELETE'});
    $('message').textContent = 'Expense deleted.';
    await loadDashboard();
  } catch (error) {
    $('message').textContent = 'Could not delete: ' + error.message;
  }
}
loadDashboard();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return PAGE


@app.get("/expenses")
def list_expenses(
    day: date | None = Query(default=None),
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
):
    sql = "SELECT * FROM expenses"
    params = []
    if day:
        sql += " WHERE expense_date = ?"
        params.append(day.isoformat())
    elif month:
        sql += " WHERE substr(expense_date, 1, 7) = ?"
        params.append(month)
    sql += " ORDER BY expense_date DESC, id DESC"
    with connect_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [serialize(row) for row in rows]


@app.post("/expenses", status_code=201)
def create_expense(expense: ExpenseInput):
    data = expense.model_dump()
    with connect_db() as conn:
        cursor = conn.execute(
            """INSERT INTO expenses
            (title, amount, category, expense_date, description)
            VALUES (?, ?, ?, ?, ?)""",
            (
                data["title"].strip(),
                data["amount"],
                data["category"].strip(),
                data["expense_date"].isoformat(),
                data["description"],
            ),
        )
        row = conn.execute(
            "SELECT * FROM expenses WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return serialize(row)


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    with connect_db() as conn:
        cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Expense not found")


@app.get("/budgets")
def get_budgets():
    with connect_db() as conn:
        rows = conn.execute("SELECT budget_type, amount FROM budgets").fetchall()
    result = {row["budget_type"]: row["amount"] for row in rows}
    return {"daily": result.get("daily", 3000), "monthly": result.get("monthly", 50000)}


@app.put("/budgets/{budget_type}")
def update_budget(budget_type: str, budget: BudgetInput):
    if budget_type not in ("daily", "monthly"):
        raise HTTPException(status_code=400, detail="Budget type must be daily or monthly")
    with connect_db() as conn:
        conn.execute(
            """INSERT INTO budgets (budget_type, amount) VALUES (?, ?)
            ON CONFLICT(budget_type) DO UPDATE SET amount = excluded.amount""",
            (budget_type, budget.amount),
        )
    return {"budget_type": budget_type, "amount": budget.amount}


@app.get("/summary")
def expense_summary(
    day: date | None = Query(default=None),
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
):
    where = []
    params = []
    if day:
        where.append("expense_date = ?")
        params.append(day.isoformat())
    elif month:
        where.append("substr(expense_date, 1, 7) = ?")
        params.append(month)
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    with connect_db() as conn:
        total = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses" + clause, params).fetchone()[0]
        count = conn.execute("SELECT COUNT(*) FROM expenses" + clause, params).fetchone()[0]
        danger_count = conn.execute(
            "SELECT COUNT(*) FROM expenses" + (clause + " AND " if clause else " WHERE ") + "amount > ?",
            params + [DANGER_AMOUNT],
        ).fetchone()[0]
        rows = conn.execute(
            "SELECT category, SUM(amount) AS total FROM expenses" + clause + " GROUP BY category",
            params,
        ).fetchall()
    return {
        "total_spent": round(total, 2),
        "expense_count": count,
        "danger_count": danger_count,
        "category_totals": {row["category"]: round(row["total"], 2) for row in rows},
    }


@app.get("/daily-totals")
def daily_totals(month: str = Query(pattern=r"^\d{4}-\d{2}$")):
    with connect_db() as conn:
        rows = conn.execute(
            """SELECT expense_date, ROUND(SUM(amount), 2) AS total, COUNT(*) AS transaction_count
            FROM expenses WHERE substr(expense_date, 1, 7) = ?
            GROUP BY expense_date ORDER BY expense_date DESC""",
            (month,),
        ).fetchall()
    return [dict(row) for row in rows]
