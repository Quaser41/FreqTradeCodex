from datetime import datetime
from functools import reduce

import pandas_ta as ta
from pandas import DataFrame
from technical import qtpylib

from freqtrade.persistence import Trade
from freqtrade.strategy import BooleanParameter, IntParameter, IStrategy


class HybridStrategy(IStrategy):
    """EMA crossover with optional RSI, volume, and TEMA/Bollinger confirmations.

    Parameters:
        rsi_entry: RSI threshold for entries. Default: 50.
        use_volume_filter: Enable volume moving-average filter. Default: True.
        use_tema_bband: Require TEMA below Bollinger mid-band and rising. Default: True.

    ROI and stoploss are defined within this strategy to keep it self-contained.
    user_data/config.json should not define these parameters.
    """

    timeframe = "5m"
    # Minimal ROI mapping.
    minimal_roi = {
        "0": 0.05,
        "15": 0.03,
        "30": 0.02,
        "60": 0.01,
        "120": 0.0,
    }
    # Initial stoploss.
    stoploss = -0.10
    process_only_new_candles = True
    startup_candle_count: int = 50

    rsi_entry = IntParameter(1, 100, default=50)
    use_volume_filter = BooleanParameter(default=True)
    use_tema_bband = BooleanParameter(default=True)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.ema(dataframe["close"], length=5)
        dataframe["ema_slow"] = ta.ema(dataframe["close"], length=20)
        dataframe["rsi"] = ta.rsi(dataframe["close"], length=14)
        dataframe["volume_sma"] = dataframe["volume"].rolling(window=20).mean()
        dataframe["tema"] = ta.tema(dataframe["close"], length=9)
        dataframe["atr"] = ta.atr(
            high=dataframe["high"],
            low=dataframe["low"],
            close=dataframe["close"],
            length=14,
        )
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe["bb_lowerband"] = bollinger["lower"]
        dataframe["bb_middleband"] = bollinger["mid"]
        dataframe["bb_upperband"] = bollinger["upper"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = [
            qtpylib.crossed_above(dataframe["ema_fast"], dataframe["ema_slow"]),
            dataframe["rsi"] < self.rsi_entry.value,
        ]

        if self.use_volume_filter.value:
            conditions.append(dataframe["volume"] > dataframe["volume_sma"])

        if self.use_tema_bband.value:
            conditions.append(dataframe["tema"] <= dataframe["bb_middleband"])
            conditions.append(dataframe["tema"] > dataframe["tema"].shift(1))

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x & y, conditions),
                "enter_long",
            ] = 1
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                qtpylib.crossed_below(dataframe["ema_fast"], dataframe["ema_slow"])
                | (dataframe["rsi"] > 70)
                | (dataframe["tema"] < dataframe["tema"].shift(1))
            ),
            "exit_long",
        ] = 1
        return dataframe

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty:
            return self.stoploss

        atr = dataframe["atr"].iloc[-1]
        if atr is None or current_rate == 0:
            return self.stoploss

        atr_stop = -atr / current_rate
        return max(self.stoploss, atr_stop)
