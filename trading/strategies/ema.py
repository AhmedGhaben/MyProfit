import pandas_ta as ta
import pandas as pd

price = pd.read_csv("price.csv") #example file

def calc_ema(df, l: int):
    emaname = f"EMA{l}"
    df[emaname] = ta.ema(df["close"], length=l)

def cross58(df):
    calc_ema(df, 5)
    calc_ema(df, 8)
    lastcandle = df.iloc[-1]
    previouscandle = df.iloc[-2]

    if lastcandle["EMA5"] > lastcandle["EMA8"] and previouscandle["EMA5"] < previouscandle["EMA8"]:
        return True
    else:
        return False

#print(price)
#print(cross58(price))
