from freqtrade.strategy import IStrategy
import pandas as pd
import talib.abstract as ta


class ScalpRsiStrategy(IStrategy):
    """Simple RSI based scalp strategy."""
    timeframe = "5m"
    startup_candle_count = 50
    can_short = False

    # Adjusted for a moderate risk profile
    minimal_roi = {
        "0": 0.03,   # Take profit 3%
        "30": 0.01,  # After 30 minutes, accept 1%
        "60": 0
    }

    stoploss = -0.02  # Hard stoploss at 2%

    rsi_buy = 30
    rsi_sell = 70

    def populate_indicators(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df["rsi"] = ta.RSI(df, timeperiod=14)
        return df

    def populate_buy_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[
            (df["rsi"] < self.rsi_buy),
            "buy"
        ] = 1
        return df

    def populate_sell_trend(self, df: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        df.loc[
            (df["rsi"] > self.rsi_sell),
            "sell"
        ] = 1
        return df
