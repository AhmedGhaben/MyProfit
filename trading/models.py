import pandas as pd
import pandas_ta as ta
from market import CandleData

class EMACrossoverStrategy:
    """
    EMA crossover strategy: signals when EMA5 crosses EMA8
    Works with CandleData from Binance
    Generates separate boolean flags for signals
    """
    def __init__(self, candle_data: CandleData):
        self.candle_data = candle_data
        self.df = pd.DataFrame()

    def fetch_data(self, symbol, interval='1m', lookback='10 minutes ago UTC'):
        """Fetch historical candle data from Binance"""
        self.df = self.candle_data.get_candles(symbol, interval=interval, start_str=lookback)
        return self.df

    def calc_ema(self, length: int, column="close"):
        """Calculate EMA of given length"""
        ema_name = f"EMA{length}"
        self.df[ema_name] = ta.ema(self.df[column], length=length)
        return self.df

    def cross58_signal(self):
        """
        Check if EMA5 crossed EMA8 in the last candle
        Returns a tuple of booleans: (buy_signal, sell_signal)
        """
        buy_signal = False
        sell_signal = False

        if self.df.empty or len(self.df) < 2:
            return buy_signal, sell_signal

        self.calc_ema(5)
        self.calc_ema(8)

        last_candle = self.df.iloc[-1]
        prev_candle = self.df.iloc[-2]

        # EMA5 cross above EMA8 (Buy)
        if last_candle["EMA5"] > last_candle["EMA8"] and prev_candle["EMA5"] < prev_candle["EMA8"]:
            buy_signal = True

        # EMA5 cross below EMA8 (Sell)
        elif last_candle["EMA5"] < last_candle["EMA8"] and prev_candle["EMA5"] > prev_candle["EMA8"]:
            sell_signal = True

        return buy_signal, sell_signal

    def run_live_ema(self, symbol, interval='1m', poll_interval=15):
        """
        Continuously fetch latest candles and generate boolean signals
        """
        import time
        print(f"Starting live EMA crossover signal generator for {symbol} ({interval})...")

        while True:
            try:
                self.df = self.candle_data.get_candles(symbol, interval=interval, start_str='5 minutes ago UTC')
                buy_signal, sell_signal = self.cross58_signal()

                if buy_signal:
                    print("BUY signal detected")
                if sell_signal:
                    print("SELL signal detected")

                time.sleep(poll_interval)

            except KeyboardInterrupt:
                print("Live signal generator stopped by user.")
                break
            except Exception as e:
                print(f"Error fetching live candles: {e}")
                time.sleep(poll_interval)
