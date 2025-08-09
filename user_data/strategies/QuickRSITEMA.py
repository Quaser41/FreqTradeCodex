from functools import lru_cache
from freqtrade.strategy import IStrategy, IntParameter
import pandas as pd
import talib.abstract as ta

class QuickRSITEMA(IStrategy):
    timeframe = "5m"
    startup_candle_count = 100
    can_short = False

    rsi_buy = IntParameter(20, 45, default=30, space="buy")
    rsi_sell = IntParameter(55, 80, default=70, space="sell")
    tema_len = IntParameter(5, 20, default=9, space="buy")

    minimal_roi = { "0": 0.02 }       # take profit at ~2%
    stoploss = -0.03                   # hard stop ~3%

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df["rsi"] = ta.RSI(df, timeperiod=14)
        df["tema"] = ta.TEMA(df["close"], timeperiod=int(self.tema_len.value))
        df["tema_prev"] = df["tema"].shift(1)
        return df

    def populate_buy_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[
            (df["rsi"] < int(self.rsi_buy.value)) &
            (df["tema"] > df["tema_prev"]),
            "buy"
        ] = 1
        return df

    def populate_sell_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[
            (df["rsi"] > int(self.rsi_sell.value)) |
            (df["tema"] < df["tema_prev"]),
            "sell"
        ] = 1
        return df
