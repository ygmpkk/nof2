"""Trading execution helpers, including Binance order integration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, Optional

try:  # pragma: no cover - optional dependency for Binance integration
    from binance.client import Client as BinanceClient
    from binance.exceptions import BinanceAPIException
except Exception:  # pragma: no cover - fallback when library missing
    BinanceClient = None
    BinanceAPIException = Exception


@dataclass
class TradeExecutionResult:
    """Normalized view of an execution response."""

    symbol: str
    side: str
    quantity: float
    price: float
    raw: Dict[str, Any]


class TradeExecutor:
    """Abstract interface for sending live trades."""

    def buy(self, symbol: str, quantity: float) -> TradeExecutionResult:
        raise NotImplementedError

    def sell(self, symbol: str, quantity: float) -> TradeExecutionResult:
        raise NotImplementedError


class BinanceTradeExecutor(TradeExecutor):
    """Execute trades on Binance using market orders."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        testnet: bool = False,
        client: Optional[BinanceClient] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if client is not None:
            self.client = client
        else:
            if BinanceClient is None:
                raise ImportError("python-binance must be installed for Binance trading")
            self.client = BinanceClient(api_key, api_secret, testnet=testnet)

        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._lot_size_cache: Dict[str, Dict[str, Decimal]] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _fetch_lot_size(self, symbol: str) -> Dict[str, Decimal]:
        """Fetch and cache lot-size settings for *symbol*."""

        if symbol in self._lot_size_cache:
            return self._lot_size_cache[symbol]

        try:
            info = self.client.get_symbol_info(symbol)
        except BinanceAPIException as exc:  # pragma: no cover - depends on API
            self.logger.error("Failed to fetch symbol info for %s: %s", symbol, exc)
            raise

        if not info:
            raise ValueError(f"Unknown Binance symbol: {symbol}")

        lot_filter = next(
            (f for f in info.get("filters", []) if f.get("filterType") == "LOT_SIZE"),
            None,
        )
        if not lot_filter:
            raise ValueError(f"Missing LOT_SIZE filter for symbol {symbol}")

        data = {
            "stepSize": Decimal(lot_filter["stepSize"]),
            "minQty": Decimal(lot_filter["minQty"]),
        }
        self._lot_size_cache[symbol] = data
        return data

    def _normalize_quantity(self, symbol: str, quantity: float) -> Decimal:
        """Normalize *quantity* according to the symbol's lot size."""

        lot = self._fetch_lot_size(symbol)
        step = lot["stepSize"]
        precision = abs(step.normalize().as_tuple().exponent)
        quantized = Decimal(str(quantity)).quantize(
            Decimal(f"1e-{precision}"), rounding=ROUND_DOWN
        )

        if quantized < lot["minQty"]:
            raise ValueError(
                f"Quantity {quantized} is below Binance minimum {lot['minQty']} for {symbol}"
            )

        # Ensure compatibility with the step size by removing residual decimals
        residual = (quantized / step).quantize(Decimal("1"), rounding=ROUND_DOWN)
        quantized = residual * step
        return quantized

    def _build_result(self, symbol: str, side: str, response: Dict[str, Any]) -> TradeExecutionResult:
        """Create a :class:`TradeExecutionResult` from a Binance response."""

        fills = response.get("fills") or []
        if fills:
            total_cost = sum(float(fill["price"]) * float(fill["qty"]) for fill in fills)
            total_qty = sum(float(fill["qty"]) for fill in fills)
            avg_price = total_cost / total_qty if total_qty else float(response.get("price", 0.0))
            executed_qty = total_qty
        else:
            avg_price = float(response.get("price") or response.get("avgPrice") or 0.0)
            executed_qty = float(response.get("executedQty") or response.get("origQty") or 0.0)

        return TradeExecutionResult(
            symbol=symbol,
            side=side,
            quantity=executed_qty,
            price=avg_price,
            raw=response,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def buy(self, symbol: str, quantity: float) -> TradeExecutionResult:
        normalized_qty = self._normalize_quantity(symbol, quantity)
        try:
            response = self.client.create_order(
                symbol=symbol,
                side=BinanceClient.SIDE_BUY,
                type=BinanceClient.ORDER_TYPE_MARKET,
                quantity=float(normalized_qty),
            )
        except BinanceAPIException as exc:  # pragma: no cover - depends on API
            self.logger.error("Binance BUY order failed for %s: %s", symbol, exc)
            raise
        return self._build_result(symbol, "BUY", response)

    def sell(self, symbol: str, quantity: float) -> TradeExecutionResult:
        normalized_qty = self._normalize_quantity(symbol, quantity)
        try:
            response = self.client.create_order(
                symbol=symbol,
                side=BinanceClient.SIDE_SELL,
                type=BinanceClient.ORDER_TYPE_MARKET,
                quantity=float(normalized_qty),
            )
        except BinanceAPIException as exc:  # pragma: no cover - depends on API
            self.logger.error("Binance SELL order failed for %s: %s", symbol, exc)
            raise
        return self._build_result(symbol, "SELL", response)

