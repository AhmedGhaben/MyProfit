from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterable, Dict
from .models import (
  Expense,
  MonthlyReport,
  ExpenseCategory,
  Budget,
  Income
)

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


@dataclass
class FinancialEngine:

  """
  hold the main operations:
  -builds budget if not given
  -track expenses.
  -updates remaining money
  -generates the Monthly  report
  """
  income:Income
  budget:Budget| None=None
  expenses: list[Expense] = field(default_factory=list)

#build the post init for creating budget
  def __post_init__(self) -> None:
    if self.budget==None:
      self.budget = build_budget_from_income(self.income.amount)

#methods to add an expense or muiltiple expenses
  def add_expense(self, expense:Expense) -> None:
    self.expenses.append(expense)

  def add_multiple_expenses(self, expenses: Iterable[Expense]) -> None:
    for e in expenses:
      self.expenses.append(e)

#method to calculate total expences and one for expenses per catagory
  def total_expenses(self) -> float:
    return sum(e.amount for e in self.expenses)

  def expenses_per_catagory(self) -> dict:
    catagory_expenses: Dict[ExpenseCategory, float]={}
    for e in self.expenses:
      catagory_expenses[e.catagory]= catagory_expenses.get(e.catagory, 0.0) + e.amount
    return catagory_expenses

#compute trading budget for the recommended and net cash
  def trading_budget(self) -> float:
    net_cash = max(self.income.amount-self.total_expenses(), 0.0)
    return min(net_cash, self.budget.savings_target)

#generate the monthly report 
  def generate_monthly_report(self) -> MonthlyReport:
    total_expenses=self.total_expenses()
    recomended_saving=self.trading_budget()
    net_cash=self.income.amount-total_expenses
    trading_budget=self.trading_budget()
    return MonthlyReport(
      income=self.income,
      total_expenses=total_expenses,
      net_cash=net_cash,
      recommended_saving=recomended_saving,
      trading_budget=trading_budget
    )


#check if the current spending follows the finance stratagy (to be used each time the user updates spending)
# (if not then the issue will be said in the other function)
#monthly report (spending report)
#monthly report (investing report)
#saving goal with rate of saving and expected time remaining
#set investing budget 

