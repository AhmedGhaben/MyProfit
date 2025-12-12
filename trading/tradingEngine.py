from __future__ import annotations

import time
from typing import Optional

from market import CandleData, Transaction
from trading import EMACrossoverStrategy, Trade
from . import binance_credentials


API_KEY = binance_credentials.API_KEY
API_SECRET = binance_credentials.API_SECRET


# Poll interval (seconds)
POLL_INTERVAL = 15

# Global switch (do not auto-run on import)
RUN_BOT = False


def set_run_bot(value: bool) -> None:
    """Enable/disable the trading loop."""
    global RUN_BOT
    RUN_BOT = value


def build_default_components(
    symbol: str = "BTCUSDT",
    quantity: float = 0.001,
    testnet: bool = True,
) -> tuple[Trade, EMACrossoverStrategy, str]:
    """Create default CandleData/Transaction/Strategy/Trade objects."""
    candle_data = CandleData(api_key=API_KEY, api_secret=API_SECRET, testnet=testnet)
    transaction = Transaction(api_key=API_KEY, api_secret=API_SECRET, testnet=testnet)

    strategy = EMACrossoverStrategy(candle_data=candle_data)
    trade = Trade(transaction=transaction, symbol=symbol, quantity=quantity)
    return trade, strategy, symbol


def run_trading_loop(
    trade: Optional[Trade] = None,
    strategy: Optional[EMACrossoverStrategy] = None,
    symbol: str = "BTCUSDT",
    poll_interval: int = POLL_INTERVAL,
) -> None:
    """
    Run the trading loop while RUN_BOT is True.

    IMPORTANT:
    - This function is intentionally not called automatically on import.
    - Call it explicitly (or run this module as a script).
    """
    global RUN_BOT

    if trade is None or strategy is None:
        trade, strategy, symbol = build_default_components(symbol=symbol)

    print(f"Trading loop ready for {symbol}.")
    print("Set RUN_BOT=True (or call set_run_bot(True)) to start.\n")

    while RUN_BOT:
        try:
            trade.check_tp_sl()

            strategy.fetch_data(symbol, interval="1m", lookback="20 minutes ago UTC")
            signals = strategy.cross58_signal()
            trade.process_signals(signals)

            time.sleep(poll_interval)

        except KeyboardInterrupt:
            print("\nBot stopped manually (KeyboardInterrupt).")
            RUN_BOT = False

        except Exception as e:
            print(f"Error in bot loop: {e}")
            time.sleep(poll_interval)

    print("Bot stopped.")


if __name__ == "__main__":
    # If you run `python -m trading.tradingEngine` (or python tradingEngine.py),
    # trading will start here and not during import.
    set_run_bot(True)
    trade_obj, strat_obj, sym = build_default_components()
    run_trading_loop(trade=trade_obj, strategy=strat_obj, symbol=sym, poll_interval=POLL_INTERVAL)
