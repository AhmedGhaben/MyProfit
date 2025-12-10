"""Core domain models for the personal finance engine."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Mapping


class FinanceError(ValueError):
    """Base error for finance-related problems."""
    pass


class NegativeAmountError(FinanceError):
    """Amount must be non-negative."""
    pass


class InvalidAmountError(FinanceError):
    """Invalid money amount type (not int/float)."""
    pass

class InvalidCategoryError(FinanceError):
  #might not need it if we make the category buttons
  pass

class ExpenseCategory(Enum):
    """Categories for personal expenses."""
    HOUSING = "housing"
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    HEALTH = "health"
    EDUCATION = "education"
    OTHER = "other"

@dataclass(frozen=True, order=True)
class Expense:
  """
  arguments:
  -amount(must be float or int and non negative)
  -category:object (probably buttons in the telegram bot)
  -description optional
  """
  amount: float
  category: ExpenseCategory
  description: str | None = None

  def __post_init__(self) -> None:
    if not isinstance(self.amount, (int, float)):
      raise InvalidAmountError("Expense amount must be int or float.")
    if self.amount < 0:
      raise NegativeAmountError("Expense amount cannot be negative.")

  
  def to_dict(self) -> dict[str, Any]:
    data = asdict(self)
    data["category"] = self.category.value
    return data
  
  @classmethod
  def from_dict(cls, data: Mapping[str, Any]) -> "Expense":
    if "amount" not in data:
      raise FinanceError("Missing required field: 'amount'")
    if "category" not in data:
      raise FinanceError("Missing required field: 'category'")

    amount = data["amount"]
    category_raw = data["category"]
    description = data.get("description")  # optional

    if isinstance(category_raw, ExpenseCategory):
      category = category_raw
    elif isinstance(category_raw, str):
      try:
        category = ExpenseCategory(category_raw.lower())
      except ValueError:
        valid = ", ".join(c.value for c in ExpenseCategory)
        raise InvalidCategoryError(
          f"Invalid category: {category_raw}. "
          f"Category must be one of: {valid}"
          )
    else:
      raise InvalidCategoryError(
        "category must be a string or an ExpenseCategory object."
      )

    return cls(
      amount=float(amount),
      category=category,
      description=description,
    )



@dataclass(frozen=True)
class Income:
  """Monthly income of the user."""
  source: str
  amount: float

  def __post_init__(self) -> None:
    if not isinstance(self.amount, (int, float)):
      raise FinanceError("Income amount must be int or float.")
    if self.amount < 0:
      raise FinanceError("Income amount cannot be negative.")

  def to_dict(self) -> dict[str, Any]:
    return asdict(self)

@dataclass
class MonthlyReport:
  """A report of income expenses net cash and trading budget """
  income: float
  total_expenses: float
  net_cash: float
  recommended_saving: float
  trading_budget: float


  def to_dict(self) -> dict[str, Any]:
    return asdict(self)


@dataclass
class Budget:
  """Spending limits and savings target derived from income."""
  total_income: float
  category_limit: Mapping[ExpenseCategory, float]
  savings_target: float =0.0