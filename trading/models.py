import pandas as pd
import pandas_ta as ta
from market import CandleData, Transaction
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Tuple
from pathlib import Path


# Compute project root
BASE_DIR = Path(__file__).resolve().parents[1]   # this gives: MyProfit/

# Define full path to trade history file
HISTORY_PATH = BASE_DIR / "storage" / "trade_history.json"

# Ensure storage/ exists
os.makedirs(BASE_DIR / "storage", exist_ok=True)

# Ensure file exists
if not HISTORY_PATH.exists():
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)


@dataclass
class EMACrossoverStrategy:
    """
    EMA crossover strategy using EMA5 and EMA8
    """
    candle_data: CandleData
    df: pd.DataFrame = field(default_factory=pd.DataFrame)

    def fetch_data(self, symbol: str, interval: str = "1m",
                   lookback: str = "10 minutes ago UTC") -> pd.DataFrame:
        """Fetch historical candle data."""
        self.df = self.candle_data.get_candles(symbol, interval=interval, start_str=lookback)
        return self.df

    def calc_ema(self, length: int, column: str = "close") -> None:
        """Calculate EMA and store it in the dataframe."""
        ema_col = f"EMA{length}"

        if ema_col not in self.df.columns:
            self.df[ema_col] = ta.ema(self.df[column], length=length)

    def cross58_signal(self) -> tuple[bool, bool]:
        """
        Returns (buy_signal, sell_signal):
        buy_signal = EMA5 crosses above EMA8
        sell_signal = EMA5 crosses below EMA8
        """
        if len(self.df) < 2:
            return False, False

        self.calc_ema(5)
        self.calc_ema(8)

        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]

        buy = last.EMA5 > last.EMA8 and prev.EMA5 < prev.EMA8
        sell = last.EMA5 < last.EMA8 and prev.EMA5 > prev.EMA8

        return buy, sell

    def live_ema(self, symbol: str, interval: str = "1m",
                 poll_interval: int = 15) -> None:
        """print signals continuously"""
        import time

        print(f"Started live EMA crossover for {symbol} ({interval})")

        while True:
            try:
                self.df = self.candle_data.get_candles(
                    symbol, interval=interval, start_str="30 minutes ago UTC"
                )

                buy, sell = self.cross58_signal()

                if buy:
                    print("BUY signal detected")
                elif sell:
                    print("SELL signal detected")

                time.sleep(poll_interval)

            except KeyboardInterrupt:
                print("Stopped by user.")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(poll_interval)


@dataclass
class Trade:
    """
    Executes trades based on boolean signals,
    blocks new trades if one is already open,
    logs everything to trade_history.json
    and automatically closes position if Binance shows no open orders.
    """
    transaction: Transaction
    symbol: str
    quantity: float
    entry_price: float | None = None
    take_profit: float | None = None
    stop_loss: float | None = None

    history_file: str = "storage/trade_history.json"
    last_signal: Tuple[bool, bool] = field(default_factory=lambda: (False, False))

    in_position: bool = False
    open_side: str | None = None



    def process_signals(self, signals: Tuple[bool, bool]):
        buy_signal, sell_signal = signals

        if signals == self.last_signal:
            return None

        self.last_signal = signals

        if self.in_position:
            print("Trade blocked: already in a position.")
            return None

        if buy_signal and not sell_signal:
            return self._open_position("BUY")

        if sell_signal and not buy_signal:
            return self._open_position("SELL")

        return None



    def _open_position(self, side: str, take_profit=None, stop_loss=None, risk_reward_ratio=1):
        # EXECUTE BUY / SELL
        if side == "BUY":
            order = self.transaction.buy(symbol=self.symbol, quantity=self.quantity, take_profit=None, stop_loss=None)
        else:
            order = self.transaction.sell(symbol=self.symbol, quantity=self.quantity, take_profit=None, stop_loss=None)

        # Extract executed entry price
        executed = float(order["fills"][0]["price"])

        # Save entry
        self.entry_price = executed

        # Compute SL/TP if not provided
        if take_profit is None or stop_loss is None:
            # BUY position
            if side == "BUY":
                self.stop_loss = executed * 0.99
                self.take_profit = executed * (1 + (1 - 0.99) * risk_reward_ratio)
            # SELL position
            else:
                self.stop_loss = executed * 1.01
                self.take_profit = executed * (1 - (1.01 - 1) * risk_reward_ratio)

        else:
            self.take_profit = take_profit
            self.stop_loss = stop_loss

        print(f"[POSITION OPEN] {side} @ {executed}, TP={self.take_profit}, SL={self.stop_loss}")

        self.in_position = True
        self.open_side = side
        self._log_trade(f"OPEN_{side}", order)

        return order

    def _close_market(self, side):
        try:
            order = (
                self.transaction.sell(self.symbol, self.quantity) if side == "SELL"
                else self.transaction.buy(self.symbol, self.quantity)
            )
        except Exception as e:
            print(f"ERROR closing position via {side}: {e}")
            return

        print(f"CLOSED via {side}: {order}")
        self._log_trade(f"AUTO_CLOSE_{side}", order)

        # Reset
        self.in_position = False
        self.open_side = None
        self.entry_price = None
        self.take_profit = None
        self.stop_loss = None

    #Trading log
    def _log_trade(self, event_type: str, order: dict):
        """Append executed trade info to trade_history.json"""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "symbol": self.symbol,
            "quantity": self.quantity,
            "order": order,
            "in_position_after": self.in_position
        }

        if os.path.exists(self.history_file):
            with open(self.history_file, "r") as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        else:
            history = []

        history.append(log_entry)

        with open(self.history_file, "w") as f:
            json.dump(history, f, indent=4)

        print(f"Logged: {event_type}")



    def check_tp_sl(self):
        if not self.in_position:
            return

        try:
            ticker = self.transaction.client.get_symbol_ticker(symbol=self.symbol)
            current_price = float(ticker["price"])
        except Exception as e:
            print(f"Error fetching price: {e}")
            return

        print(f"Current price: {current_price}")

        if self.open_side == "BUY":
            if current_price >= self.take_profit:
                print("TAKE PROFIT HIT")
                self._close_market("SELL")
            elif current_price <= self.stop_loss:
                print("STOP LOSS HIT")
                self._close_market("SELL")

        elif self.open_side == "SELL":
            if current_price <= self.take_profit:
                print("TAKE PROFIT HIT")
                self._close_market("BUY")
            elif current_price >= self.stop_loss:
                print("STOP LOSS HIT")
                self._close_market("BUY")
