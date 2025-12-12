from __future__ import annotations

"""
Telegram UI for MyProfit.

Features:
- /set_income          : set monthly income
- /add_expense         : add expenses
- /report              : monthly report with saving target + trading budget
- /set_trading_budget  : user-controlled trading budget
- /expenses_detail     : detailed expenses report
- /trading             : show trading status and toggle start/stop (UI state only)
- JSON persistence for income, expenses, custom trading budget, trading state
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from finance import (
    FinancialEngine,
    Income,
    Expense,
    ExpenseCategory,
    FinanceError,
)

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Persistence (JSON file)
# -----------------------------------------------------------------------------
DATA_FILE = Path(__file__).resolve().parents[1] / "storage" / "user_finances.json"
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# In-memory mapping: telegram_user_id -> FinancialEngine
user_engines: Dict[int, FinancialEngine] = {}

# Per-user trading state (True = trading ON, False = OFF)
user_trading_state: Dict[int, bool] = {}

# Conversation states
(
    SET_INCOME_AMOUNT,
    ADD_EXPENSE_CATEGORY,
    ADD_EXPENSE_AMOUNT,
    ADD_EXPENSE_DESCRIPTION,
    SET_TRADING_BUDGET_AMOUNT,
) = range(5)


def save_engine_for_user(user_id: int, engine: FinancialEngine) -> None:
    """Persist income, expenses, custom trading budget and trading state for one user."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Failed to decode JSON from %s, resetting file", DATA_FILE)
            data = {}
    else:
        data = {}

    income_payload = {
        "source": getattr(engine.income, "source", "income"),
        "amount": float(getattr(engine.income, "amount", 0.0)),
    }

    expenses_payload = []
    for e in engine.expenses:
        try:
            expenses_payload.append(
                {
                    "amount": float(e.amount),
                    "category": e.category.name,  # enum name, e.g. "FOOD"
                    "description": e.description,
                }
            )
        except Exception as exc:
            logger.warning(
                "Failed to serialise expense %r for user %s: %s",
                e,
                user_id,
                exc,
            )

    custom_trading_budget = getattr(engine, "custom_trading_budget", None)
    trading_enabled = user_trading_state.get(user_id, False)

    data[str(user_id)] = {
        "income": income_payload,
        "expenses": expenses_payload,
        "custom_trading_budget": custom_trading_budget,
        "trading_enabled": trading_enabled,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    logger.info("Saved finance data for user %s to %s", user_id, DATA_FILE)


def load_engines_from_file() -> None:
    """Restore all FinancialEngine instances and trading state from JSON on startup."""
    global user_engines, user_trading_state

    if not DATA_FILE.exists():
        logger.info("No existing data file found at %s", DATA_FILE)
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.warning("Failed to decode JSON from %s, ignoring file", DATA_FILE)
        return

    restored_count = 0
    for user_id_str, payload in data.items():
        try:
            user_id = int(user_id_str)
        except ValueError:
            continue

        income_payload = payload.get("income")
        if income_payload is None:
            continue

        try:
            if isinstance(income_payload, dict):
                income = Income(
                    source=income_payload.get("source", "income"),
                    amount=float(income_payload.get("amount", 0.0)),
                )
            else:
                income = Income(source="salary", amount=float(income_payload))
        except Exception as exc:
            logger.warning("Failed to restore income for user %s: %s", user_id, exc)
            continue

        engine = FinancialEngine(income=income)

        expenses_payload = payload.get("expenses", [])
        for e_data in expenses_payload:
            try:
                amount = float(e_data.get("amount", 0.0))
                cat_key = e_data.get("category")
                if cat_key is None:
                    continue
                category = ExpenseCategory[cat_key]
                description = e_data.get("description")
                expense = Expense(amount=amount, category=category, description=description)
                engine.expenses.append(expense)
            except Exception as exc:
                logger.warning(
                    "Failed to restore one expense for user %s: %s",
                    user_id,
                    exc,
                )

        custom_tb = payload.get("custom_trading_budget")
        if isinstance(custom_tb, (int, float)):
            try:
                engine.custom_trading_budget = float(custom_tb)
            except Exception:
                pass

        trading_enabled = bool(payload.get("trading_enabled", False))
        user_trading_state[user_id] = trading_enabled

        user_engines[user_id] = engine
        restored_count += 1

    logger.info("Restored %d user(s) from %s", restored_count, DATA_FILE)


load_engines_from_file()


def get_engine_for_user(user_id: int) -> FinancialEngine | None:
    return user_engines.get(user_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    text = (
        f"Hi {user.first_name or ''}\n\n"
        "I'm your MyProfit assistant.\n\n"
        "Main commands:\n"
        "• /set_income – set your monthly income\n"
        "• /add_expense – add an expense\n"
        "• /report – show monthly finance report\n"
        "• /expenses_detail – detailed expenses report\n"
        "• /set_trading_budget – choose your trading budget\n"
        "• /trading – start/stop trading (UI flag)\n"
        "• /help – show all commands\n"
    )
    await update.message.reply_text(text)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "Available commands:\n"
        "• /set_income – set or update your monthly income\n"
        "• /add_expense – add an expense (amount + category + description)\n"
        "• /report – see monthly report and trading budget\n"
        "• /expenses_detail – detailed expenses by category\n"
        "• /set_trading_budget – set or reset your trading budget\n"
        "• /trading – show trading status and toggle start/stop (UI flag)\n"
        "• /cancel – cancel current operation\n"
    )
    await update.message.reply_text(text)


async def set_income(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Great, let's set your monthly income.\n"
        "Please send me your monthly income as a number (for example: 2500)."
    )
    return SET_INCOME_AMOUNT


async def set_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    text = update.message.text.strip()

    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError("Income must be positive.")
    except ValueError:
        await update.message.reply_text(
            "Please send a valid positive number for your income "
            "(for example: 3000). Try again or /cancel."
        )
        return SET_INCOME_AMOUNT

    income = Income(source="salary", amount=amount)
    engine = FinancialEngine(income=income)
    user_engines[user_id] = engine

    save_engine_for_user(user_id, engine)

    await update.message.reply_text(
        f"Income set to {amount:.2f}.\n"
        "You can now:\n"
        "• /add_expense to record your spending\n"
        "• /report to see your monthly report."
    )
    return ConversationHandler.END


async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    engine = get_engine_for_user(user_id)
    if engine is None:
        await update.message.reply_text(
            "I don't have your income yet.\n\n"
            "Use /set_income to tell me your monthly income first."
        )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton(cat.name.title(), callback_data=f"exp_cat:{cat.name}")]
        for cat in ExpenseCategory
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Choose an expense category:", reply_markup=reply_markup)
    return ADD_EXPENSE_CATEGORY


