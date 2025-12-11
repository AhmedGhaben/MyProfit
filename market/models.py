import pandas as pd
from binance.client import Client
import time


class CandleData:
    """
    Handles the price-fetching (including live price streaming)
    """
    def __init__(self, api_key=None, api_secret=None, testnet=True):
        self.client = Client(api_key,
                             api_secret,
                             testnet=testnet)
        self.client.API_URL = 'https://testnet.binance.vision/api'

    def get_candles(self, symbol, interval='1m', start_str='2 hours ago UTC', end_str=None):
        """
        Fetch price data as candles
        """
        klines = self.client.get_historical_klines(symbol, interval, start_str, end_str)

        df = pd.DataFrame(klines, columns=[
            "timestamp", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
        ])

        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)

        df = df[["timestamp", "open", "high", "low", "close", "volume"]]
        return df

    def get_latest_price(self, symbol):
        """
        Fetch the latest price
        """
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def stream_candles(self, symbol, interval='1m', poll_interval=10):
        """
        Stream live candle data into a pandas DataFrame
        """
        df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        print(f"Starting live candle stream: {symbol} ({interval})...")

        while True:
            try:
                candles = self.client.get_klines(symbol=symbol, interval=interval, limit=2)
                latest_candle = candles[-1]

                candle_data = {
                    "timestamp": pd.to_datetime(latest_candle[0], unit='ms'),
                    "open": float(latest_candle[1]),
                    "high": float(latest_candle[2]),
                    "low": float(latest_candle[3]),
                    "close": float(latest_candle[4]),
                    "volume": float(latest_candle[5])
                }

                if df.empty or candle_data["timestamp"] > df["timestamp"].iloc[-1]:
                    df = pd.concat([df, pd.DataFrame([candle_data])], ignore_index=True)
                    print(candle_data)

                time.sleep(poll_interval)
            except KeyboardInterrupt:
                print("Live candle streaming stopped manually")
                break
            except Exception as e:
                print(f"Error fetching live candles: {e}")
                time.sleep(poll_interval)

        return df


class Transaction:
    """
    Handles market transactions with optional TP/SL via OCO orders
    """
    def __init__(self, api_key=None, api_secret=None, testnet=True):
        self.client = Client(api_key,
                             api_secret,
                             testnet=testnet)
        self.client.API_URL = 'https://testnet.binance.vision/api'

    def buy(self, symbol, quantity, take_profit=None, stop_loss=None, risk_reward_ratio=1):
        """
        Market buy with optional TP/SL
        risk_reward_ratio: TP distance / SL distance
        """
        order = self.client.order_market_buy(symbol=symbol, quantity=quantity)
        executed_price = float(order['fills'][0]['price'])
        print(f"Buy order executed at {executed_price}: {order}")

        if take_profit or stop_loss or risk_reward_ratio:
            self._create_oco_order(
                symbol, quantity, side='SELL',
                take_profit=take_profit, stop_loss=stop_loss,
                executed_price=executed_price,
                risk_reward_ratio=risk_reward_ratio
            )
        return order

    def sell(self, symbol, quantity, take_profit=None, stop_loss=None, risk_reward_ratio=1):
        """
        Market sell with optional TP/SL
        risk_reward_ratio: TP distance / SL distance
        """
        order = self.client.order_market_sell(symbol=symbol, quantity=quantity)
        executed_price = float(order['fills'][0]['price'])
        print(f"Sell order executed at {executed_price}: {order}")

        if take_profit or stop_loss or risk_reward_ratio:
            self._create_oco_order(
                symbol, quantity, side='BUY',
                take_profit=take_profit, stop_loss=stop_loss,
                executed_price=executed_price,
                risk_reward_ratio=risk_reward_ratio
            )
        return order

    def _create_oco_order(self, symbol, quantity, side, executed_price,
                          take_profit=None, stop_loss=None, risk_reward_ratio=1):
        """
        Place an OCO order with optional TP/SL (or calculated via risk/reward ratio)
        """

        if stop_loss is None:
            stop_loss = executed_price * 0.99 if side == 'SELL' else executed_price * 1.01

        if take_profit is None:
            if side == 'SELL':
                take_profit = executed_price + (executed_price - stop_loss) * risk_reward_ratio
            else:
                take_profit = executed_price - (stop_loss - executed_price) * risk_reward_ratio

        stop_limit_price = stop_loss * 0.995 if side == 'SELL' else stop_loss * 1.005

        oco_order = self.client.create_oco_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=str(round(take_profit, 8)),
            stopPrice=str(round(stop_loss, 8)),
            stopLimitPrice=str(round(stop_limit_price, 8)),
            stopLimitTimeInForce='GTC'
        )
        print(f"OCO order placed: {oco_order}")
        return oco_order
