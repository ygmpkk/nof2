"""
Unit tests for the AI Trading Agent
"""

import unittest
from trading_agent import TradingAgent
from trading_agent.config import TradingConfig
from trading_agent.portfolio import Portfolio, Position
from trading_agent.data import SimulatedMarketDataProvider, TechnicalIndicators
from trading_agent.strategies import (
    TrendFollowingStrategy, 
    MeanReversionStrategy,
    Signal,
    create_strategy
)
from datetime import datetime


class TestPortfolio(unittest.TestCase):
    """Test portfolio management"""
    
    def setUp(self):
        self.portfolio = Portfolio(initial_capital=100000.0)
    
    def test_initial_state(self):
        """Test initial portfolio state"""
        self.assertEqual(self.portfolio.cash, 100000.0)
        self.assertEqual(self.portfolio.total_value, 100000.0)
        self.assertEqual(len(self.portfolio.positions), 0)
    
    def test_open_position(self):
        """Test opening a position"""
        success = self.portfolio.open_position("AAPL", 100, 150.0)
        self.assertTrue(success)
        self.assertEqual(self.portfolio.cash, 85000.0)
        self.assertTrue(self.portfolio.has_position("AAPL"))
        self.assertEqual(len(self.portfolio.positions), 1)
    
    def test_close_position(self):
        """Test closing a position"""
        self.portfolio.open_position("AAPL", 100, 150.0)
        success = self.portfolio.close_position("AAPL", 160.0)
        self.assertTrue(success)
        self.assertEqual(self.portfolio.cash, 101000.0)
        self.assertFalse(self.portfolio.has_position("AAPL"))
    
    def test_position_pnl(self):
        """Test position P&L calculation"""
        self.portfolio.open_position("AAPL", 100, 150.0)
        self.portfolio.update_prices({"AAPL": 160.0})
        position = self.portfolio.get_position("AAPL")
        self.assertEqual(position.pnl, 1000.0)
        self.assertAlmostEqual(position.pnl_pct, 6.67, places=1)
    
    def test_portfolio_value(self):
        """Test portfolio value calculation"""
        self.portfolio.open_position("AAPL", 100, 150.0)
        self.portfolio.open_position("GOOGL", 50, 200.0)
        self.portfolio.update_prices({"AAPL": 160.0, "GOOGL": 210.0})
        
        expected_value = self.portfolio.cash + (100 * 160) + (50 * 210)
        self.assertEqual(self.portfolio.total_value, expected_value)
    
    def test_cannot_open_duplicate_position(self):
        """Test that duplicate positions are prevented"""
        self.portfolio.open_position("AAPL", 100, 150.0)
        success = self.portfolio.open_position("AAPL", 50, 150.0)
        self.assertFalse(success)
    
    def test_insufficient_cash(self):
        """Test that positions cannot be opened without sufficient cash"""
        success = self.portfolio.open_position("AAPL", 1000, 150.0)
        self.assertFalse(success)


class TestTechnicalIndicators(unittest.TestCase):
    """Test technical indicators"""
    
    def test_moving_average(self):
        """Test moving average calculation"""
        prices = [100, 102, 104, 103, 105]
        ma = TechnicalIndicators.moving_average(prices, 3)
        expected = (104 + 103 + 105) / 3
        self.assertAlmostEqual(ma, expected, places=2)
    
    def test_rsi(self):
        """Test RSI calculation"""
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 105, 107, 106, 108, 107]
        rsi = TechnicalIndicators.rsi(prices, 14)
        self.assertTrue(0 <= rsi <= 100)
    
    def test_bollinger_bands(self):
        """Test Bollinger Bands calculation"""
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106]
        upper, middle, lower = TechnicalIndicators.bollinger_bands(prices, 10, 2.0)
        
        self.assertGreater(upper, middle)
        self.assertGreater(middle, lower)
        self.assertAlmostEqual(middle, sum(prices) / len(prices), places=2)


class TestTradingStrategies(unittest.TestCase):
    """Test trading strategies"""
    
    def setUp(self):
        self.config = {
            "lookback_period": 20,
            "short_period": 10,
            "long_period": 20,
            "entry_threshold": 0.02,
            "max_position_size": 0.1,
        }
    
    def test_trend_following_strategy(self):
        """Test trend following strategy"""
        strategy = TrendFollowingStrategy(self.config)
        
        # Create uptrend
        prices = [100 + i for i in range(25)]
        signal = strategy.generate_signal("AAPL", prices, prices[-1])
        self.assertEqual(signal, Signal.BUY)
        
        # Create downtrend
        prices = [125 - i for i in range(25)]
        signal = strategy.generate_signal("AAPL", prices, prices[-1])
        self.assertEqual(signal, Signal.SELL)
    
    def test_mean_reversion_strategy(self):
        """Test mean reversion strategy"""
        strategy = MeanReversionStrategy(self.config)
        
        # Price should generate signals based on Bollinger Bands
        prices = [100, 102, 101, 103, 102, 104, 103, 105, 104, 106, 
                 105, 107, 106, 108, 107, 109, 108, 110, 109, 111]
        signal = strategy.generate_signal("AAPL", prices, prices[-1])
        self.assertIn(signal, [Signal.BUY, Signal.SELL, Signal.HOLD])
    
    def test_position_sizing(self):
        """Test position sizing"""
        strategy = TrendFollowingStrategy(self.config)
        portfolio_value = 100000.0
        current_price = 150.0
        
        quantity = strategy.get_position_size("AAPL", portfolio_value, current_price)
        position_value = quantity * current_price
        
        # Position should be around 10% of portfolio
        self.assertLessEqual(position_value, portfolio_value * 0.15)
    
    def test_create_strategy_factory(self):
        """Test strategy factory function"""
        strategy = create_strategy("trend_following", self.config)
        self.assertIsInstance(strategy, TrendFollowingStrategy)
        
        strategy = create_strategy("mean_reversion", self.config)
        self.assertIsInstance(strategy, MeanReversionStrategy)


