
from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Expense
from schemas import ExpenseCreate, ExpenseResponse, ExpenseUpdate


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Personal Expense Tracker API",
    description="Manage expenses and view spending summaries.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
def home():
    return {"message": "Expense Tracker API is running!"}


@app.post("/expenses", response_model=ExpenseResponse, status_code=201)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
):
    new_expense = Expense(**expense.model_dump())
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


@app.get("/expenses", response_model=list[ExpenseResponse])
def list_expenses(
    category: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Expense)

    if category:
        query = query.filter(Expense.category == category)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)

    return (
        query.order_by(Expense.expense_date.desc(), Expense.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@app.get("/expenses/{expense_id}", response_model=ExpenseResponse)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense


@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    updated: ExpenseUpdate,
    db: Session = Depends(get_db),
):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    for key, value in updated.model_dump().items():
        setattr(expense, key, value)

    db.commit()
    db.refresh(expense)
    return expense


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    expense = db.get(Expense, expense_id)
    if expense is None:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return Response(status_code=204)


@app.get("/summary")
def expense_summary(db: Session = Depends(get_db)):
    total = db.query(func.sum(Expense.amount)).scalar() or 0.0
    count = db.query(func.count(Expense.id)).scalar() or 0

    categories = (
        db.query(Expense.category, func.sum(Expense.amount))
        .group_by(Expense.category)
        .all()
    )

    return {
        "total_spent": round(total, 2),
        "expense_count": count,
        "category_totals": {
            category: round(amount, 2)
            for category, amount in categories
        },
    }


@app.get("/summary/monthly")
def monthly_summary(db: Session = Depends(get_db)):
    month = func.strftime("%Y-%m", Expense.expense_date)

    rows = (
        db.query(month.label("month"), func.sum(Expense.amount))
        .group_by(month)
        .order_by(month)
        .all()
    )

    return {
        "monthly_totals": [
            {"month": month_name, "total": round(total, 2)}
            for month_name, total in rows
        ]
    }
