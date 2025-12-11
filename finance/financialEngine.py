from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Dict

from .models import (
    Expense,
    MonthlyReport,
    ExpenseCategory,
    Budget,
    Income,
)

# ---------------------------------------------------------------------------
# Default configuration for budget building
# ---------------------------------------------------------------------------

# Default percent per category, relative to total income
DEFAULT_CATEGORY_PERCENTS: dict[ExpenseCategory, float] = {
    ExpenseCategory.HOUSING: 0.30,
    ExpenseCategory.FOOD: 0.15,
    ExpenseCategory.TRANSPORT: 0.05,
    ExpenseCategory.UTILITIES: 0.05,
    ExpenseCategory.ENTERTAINMENT: 0.10,
    ExpenseCategory.OTHER: 0.15,
}

# Default savings target: 20% of income
DEFAULT_SAVINGS_PERCENT: float = 0.20


def build_budget_from_income(total_income: float) -> Budget:
    """Create a Budget using a fixed percentage-based plan."""
    if total_income < 0:
        raise ValueError("total_income cannot be negative")

    category_limit = {
        category: total_income * pct
        for category, pct in DEFAULT_CATEGORY_PERCENTS.items()
    }

    savings_target = total_income * DEFAULT_SAVINGS_PERCENT

    return Budget(
        total_income=total_income,
        category_limit=category_limit,
        savings_target=savings_target,
    )


# ---------------------------------------------------------------------------
# FinancialEngine
# ---------------------------------------------------------------------------

@dataclass
class FinancialEngine:
    """
    Main finance engine:
    - builds a budget if not given
    - tracks expenses
    - computes trading budget
    - generates monthly report
    """

    income: Income
    budget: Budget | None = None
    expenses: list[Expense] = field(default_factory=list)
    # Optional override chosen by user; if None, use automatic trading_budget logic
    custom_trading_budget: float | None = None

    def __post_init__(self) -> None:
        # if no budget provided, build a default one based on income
        if self.budget is None:
            self.budget = build_budget_from_income(self.income.amount)

    # ---------------------- Expense management ------------------------------

    def add_expense(self, expense: Expense) -> None:
        """Add a single expense to the list."""
        self.expenses.append(expense)

    def add_multiple_expenses(self, expenses: Iterable[Expense]) -> None:
        """Convenience helper to add several expenses."""
        for e in expenses:
            self.expenses.append(e)

    # ---------------------- Aggregations -----------------------------------

    def total_expenses(self) -> float:
        """Return the sum of all expenses."""
        return sum(e.amount for e in self.expenses)

    def expenses_per_category(self) -> dict[ExpenseCategory, float]:
        """
        Aggregate expenses per category.

        (The field in Expense is called 'category' in your models,
        so we keep that spelling here.)
        """
        category_expenses: Dict[ExpenseCategory, float] = {}
        for e in self.expenses:
            category_expenses[e.category] = category_expenses.get(e.category, 0.0) + e.amount
        return category_expenses

    # ---------------------- Trading budget logic ---------------------------

    def set_trading_budget(self, amount: float | None) -> None:
        """
        Set a custom trading budget (absolute amount).

        - amount < 0  → error
        - amount is None  → reset to automatic calculation
        - amount > net_cash → error (cannot trade more than what you have)
        """
        if amount is None:
            self.custom_trading_budget = None
            return

        if amount < 0:
            raise ValueError("Trading budget must be non-negative.")

        net_cash = max(self.income.amount - self.total_expenses(), 0.0)
        if amount > net_cash:
            raise ValueError("Trading budget cannot exceed available net cash.")

        self.custom_trading_budget = amount

    def trading_budget(self) -> float:
        """
        Effective trading budget to use.

        - Recommended max is savings_target (e.g. 20% of income),
          additionally limited by current net cash.
        - If user set a custom_trading_budget, use it but never exceed net cash.
        """
        total_expenses = self.total_expenses()
        net_cash = max(self.income.amount - total_expenses, 0.0)
        recommended = min(net_cash, self.budget.savings_target)

        # If user configured a custom trading budget, respect it but
        # still do not allow more than net_cash.
        if self.custom_trading_budget is not None:
            return min(self.custom_trading_budget, net_cash)

        # Otherwise use the recommended automatic value
        return recommended

    # ---------------------- Reporting --------------------------------------

    def generate_monthly_report(self) -> MonthlyReport:
        """
        Build a MonthlyReport dataclass with:
        - total_expenses
        - net_cash
        - recommended_saving (savings_target from budget)
        - trading_budget (effective trading budget)
        """
        total_expenses = self.total_expenses()
        net_cash = max(self.income.amount - total_expenses, 0.0)
        recommended_saving = self.budget.savings_target
        trading_budget_value = self.trading_budget()

        return MonthlyReport(
            income=self.income,
            total_expenses=total_expenses,
            net_cash=net_cash,
            recommended_saving=recommended_saving,
            trading_budget=trading_budget_value,
        )