async def select_expense_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = query.data
    try:
        _, cat_name = data.split(":", maxsplit=1)
        category = ExpenseCategory[cat_name]
    except (ValueError, KeyError):
        await query.edit_message_text("Unknown category. Please run /add_expense again.")
        return ConversationHandler.END

    context.user_data["expense_category"] = category

    await query.edit_message_text(
        f"Category: {category.name.title()}\n\n"
        "Now send me the expense amount (for example: 15.9)."
    )
    return ADD_EXPENSE_AMOUNT


async def set_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "Please send a valid non-negative number for the amount, or /cancel to stop."
        )
        return ADD_EXPENSE_AMOUNT

    context.user_data["expense_amount"] = amount

    await update.message.reply_text(
        "Got it. Optionally send a short description (e.g. 'groceries', 'rent').\n"
        "If you don't want a description, you can just send '-' ."
    )
    return ADD_EXPENSE_DESCRIPTION


async def set_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    engine = get_engine_for_user(user_id)
    if engine is None:
        await update.message.reply_text(
            "I lost your finance session. Please set income again with /set_income."
        )
        return ConversationHandler.END

    category: ExpenseCategory = context.user_data.get("expense_category")
    amount: float = context.user_data.get("expense_amount")
    description_raw = update.message.text.strip()
    description = None if description_raw == "-" else (description_raw or None)

    if category is None or amount is None:
        await update.message.reply_text(
            "Something went wrong with the expense data. Please try /add_expense again."
        )
        return ConversationHandler.END

    try:
        expense = Expense(amount=amount, category=category, description=description)
        engine.add_expense(expense)
        save_engine_for_user(user_id, engine)
    except FinanceError as e:
        logger.exception("Failed to add expense for user %s", user_id)
        await update.message.reply_text(f"Something went wrong when saving the expense: {e}")
        return ConversationHandler.END

    await update.message.reply_text(f"Added expense: {amount:.2f} in {category.value}.")

    context.user_data.pop("expense_category", None)
    context.user_data.pop("expense_amount", None)

    return ConversationHandler.END


