import talib.abstract as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.strategy import IntParameter, IStrategy


class CombinedIndicatorStrategy(IStrategy):
    """EMA crossover with RSI confirmation and volume filter.

    Defaults & ranges:
    - ``ema_fast_period``: 5 (2-50)
    - ``ema_slow_period``: 20 (10-200)
    - ``rsi_oversold``: 30 (10-50)
    - ``rsi_overbought``: 70 (50-90)
    - ``volume_lookback``: 20 (5-50)
    """

    timeframe = "5m"
    minimal_roi = {
        "0": 0.05,
    }
    stoploss = -0.1

    ema_fast_period = IntParameter(2, 50, default=5)
    ema_slow_period = IntParameter(10, 200, default=20)
    rsi_oversold = IntParameter(10, 50, default=30)
    rsi_overbought = IntParameter(50, 90, default=70)
    volume_lookback = IntParameter(5, 50, default=20)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=int(self.ema_fast_period.value))
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=int(self.ema_slow_period.value))
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["volume_sma"] = ta.SMA(
            dataframe["volume"], timeperiod=int(self.volume_lookback.value)
        )
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                qtpylib.crossed_above(dataframe["ema_fast"], dataframe["ema_slow"])
                & (dataframe["rsi"] < self.rsi_oversold.value)
                & (dataframe["volume"] > dataframe["volume_sma"])
            ),
            "enter_long",
        ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                qtpylib.crossed_below(dataframe["ema_fast"], dataframe["ema_slow"])
                | (dataframe["rsi"] > self.rsi_overbought.value)
            ),
            "exit_long",
        ] = 1
        return dataframe
