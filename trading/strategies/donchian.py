import pandas_ta as ta
import pandas as pd

price = pd.read_csv("price.csv") #example file

price.ta.donchian(append=True)