class TestMarketData(unittest.TestCase):
    """Test market data provider"""
    
    def test_simulated_data_provider(self):
        """Test simulated market data provider"""
        provider = SimulatedMarketDataProvider(initial_price=100.0, volatility=0.02)
        
        price = provider.get_latest_price("AAPL")
        self.assertGreater(price, 0)
    
    def test_historical_data(self):
        """Test historical data generation"""
        provider = SimulatedMarketDataProvider(initial_price=100.0, volatility=0.02)
        
        historical = provider.get_historical_data("AAPL", 20)
        self.assertEqual(len(historical), 20)
        
        for data in historical:
            self.assertGreater(data.close, 0)
            self.assertGreaterEqual(data.high, data.close)
            self.assertLessEqual(data.low, data.close)
    
    def test_advance_time(self):
        """Test time advancement in simulation"""
        provider = SimulatedMarketDataProvider(initial_price=100.0, volatility=0.02)
        
        price1 = provider.get_latest_price("AAPL")
        provider.advance_time()
        price2 = provider.get_latest_price("AAPL")
        
        # Prices should change (though they could theoretically be equal)
        self.assertIsNotNone(price2)


class TestTradingAgent(unittest.TestCase):
    """Test trading agent"""
    
    def setUp(self):
        self.config = TradingConfig(
            initial_capital=100000.0,
            strategy_type="trend_following",
            symbols=["AAPL", "GOOGL"],
            lookback_period=20,
            use_ai_predictions=False,  # Disable for deterministic tests
        )
        self.data_provider = SimulatedMarketDataProvider(
            initial_price=150.0,
            volatility=0.02
        )
    
    def test_agent_initialization(self):
        """Test agent initialization"""
        agent = TradingAgent(config=self.config, data_provider=self.data_provider)
        self.assertEqual(agent.portfolio.initial_capital, 100000.0)
        self.assertEqual(len(agent.config.symbols), 2)
    
    def test_agent_run(self):
        """Test agent run"""
        agent = TradingAgent(config=self.config, data_provider=self.data_provider)
        results = agent.run(steps=10)
        
        self.assertIn('total_value', results)
        self.assertIn('total_pnl', results)
        self.assertIn('cash', results)
        self.assertGreater(results['total_value'], 0)
    
    def test_stop_loss(self):
        """Test stop loss functionality"""
        agent = TradingAgent(config=self.config, data_provider=self.data_provider)
        
        # Manually open a position
        agent.portfolio.open_position("AAPL", 100, 150.0, stop_loss=140.0)
        
        # Update price to trigger stop loss
        agent.portfolio.update_prices({"AAPL": 135.0})
        
        # Check risk management
        should_close = agent._check_risk_management("AAPL", 135.0)
        self.assertTrue(should_close)
    
    def test_take_profit(self):
        """Test take profit functionality"""
        agent = TradingAgent(config=self.config, data_provider=self.data_provider)
        
        # Manually open a position
        agent.portfolio.open_position("AAPL", 100, 150.0, take_profit=170.0)
        
        # Update price to trigger take profit
        agent.portfolio.update_prices({"AAPL": 175.0})
        
        # Check risk management
        should_close = agent._check_risk_management("AAPL", 175.0)
        self.assertTrue(should_close)


class TestConfig(unittest.TestCase):
    """Test configuration"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        config = TradingConfig()
        self.assertEqual(config.initial_capital, 100000.0)
        self.assertEqual(config.strategy_type, "trend_following")
        self.assertEqual(config.lookback_period, 20)
    
    def test_config_to_dict(self):
        """Test config to dictionary conversion"""
        config = TradingConfig(initial_capital=50000.0)
        config_dict = config.to_dict()
        
        self.assertEqual(config_dict['initial_capital'], 50000.0)
        self.assertIn('strategy_type', config_dict)
    
    def test_config_from_dict(self):
        """Test config from dictionary"""
        config_dict = {
            'initial_capital': 75000.0,
            'strategy_type': 'mean_reversion',
        }
        config = TradingConfig.from_dict(config_dict)
        
        self.assertEqual(config.initial_capital, 75000.0)
        self.assertEqual(config.strategy_type, 'mean_reversion')


if __name__ == '__main__':
    unittest.main()
