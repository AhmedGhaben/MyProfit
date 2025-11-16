# MyProfit

Oscar Prada and Ahmed Ghaben 

MyProfit is a personal finance and automated trading system.  
It integrates financial analysis, market data, trading strategies, and risk management to help users manage budgets and trade assets on platforms like OANDA or Binance.

## Iteration 1 — Core System

### 1. Financial Engine
Handles all personal finance logic.  
Features include:
- Analysis of salary, expenses, and budgets  
- Monthly financial reports  
- Savings recommendations  
- Budget suggestions used by the trading engine  

### 2. Market Data
Fetches market information from broker APIs (OANDA, Binance):
- Real-time and historical asset prices
- Candlestick data
- Market spreads and volatility

Data is normalized for use by the trading engine.

### 3. Account State
Fetches the current state of the trading account:
- Open positions  
- Account balance 
- Realized and unrealized profits/losses  
- Risk exposure  

### 4. Trading Engine
- Receives market data and account state  
- Applies trading strategies  
- Executes trades via broker API 
- Enforces risk management rules

---

## Iteration 2 — UI and other features

### 5. Trading Strategies
A module for developing strategies for the trading engine:
- Moving averages
- Breakout strategies
- Risk-based rules

### 6. Trade History
Stores all executed trades and provides analytics:
- Win/loss statistics
- Risk-to-reward ratios

---

### User Interface Layer

The UI provides user access to MyProfit's features.  


### 7. UI: Finances
Shows insights from the financial engine:
- Salary and expense breakdowns
- Monthly savings reports
- Suggested trading budget
- Allows users to adjust budgets and inputs

### 8. UI: Trading Settings
Control panel for trading:
- Select and configure trading strategies
- Adjust risk parameters
- View account state and PnL
- Start or stop the trading engine

### 9. UI: Trade History
Displays historical trades and analytics:
- Trade entries and exits
- Profits and losses
- Strategy evaluation and performance metrics