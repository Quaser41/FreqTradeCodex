"""Cryptofeed adapter
----------------------

This module exposes a small adapter around the `cryptofeed` project which
subscribes to public websocket channels for multiple exchanges and forwards
trade and ticker events to Freqtrade via the external message interface.

The adapter spins up a very small websocket server using
`ExternalMessageProducer` so that a Freqtrade bot configured with
``external_message_consumer`` can subscribe to these updates.

Example usage::

    $ python -m freqtrade.datafeeds.cryptofeed_adapter --pairs BTC-USDT,ETH-USDT

The server will listen on ``ws://localhost:9000`` by default.  Pairs can be
specified as a comma separated list.  Trade and ticker updates from the
following exchanges are supported: KuCoin, OKX, Kraken, Bybit and Bitfinex.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, List
from urllib.parse import urlparse

import websockets
from cryptofeed import FeedHandler
from cryptofeed.defines import TICKER, TRADES
from cryptofeed.exchanges import Bitfinex, Bybit, Kraken, Kucoin, OKX


class ExternalMessageProducer:
    """Minimal websocket based message producer.

    The real Freqtrade project exposes a similar helper which acts as the
    counterpart to :class:`~freqtrade.rpc.external_message_consumer.ExternalMessageConsumer`.
    For the purpose of this example adapter we only require a very small
    subset of the functionality – broadcasting JSON encoded messages to all
    connected clients.
    """

    def __init__(self, url: str) -> None:
        parsed = urlparse(url)
        self._host = parsed.hostname or "localhost"
        self._port = parsed.port or 9000
        self._clients: set[websockets.WebSocketServerProtocol] = set()
        self._server: websockets.server.Serve | None = None

    async def _handler(self, ws: websockets.WebSocketServerProtocol) -> None:
        self._clients.add(ws)
        try:
            # keep the connection open
            async for _ in ws:
                pass
        finally:
            self._clients.discard(ws)

    async def start(self) -> None:
        """Start the websocket server."""

        self._server = await websockets.serve(self._handler, self._host, self._port)

    async def publish(self, message: dict[str, Any]) -> None:
        """Publish *message* to all connected websocket clients."""

        if not self._clients:
            return
        websockets.broadcast(self._clients, json.dumps(message))


class CryptofeedAdapter:
    """Bridge ``cryptofeed`` events to Freqtrade's message channel."""

    def __init__(self, url: str, pairs: List[str]):
        self._pairs = pairs
        self._producer = ExternalMessageProducer(url)
        self._fh = FeedHandler()

        callbacks = {TRADES: self._on_trade, TICKER: self._on_ticker}
        exchanges = [Kucoin, OKX, Kraken, Bybit, Bitfinex]

        for ex in exchanges:
            # Each exchange can subscribe to the same list of pairs.
            # ``cryptofeed`` uses the term "symbols" for trading pairs.
            self._fh.add_feed(ex(symbols=self._pairs, channels=[TRADES, TICKER], callbacks=callbacks))

    async def _on_trade(self, feed: str, symbol: str, data: Any, timestamp: float, receipt_timestamp: float) -> None:  # noqa: D401
        """Handle trade events and forward them to the consumer."""

        message = {
            "type": "trade",
            "exchange": feed,
            "symbol": symbol,
            "data": data,
            "timestamp": timestamp,
        }
        await self._producer.publish(message)

    async def _on_ticker(self, feed: str, symbol: str, data: Any, timestamp: float, receipt_timestamp: float) -> None:  # noqa: D401
        """Handle ticker events and forward them to the consumer."""

        message = {
            "type": "ticker",
            "exchange": feed,
            "symbol": symbol,
            "data": data,
            "timestamp": timestamp,
        }
        await self._producer.publish(message)

    async def run(self) -> None:
        """Run the websocket producer and cryptofeed event loop."""

        await self._producer.start()
        # ``FeedHandler.run`` is a coroutine starting the internal tasks.
        await self._fh.run()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start cryptofeed adapter")
    parser.add_argument("--url", default="ws://localhost:9000", help="Websocket URL for the producer")
    parser.add_argument("--pairs", default="BTC-USDT", help="Comma separated list of symbols")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    pairs = [p.strip() for p in args.pairs.split(",") if p.strip()]
    adapter = CryptofeedAdapter(args.url, pairs)
    asyncio.run(adapter.run())


if __name__ == "__main__":
    main()

