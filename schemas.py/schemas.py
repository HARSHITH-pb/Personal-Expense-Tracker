
from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    amount: float = Field(gt=0, allow_inf_nan=False)
    category: str = Field(min_length=1, max_length=50)
    expense_date: date
    description: str | None = Field(default=None, max_length=300)


class ExpenseUpdate(ExpenseCreate):
    pass


class ExpenseResponse(ExpenseCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
