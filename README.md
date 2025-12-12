# MyProfit

**Authors:**  
Oscar Prada, Ahmed Ghaben

---

## Project Overview

**MyProfit** is a modular personal finance assistant combined with an automated trading system, controlled through a Telegram bot interface.

The project allows users to:
- Track monthly income and categorized expenses
- Receive savings and trading budget recommendations
- Control and monitor an automated trading engine
- View summarized trade reports and execution history

The system is designed with a **clear separation of concerns** between the user interface, financial logic, and trading logic.

---

## Architecture

MyProfit/
├── finance/ # Income, expenses, budgeting logic
├── trading/ # Trading engine and strategies
├── market/ # Market data & transaction abstractions
├── ui/ # Telegram bot UI
├── storage/ # JSON persistence (finance + trades)
├── main.py # Telegram bot entry point
└── README.md


---

## Iteration 1 — Core System

### 1. Financial Engine (Ahmed)

The **Financial Engine** handles all personal finance logic.

**Features:**
- Analysis of salary, expenses, and budgets
- Monthly financial reporting
- Savings recommendations
- Trading budget suggestions used by the trading engine


### 2. Market Data Layer (Oscar)

The **Market Data** module is responsible for fetching and normalizing market information from broker APIs (OANDA, Binance).

**Responsibilities:**
- Real-time and historical price retrieval
- Candlestick data acquisition
- Market spread and volatility handling



### Note on Trading Execution

Trading execution features were postponed to **Iteration 2** due to delays in broker account approval.

---

## Iteration 2 — UI and Trading Features

### 3. Trading Engine (Oscar)

The **Trading Engine** executes automated trades based on strategy signals.

**Responsibilities:**
- Fetch market data
- Apply trading strategies
- Execute BUY/SELL orders via broker API
- Manage open positions and automatic closes
- Persist trade execution history

The trading engine is designed to run **independently** from the Telegram UI to avoid blocking behavior.

---

### 4. Trading Strategies (Oscar)

A dedicated module for implementing and testing trading strategies.

**Current strategies include:**
- Exponential Moving Average (EMA) crossover
- Rule-based signal generation
- Position locking to prevent overlapping trades

**Milestone (30 November):**  
Implemented and tested an EMA crossover strategy using real market data.

---

## User Interface Layer

### 5. Telegram Bot UI (Ahmed)

The Telegram bot serves as the main user interface for the system.

**Supported commands:**
- `/set_income` – set monthly income
- `/add_expense` – add expenses by category
- `/report` – financial summary
- `/expenses_detail` – detailed expense breakdown
- `/set_trading_budget` – override recommended trading budget
- `/trading` – toggle trading ON/OFF and request trade report

The UI interacts only with high-level APIs and does not execute trading logic directly.
---
### System Integration and Command Handling (Ahmed)

In this iteration, all Telegram bot commands and the overall orchestration of the system were implemented. This includes defining and handling all user commands, managing conversational flows, and coordinating interactions between the Telegram UI, the financial engine, and the trading engine. The integration ensures that user actions are correctly validated, persisted, and reflected across the system while maintaining a strict separation between the user interface and the underlying execution logic.

### 6. Trade Reporting (Ahmed)

The system provides summarized trade reports via the Telegram UI.

**Report features:**
- Total trade event count
- Event-type summary (OPEN / CLOSE)
- Clean table of recent trades
- Optional executed price over time visualization

---

## Persistence

All runtime data is stored using lightweight JSON persistence:

- `storage/user_finances.json` — user income, expenses, budgets, and trading state
- `storage/trade_history.json` — executed trade history

User data is restored automatically on application restart.

---

## How to Run

1. Create and activate a virtual environment  
2. Install project dependencies  
3. Set `TELEGRAM_BOT_TOKEN` as an environment variable  

### Run the Telegram bot (from project root):

python main.py
run the trading bot in a seperate terminal 
python -m trading.tradingEngine
