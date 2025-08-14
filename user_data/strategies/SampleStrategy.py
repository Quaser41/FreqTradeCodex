from freqtrade.strategy import IStrategy
from pandas import DataFrame
import talib.abstract as ta


class SampleStrategy(IStrategy):
    """Simple moving average crossover strategy."""

    timeframe = '5m'
    minimal_roi = {"0": 0.10}
    stoploss = -0.10
    trailing_stop = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=9)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=21)
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe['ema_fast'] > dataframe['ema_slow']) &
                      (dataframe['close'] > dataframe['ema_fast']), 'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe['ema_fast'] < dataframe['ema_slow']) &
                      (dataframe['close'] < dataframe['ema_fast']), 'sell'] = 1
        return dataframe