async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    engine = get_engine_for_user(user_id)
    if engine is None:
        await update.message.reply_text(
            "I don't have your income yet.\n\nUse /set_income to tell me your monthly income first."
        )
        return

    report = engine.generate_monthly_report()
    income_obj = report.income
    income_amount = getattr(income_obj, "amount", income_obj)

    custom_tb = getattr(engine, "custom_trading_budget", None)
    trading_enabled = user_trading_state.get(user_id, False)

    text = (
        "Monthly Financial Report\n\n"
        f"Income: {income_amount:.2f}\n"
        f"Total expenses: {report.total_expenses:.2f}\n"
        f"Net cash: {report.net_cash:.2f}\n"
        f"Recommended saving (target): {report.recommended_saving:.2f}\n"
        f"Trading budget in use: {report.trading_budget:.2f}\n"
        f"Trading status: {'ON' if trading_enabled else 'OFF'}\n"
    )

    if custom_tb is not None:
        text += f"\nYou set a custom trading budget of {custom_tb:.2f}."
    else:
        text += (
            "\nTrading budget is currently calculated automatically "
            "from your savings target and net cash."
        )

    await update.message.reply_text(text)


async def expenses_detail_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    engine = get_engine_for_user(user_id)
    if engine is None:
        await update.message.reply_text(
            "I don't have your income yet.\n\nUse /set_income to tell me your monthly income first."
        )
        return

    if not engine.expenses:
        await update.message.reply_text("You don't have any recorded expenses yet.")
        return

    cat_totals = engine.expenses_per_category()

    lines = ["Detailed expenses by category:\n"]
    for cat, total in cat_totals.items():
        lines.append(f"{cat.value.capitalize()}: {total:.2f}")
        for e in engine.expenses:
            if e.category == cat:
                desc = f" – {e.description}" if e.description else ""
                lines.append(f"  • {e.amount:.2f}{desc}")
        lines.append("")

    await update.message.reply_text("\n".join(lines))


async def set_trading_budget_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    engine = get_engine_for_user(user_id)
    if engine is None:
        await update.message.reply_text(
            "I don't have your income yet.\n\nUse /set_income to tell me your monthly income first."
        )
        return ConversationHandler.END

    income_amount = engine.income.amount
    recommended_target = engine.budget.savings_target
    auto_budget = engine.trading_budget()

    text = (
        f"For your income of {income_amount:.2f}, the recommended savings target "
        f"(max trading budget) is {recommended_target:.2f}.\n"
        f"Given your current expenses, the automatic trading budget is {auto_budget:.2f}.\n\n"
        "Send the trading budget you want to use (number).\n"
        "Send 0 to reset to automatic calculation."
    )
    await update.message.reply_text(text)
    return SET_TRADING_BUDGET_AMOUNT


