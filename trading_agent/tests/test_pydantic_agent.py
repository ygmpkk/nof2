"""Tests for the Pydantic auto trading agent."""

import unittest

from trading_agent import PydanticAutoTradingAgent
from trading_agent.config import TradingConfig
from trading_agent.data import SimulatedMarketDataProvider


class TestPydanticAutoTradingAgent(unittest.TestCase):
    """Ensure the structured trading agent behaves deterministically."""

    def setUp(self) -> None:
        self.config = TradingConfig(
            initial_capital=50000.0,
            strategy_type="trend_following",
            symbols=["AAPL", "MSFT"],
            use_ai_predictions=False,
            max_position_size=0.1,
        )
        self.data_provider = SimulatedMarketDataProvider(initial_price=120.0, volatility=0.01)

    def test_generate_plan(self):
        agent = PydanticAutoTradingAgent(config=self.config, data_provider=self.data_provider)
        plan = agent.get_trading_plan()

        self.assertEqual(len(plan.decisions), len(self.config.symbols))
        for decision in plan.decisions:
            self.assertIn(decision.action, {"buy", "sell", "hold"})
            self.assertGreaterEqual(decision.confidence, 0.0)
            self.assertLessEqual(decision.confidence, 1.0)
            self.assertGreaterEqual(decision.quantity, 0.0)
            self.assertTrue(decision.reason)

    def test_run_updates_portfolio(self):
        agent = PydanticAutoTradingAgent(config=self.config, data_provider=self.data_provider)
        results = agent.run(steps=5)

        self.assertIn("total_value", results)
        self.assertIn("cash", results)
        self.assertGreater(results["total_value"], 0)
        self.assertGreaterEqual(results["cash"], 0)


if __name__ == "__main__":
    unittest.main()
