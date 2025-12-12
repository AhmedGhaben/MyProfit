import time
from market import CandleData, Transaction
from trading import EMACrossoverStrategy, Trade
import binance_credentials

API_KEY = binance_credentials.API_KEY
API_SECRET = binance_credentials.API_SECRET

candle_data = CandleData(api_key=API_KEY, api_secret=API_SECRET, testnet=True)
transaction = Transaction(api_key=API_KEY, api_secret=API_SECRET, testnet=True)

#Setup
symbol = "BTCUSDT"
quantity = 0.001

strategy = EMACrossoverStrategy(candle_data=candle_data)
trade = Trade(transaction=transaction, symbol=symbol, quantity=quantity)


poll_interval = 15  # seconds
RUN_BOT = True      # bool switch

print(f"Running bot on {symbol}")

while RUN_BOT:

    try:
        trade.check_tp_sl()

        strategy.fetch_data(symbol, interval="1m", lookback="20 minutes ago UTC")

        signals = strategy.cross58_signal()

        trade.process_signals(signals)

        time.sleep(poll_interval)

    except KeyboardInterrupt:
        print("\nBot stopped manually")

    except Exception as e:
        print(f"Error in bot loop: {e}")
        time.sleep(poll_interval)

print("Bot stopped")
