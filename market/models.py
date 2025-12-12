from dataclasses import dataclass, field
import pandas as pd
from binance.client import Client
import time


@dataclass
class CandleData:
    """
    Handles price-fetching (including live price streaming)
    """
    api_key: str | None = None
    api_secret: str | None = None
    testnet: bool = True
    api_url: str = "https://testnet.binance.vision/api"

    client: Client = field(init=False)

    def __post_init__(self):
        """Initialize Binance client after dataclass construction."""
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        self.client.API_URL = self.api_url
        self.client.get_account()

    def get_candles(self, symbol, interval='1m', start_str='2 hours ago UTC', end_str=None):
        """Fetch price data as candles."""
        klines = self.client.get_historical_klines(symbol, interval, start_str, end_str)

        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])

        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        return df[["timestamp", "open", "high", "low", "close", "volume"]]

    def get_latest_price(self, symbol):
        """Fetch the latest price."""
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def stream_candles(self, symbol, interval='1m', poll_interval=10):
        """Stream live candle data."""
        df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        print(f"Starting live candle stream: {symbol} ({interval})...")

        while True:
            try:
                candles = self.client.get_klines(symbol=symbol, interval=interval, limit=2)
                latest = candles[-1]

                candle = {
                    "timestamp": pd.to_datetime(latest[0], unit='ms'),
                    "open": float(latest[1]),
                    "high": float(latest[2]),
                    "low": float(latest[3]),
                    "close": float(latest[4]),
                    "volume": float(latest[5]),
                }

                if df.empty or candle["timestamp"] > df["timestamp"].iloc[-1]:
                    df = pd.concat([df, pd.DataFrame([candle])], ignore_index=True)
                    print(candle)

                time.sleep(poll_interval)

            except KeyboardInterrupt:
                print("Live candle streaming stopped manually.")
                break

            except Exception as e:
                print(f"Error fetching live candles: {e}")
                time.sleep(poll_interval)

        return df



@dataclass
class Transaction:
    """
    Handles market buy/sell orders with optional TP/SL via OCO orders
    """
    api_key: str | None = None
    api_secret: str | None = None
    testnet: bool = True
    api_url: str = "https://testnet.binance.vision/api"

    client: Client = field(init=False)

    def __post_init__(self):
        """Initialize client after dataclass creation."""
        self.client = Client(self.api_key, self.api_secret, testnet=self.testnet)
        self.client.API_URL = self.api_url

    def buy(self, symbol, quantity, take_profit=None, stop_loss=None):
        order = self.client.order_market_buy(symbol=symbol, quantity=quantity)
        executed = float(order["fills"][0]["price"])

        print(f"Buy executed at {executed}: {order}")

        return order

    def sell(self, symbol, quantity, take_profit=None, stop_loss=None):
        order = self.client.order_market_sell(symbol=symbol, quantity=quantity)
        executed = float(order["fills"][0]["price"])

        print(f"Sell executed at {executed}: {order}")

        return order
