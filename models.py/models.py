
from sqlalchemy import Column, Date, Float, Integer, String
from database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    expense_date = Column(Date, nullable=False)
    description = Column(String(300), nullable=True)
