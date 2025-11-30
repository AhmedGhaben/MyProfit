import pandas_ta as ta
import pandas as pd

price = pd.read_csv("price.csv") #example

#imports live data from yfinance
live_test = pd.DataFrame()
live_test = live_test.ta.ticker("btc-usd", period="5d", interval="15m")

def calc_ema(df, l: int):
    emaname = f"EMA{l}"
    df[emaname] = ta.ema(df["Close"], length=l)

def cross_58(df):
    calc_ema(df, 5)
    calc_ema(df, 8)
    lastcandle = df.iloc[-1]
    previouscandle = df.iloc[-2]

    if lastcandle["EMA5"] > lastcandle["EMA8"] and previouscandle["EMA5"] < previouscandle["EMA8"]:
        print("Buy")
        return True

    elif lastcandle["EMA5"] < lastcandle["EMA8"] and previouscandle["EMA5"] > previouscandle["EMA8"]:
        print("Sell")
        return True
    else:
        return False


#print(price)
#print(cross_58(price))
print(live_test)
#print(cross_58(live_test))

#while True:
    #if (cross_58(live_test)):
        #print(cross_58(live_test))