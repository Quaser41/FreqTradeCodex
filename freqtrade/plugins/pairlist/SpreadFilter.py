"""
Spread pair list filter
"""

import logging

from freqtrade.exceptions import OperationalException
from freqtrade.exchange.exchange_types import Ticker, Tickers
from freqtrade.plugins.pairlist.IPairList import IPairList, PairlistParameter, SupportsBacktesting


logger = logging.getLogger(__name__)


class SpreadFilter(IPairList):
    supports_backtesting = SupportsBacktesting.NO

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._max_spread_ratio = self._pairlistconfig.get("max_spread_ratio", 0.005)
        self._enabled = self._max_spread_ratio != 0

        if not self._exchange.get_option("tickers_have_bid_ask"):
            raise OperationalException(
                f"{self.name} requires exchange to have bid/ask data for tickers, "
                "which is not available for the selected exchange / trading mode."
            )

        # Lists used to collect removed pairs during a refresh cycle
        self._removed_spread: list[str] = []
        self._removed_invalid: list[str] = []

    @property
    def needstickers(self) -> bool:
        """
        Boolean property defining if tickers are necessary.
        If no Pairlist requires tickers, an empty Dict is passed
        as tickers argument to filter_pairlist
        """
        return True

    def short_desc(self) -> str:
        """
        Short whitelist method description - used for startup-messages
        """
        return (
            f"{self.name} - Filtering pairs with ask/bid diff above {self._max_spread_ratio:.2%}."
        )

    @staticmethod
    def description() -> str:
        return "Filter by bid/ask difference."

    @staticmethod
    def available_parameters() -> dict[str, PairlistParameter]:
        return {
            "max_spread_ratio": {
                "type": "number",
                "default": 0.005,
                "description": "Max spread ratio",
                "help": "Max spread ratio for a pair to be considered.",
            },
        }

    def _validate_pair(self, pair: str, ticker: Ticker | None) -> bool:
        """
        Validate spread for the ticker
        :param pair: Pair that's currently validated
        :param ticker: ticker dict as returned from ccxt.fetch_ticker
        :return: True if the pair can stay, false if it should be removed
        """
        if ticker and "bid" in ticker and "ask" in ticker and ticker["ask"] and ticker["bid"]:
            spread = 1 - ticker["bid"] / ticker["ask"]
            if spread > self._max_spread_ratio:
                self._removed_spread.append(pair)
                return False
            else:
                return True
        self._removed_invalid.append(pair)
        return False

    def filter_pairlist(self, pairlist: list[str], tickers: Tickers) -> list[str]:
        """Filters the pairlist and logs a summary of removed pairs."""
        # Reset removal trackers for this refresh cycle
        self._removed_spread = []
        self._removed_invalid = []

        pairlist = super().filter_pairlist(pairlist, tickers)

        if self._removed_spread:
            pairs = ", ".join(sorted(self._removed_spread))
            self.log_once(
                (
                    f"Removed {len(self._removed_spread)} pairs from whitelist due to high spread: "
                    f"{pairs}"
                ),
                logger.info,
            )
        if self._removed_invalid:
            pairs = ", ".join(sorted(self._removed_invalid))
            msg = (
                "Removed "
                f"{len(self._removed_invalid)} pairs from whitelist due to invalid ticker data: "
                f"{pairs}"
            )
            self.log_once(msg, logger.info)

        return pairlist