async def set_trading_budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    engine = get_engine_for_user(user_id)
    if engine is None:
        await update.message.reply_text(
            "I don't have your income yet.\n\nUse /set_income to tell me your monthly income first."
        )
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Please send a valid non-negative number, or 0 to reset.")
        return SET_TRADING_BUDGET_AMOUNT

    if amount == 0:
        engine.set_trading_budget(None)
        save_engine_for_user(user_id, engine)
        auto_budget = engine.trading_budget()
        await update.message.reply_text(
            f"Trading budget reset to automatic.\nCurrent automatic trading budget is {auto_budget:.2f}."
        )
        return ConversationHandler.END

    net_cash = max(engine.income.amount - engine.total_expenses(), 0.0)
    if amount > net_cash:
        await update.message.reply_text(
            f"You only have {net_cash:.2f} of net cash available.\n"
            "Choose a trading budget <= that amount, or send 0 to reset."
        )
        return SET_TRADING_BUDGET_AMOUNT

    engine.set_trading_budget(amount)
    save_engine_for_user(user_id, engine)
    await update.message.reply_text(f"Trading budget set to {amount:.2f}.")
    return ConversationHandler.END


async def trading_status_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current trading status and a button to start/stop (UI flag only)."""
    user_id = update.effective_user.id
    engine = get_engine_for_user(user_id)
    if engine is None:
        await update.message.reply_text(
            "I don't have your income yet.\n\nUse /set_income to tell me your monthly income first."
        )
        return

    current = user_trading_state.get(user_id, False)
    label = "Stop trading" if current else "Start trading"
    state_text = "Trading is currently ON." if current else "Trading is currently OFF."

    keyboard = [[InlineKeyboardButton(label, callback_data="toggle_trading")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"{state_text}\n\nUse the button below to toggle trading.",
        reply_markup=reply_markup,
    )


async def toggle_trading_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Toggle trading state via inline button (UI flag only)."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    engine = get_engine_for_user(user_id)
    if engine is None:
        await query.edit_message_text(
            "I don't have your income yet.\n\nUse /set_income to tell me your monthly income first."
        )
        return

    current = user_trading_state.get(user_id, False)
    new_state = not current
    user_trading_state[user_id] = new_state

    save_engine_for_user(user_id, engine)

    label = "Stop trading" if new_state else "Start trading"
    state_text = "Trading is now ON ✅" if new_state else "Trading is now OFF ⛔"

    keyboard = [[InlineKeyboardButton(label, callback_data="toggle_trading")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{state_text}\n\nUse the button below to toggle again.",
        reply_markup=reply_markup,
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END


def build_application(token: str | None = None) -> Application:
    if token is None:
        token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "Telegram bot token is not set. "
            "Pass it explicitly to build_application() or set TELEGRAM_BOT_TOKEN env var."
        )

    app = ApplicationBuilder().token(token).build()

    set_income_conv = ConversationHandler(
        entry_points=[CommandHandler("set_income", set_income)],
        states={
            SET_INCOME_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_income_amount)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    add_expense_conv = ConversationHandler(
        entry_points=[CommandHandler("add_expense", add_expense)],
        states={
            ADD_EXPENSE_CATEGORY: [
                CallbackQueryHandler(select_expense_category, pattern=r"^exp_cat:")
            ],
            ADD_EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_expense_amount)
            ],
            ADD_EXPENSE_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_expense_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    set_trading_budget_conv = ConversationHandler(
        entry_points=[CommandHandler("set_trading_budget", set_trading_budget_start)],
        states={
            SET_TRADING_BUDGET_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_trading_budget_amount)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(set_income_conv)
    app.add_handler(add_expense_conv)
    app.add_handler(set_trading_budget_conv)
    app.add_handler(CommandHandler("report", report_command))
    app.add_handler(CommandHandler("expenses_detail", expenses_detail_command))
    app.add_handler(CommandHandler("trading", trading_status_menu))
    app.add_handler(CallbackQueryHandler(toggle_trading_button, pattern=r"^toggle_trading$"))
    app.add_handler(CommandHandler("cancel", cancel))

    return app


def run_bot(token: str | None = None) -> None:
    application = build_application(token)
    logger.info("Starting MyProfit Telegram bot...")
    application.run_polling()
