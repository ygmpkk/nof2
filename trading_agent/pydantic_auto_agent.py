"""Pydantic AI inspired auto-trading agent.

This module mirrors the approach described in the nof1.ai blog post by using
structured models to reason about trading decisions.  The implementation uses
lightweight helpers from :mod:`pydantic_ai` (bundled with the project for offline
use) to express typed market observations and trade plans.
"""
from __future__ import annotations

from typing import List, Optional

from .agent import TradingAgent
from .config import TradingConfig
from .data import MarketDataProvider, SimulatedMarketDataProvider, TechnicalIndicators
from pydantic_ai import Agent as StructuredAgent
from pydantic_ai import BaseModel


class MarketSnapshot(BaseModel):
    """Typed view of the current market state for a single symbol."""

    symbol: str
    prices: List[float]
    current_price: float
    sma_short: float
    sma_long: float
    rsi: float
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    has_position: bool
    position_quantity: float
    position_cost_basis: float
    unrealized_pnl_pct: float
    portfolio_value: float
    cash_available: float


class TradeDecision(BaseModel):
    """Structured output describing the action the agent should perform."""

    symbol: str
    action: str  # "buy", "sell", or "hold"
    quantity: float
    confidence: float
    reason: str


class TradingPlan(BaseModel):
    """Represents the decisions for a full trading step."""

    decisions: List[TradeDecision]


