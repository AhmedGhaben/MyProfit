from dataclasses import dataclass, asdict
from __future__ import annotations
from enum import Enum
from typing import Any, Mapping


class FinanceError(ValueError):
  #Base error
  pass

class NegativeAmountError:
  #Amount mmust be non negative
  pass

class InvalidAmountError(FinanceError):
  #invaid money amount type 
  pass

class InvalidCatagoryError(FinanceError):
  #might not need it if we make the catagory buttons
  pass

class ExpenseCategory(Enum):
  #catagories for personal expenses
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
  -catagory:object (probably buttons in the telegram bot)
  -description optional
  """
  amount: float
  catagory: ExpenseCategory
  description:str | None=None

  def __post_init__(self):
    if not isinstance(self.amount, (int, float)):
      raise InvalidAmountError("Expence amount must be int or float. ")
    if self.amount < 0: 
      raise NegativeAmountError("Expence amount cannot be positive. ")
  
  def to_dict(self) -> dict[str, Any]:
    data = asdict(self)
    data["catagory"] = self.catagory.value
    return data
  
  @classmethod
  def from_dict(cls, data:Mapping[str, Any]) -> "Expense":
    if "amount" not in data:
      raise FinanceError("Missing required field: 'Amount'")
    if "catagory" not in data:
      raise FinanceError("Missing required field: 'Catagory'")
    amount = data["amount"]
    catagory_raw = data["catagory"]
    description = data.get('discription') # not required

    if isinstance(catagory_raw, ExpenseCategory):
      catagory = catagory_raw
    elif isinstance(catagory_raw, str):
      try:
        catagort = ExpenseCategory(catagory_raw.lower())
      except ValueError:
        valid = ", ".join(c.value for c in ExpenseCategory)
        raise InvalidCatagoryError(f"Invalid catagory: {catagory_raw}\nCatagory must be one of: {valid}")
    else: 
      raise InvalidCatagoryError("Catagory must be a string or a ExpenseCategory object. ")
    return cls(
      amount=float(amount),
      catagory=catagory,
      description=description,
      )



@dataclass(frozen=True)
class Income:
  source: str
  amount: float

  def __post_init__(self) -> None:
    if not isinstance(self.amount, (int, float)):
      raise FinanceError()#should be number
    if self.amount < 0: 
      raise FinanceError()#cannot be negative
    
  def to_dict(self) -> dict[str, Any]:
    return asdict(self)

@dataclass
class MonethlyReport:
  income:float
  total_expences:float
  net_cash:float
  recomended_saving:float
  trading_budget:float
  def to_dict(self) -> dict[str, Any]:
    return asdict(self)


@dataclass
class Budget:
  total_income= float
  catagory_limit: Mapping[ExpenseCategory, float]
  saving_target= float =0.0



DEFAULT_CATEGORY_PERCENTS: dict[ExpenseCategory, float] = {
    ExpenseCategory.HOUSING: 0.30,
    ExpenseCategory.FOOD: 0.15,
    ExpenseCategory.TRANSPORT: 0.05,
    ExpenseCategory.UTILITIES: 0.05,
    ExpenseCategory.ENTERTAINMENT: 0.10,
    ExpenseCategory.OTHER: 0.15,  
}

DEFAULT_SAVINGS_PERCENT: float = 0.20

def build_budget_from_income(total_income: float) -> Budget:
  """Create a Budget using a fixed percentage-based plan."""
  if total_income < 0:
    raise ValueError("total_income cannot be negative")

  category_limits = {
    category: total_income * pct
    for category, pct in DEFAULT_CATEGORY_PERCENTS.items()
  }

  savings_target = total_income * DEFAULT_SAVINGS_PERCENT

  return Budget(
    total_income=total_income,
    category_limits=category_limits,
    savings_target=savings_target,
  )


"""
def ramaining_for(self, catagory:ExpenseCategory, spent:float) -> float:
limit = self.catagory_limit.get(catagory, 0.0)
return max(limit - spent, 0.0)
"""