class PydanticAutoTradingAgent(TradingAgent):
    """Extension of :class:`TradingAgent` that relies on structured reasoning."""

    def __init__(
        self,
        config: Optional[TradingConfig] = None,
        data_provider: Optional[MarketDataProvider] = None,
    ) -> None:
        super().__init__(config=config, data_provider=data_provider)
        self.structured_agent = StructuredAgent(
            name="AutoTrader",
            input_model=MarketSnapshot,
            output_model=TradeDecision,
            planner=self._plan_trade,
            description=(
                "Generates disciplined trading decisions using technical "
                "indicator context and risk management data."
            ),
        )

    # ------------------------------------------------------------------
    # Planning helpers
    # ------------------------------------------------------------------
    def _build_snapshot(self, symbol: str, prices: List[float], current_price: float) -> MarketSnapshot:
        sma_short = TechnicalIndicators.moving_average(prices, period=max(5, len(prices) // 4))
        sma_long = TechnicalIndicators.moving_average(prices, period=max(10, len(prices) // 2))
        rsi = TechnicalIndicators.rsi(prices, period=14)
        boll_upper, boll_mid, boll_lower = TechnicalIndicators.bollinger_bands(prices, period=20, num_std=2.0)
        macd_line, macd_signal, macd_histogram = TechnicalIndicators.macd(prices)

        position = self.portfolio.get_position(symbol)
        has_position = position is not None
        position_quantity = position.quantity if position else 0.0
        cost_basis = position.average_price if position else 0.0
        unrealized_pct = position.pnl_pct if position else 0.0

        snapshot = MarketSnapshot(
            symbol=symbol,
            prices=list(prices),
            current_price=current_price,
            sma_short=sma_short,
            sma_long=sma_long,
            rsi=rsi,
            bollinger_upper=boll_upper,
            bollinger_middle=boll_mid,
            bollinger_lower=boll_lower,
            macd_line=macd_line,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            has_position=has_position,
            position_quantity=position_quantity,
            position_cost_basis=cost_basis,
            unrealized_pnl_pct=unrealized_pct,
            portfolio_value=self.portfolio.total_value,
            cash_available=self.portfolio.cash,
        )
        return snapshot

    def _plan_trade(self, snapshot: MarketSnapshot) -> TradeDecision:
        """Derive a deterministic trade decision from market context."""

        reason_components: List[str] = []
        action = "hold"
        confidence = 0.4
        quantity = 0.0

        trend_strength = snapshot.sma_short - snapshot.sma_long
        momentum_bias = snapshot.macd_histogram
        risk_buffer = self.config.max_position_size * snapshot.portfolio_value
        max_affordable = max(risk_buffer / max(snapshot.current_price, 1e-6), 0.0)

        # Entry conditions -------------------------------------------------
        if not snapshot.has_position:
            oversold = snapshot.rsi < 40 and snapshot.current_price <= snapshot.bollinger_lower
            bullish_trend = trend_strength > 0 and momentum_bias > 0

            if oversold or bullish_trend:
                action = "buy"
                base_confidence = 0.6 if oversold else 0.55
                confidence = min(0.95, base_confidence + abs(momentum_bias))
                quantity = round(max_affordable, 4)
                reason_components.append(
                    "Oversold rebound" if oversold else "Trend and momentum alignment"
                )

        # Exit conditions --------------------------------------------------
        else:
            stop_loss_triggered = snapshot.unrealized_pnl_pct <= -self.config.stop_loss_pct * 100
            take_profit_ready = snapshot.unrealized_pnl_pct >= self.config.take_profit_pct * 100
            overbought = snapshot.rsi > 60 and snapshot.current_price >= snapshot.bollinger_upper
            bearish_trend = trend_strength < 0 and momentum_bias < 0

            if stop_loss_triggered:
                action = "sell"
                confidence = 0.9
                reason_components.append("Stop loss protection")
            elif take_profit_ready:
                action = "sell"
                confidence = 0.85
                reason_components.append("Take profit target met")
            elif overbought or bearish_trend:
                action = "sell"
                confidence = min(0.9, 0.55 + abs(momentum_bias))
                reason_components.append(
                    "Overbought conditions" if overbought else "Momentum turning bearish"
                )

            if action == "sell":
                quantity = round(snapshot.position_quantity, 4)

        if action == "hold":
            reason_components.append("No decisive signal")

        reason = "; ".join(reason_components)
        return TradeDecision(
            symbol=snapshot.symbol,
            action=action,
            quantity=max(quantity, 0.0),
            confidence=max(0.0, min(confidence, 1.0)),
            reason=reason,
        )

    # ------------------------------------------------------------------
    # Trading loop overrides
    # ------------------------------------------------------------------
    def process_symbol(self, symbol: str) -> None:  # type: ignore[override]
        try:
            current_price = self.data_provider.get_latest_price(symbol)
            prices = self._get_historical_prices(symbol)
            if not prices:
                prices = [current_price]

            self.portfolio.update_prices({symbol: current_price})

            # Risk management check prior to planning a new trade
            if self.portfolio.has_position(symbol) and self._check_risk_management(symbol, current_price):
                if self.portfolio.close_position(symbol, current_price):
                    self.trade_count += 1
                    self.logger.info(f"Closed position due to risk rules: {symbol} at {current_price:.2f}")
                return

            snapshot = self._build_snapshot(symbol, prices, current_price)
            decision = self.structured_agent.run(snapshot)

            if decision.action == "sell" and self.portfolio.has_position(symbol):
                if self.portfolio.close_position(symbol, current_price):
                    self.trade_count += 1
                    self.logger.info(
                        f"Pydantic agent closed {symbol}: qty={decision.quantity:.4f}, "
                        f"price={current_price:.2f} | {decision.reason}"
                    )
            elif decision.action == "buy" and not self.portfolio.has_position(symbol):
                if decision.quantity <= 0:
                    return

                stop_loss = self._calculate_stop_loss(current_price, is_long=True)
                take_profit = self._calculate_take_profit(current_price, is_long=True)

                if self.portfolio.open_position(
                    symbol,
                    decision.quantity,
                    current_price,
                    stop_loss,
                    take_profit,
                ):
                    self.trade_count += 1
                    self.logger.info(
                        f"Pydantic agent opened {symbol}: qty={decision.quantity:.4f}, "
                        f"price={current_price:.2f}, SL={stop_loss:.2f}, TP={take_profit:.2f} | {decision.reason}"
                    )
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error(f"Pydantic agent error processing {symbol}: {exc}")

    def run(self, steps: int = 100):  # type: ignore[override]
        """Run the structured agent for ``steps`` iterations."""

        self.logger.info(
            "Starting Pydantic AI auto-trading session for %d symbols", len(self.config.symbols)
        )
        for _ in range(steps):
            for symbol in self.config.symbols:
                self.process_symbol(symbol)

            if isinstance(self.data_provider, SimulatedMarketDataProvider):
                self.data_provider.advance_time()

            summary = self.portfolio.get_summary()
            self.logger.debug(
                "Portfolio snapshot: value=%.2f cash=%.2f pnl%%=%.2f",
                summary["total_value"],
                summary["cash"],
                summary["total_pnl_pct"],
            )

        return self.portfolio.get_summary()

    def get_trading_plan(self) -> TradingPlan:
        """Return the most recent plan for all configured symbols."""

        decisions: List[TradeDecision] = []
        for symbol in self.config.symbols:
            current_price = self.data_provider.get_latest_price(symbol)
            prices = self._get_historical_prices(symbol)
            if not prices:
                prices = [current_price]
            snapshot = self._build_snapshot(symbol, prices, current_price)
            decisions.append(self.structured_agent.run(snapshot))
        return TradingPlan(decisions=decisions)
