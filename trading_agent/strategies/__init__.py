"""
Trading strategies for the AI agent
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from enum import Enum
from ..data.market_data import TechnicalIndicators


class Signal(Enum):
    """Trading signals"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradingStrategy(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.lookback_period = config.get("lookback_period", 20)
    
    @abstractmethod
    def generate_signal(self, symbol: str, prices: List[float], 
                       current_price: float) -> Signal:
        """Generate trading signal"""
        pass
    
    @abstractmethod
    def get_position_size(self, symbol: str, portfolio_value: float, 
                         current_price: float) -> float:
        """Calculate position size"""
        pass


class TrendFollowingStrategy(TradingStrategy):
    """Trend following strategy using moving averages"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.short_period = config.get("short_period", 10)
        self.long_period = config.get("long_period", 20)
        self.entry_threshold = config.get("entry_threshold", 0.02)
    
    def generate_signal(self, symbol: str, prices: List[float], 
                       current_price: float) -> Signal:
        """Generate signal based on moving average crossover"""
        if len(prices) < self.long_period:
            return Signal.HOLD
        
        short_ma = TechnicalIndicators.moving_average(prices, self.short_period)
        long_ma = TechnicalIndicators.moving_average(prices, self.long_period)
        
        # Calculate the percentage difference
        ma_diff_pct = (short_ma - long_ma) / long_ma
        
        # Buy signal: short MA crosses above long MA
        if ma_diff_pct > self.entry_threshold:
            return Signal.BUY
        
        # Sell signal: short MA crosses below long MA
        if ma_diff_pct < -self.entry_threshold:
            return Signal.SELL
        
        return Signal.HOLD
    
    def get_position_size(self, symbol: str, portfolio_value: float, 
                         current_price: float) -> float:
        """Calculate position size based on portfolio value"""
        max_position_size = self.config.get("max_position_size", 0.1)
        position_value = portfolio_value * max_position_size
        quantity = position_value / current_price
        return quantity


class MeanReversionStrategy(TradingStrategy):
    """Mean reversion strategy using Bollinger Bands"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.bb_period = config.get("lookback_period", 20)
        self.bb_std = config.get("bb_std", 2.0)
        self.rsi_period = config.get("rsi_period", 14)
    
    def generate_signal(self, symbol: str, prices: List[float], 
                       current_price: float) -> Signal:
        """Generate signal based on mean reversion"""
        if len(prices) < self.bb_period:
            return Signal.HOLD
        
        # Calculate Bollinger Bands
        upper_band, middle_band, lower_band = TechnicalIndicators.bollinger_bands(
            prices, self.bb_period, self.bb_std
        )
        
        # Calculate RSI for confirmation
        rsi = TechnicalIndicators.rsi(prices, self.rsi_period)
        
        # Buy signal: price below lower band and RSI oversold
        if current_price < lower_band and rsi < 30:
            return Signal.BUY
        
        # Sell signal: price above upper band and RSI overbought
        if current_price > upper_band and rsi > 70:
            return Signal.SELL
        
        return Signal.HOLD
    
    def get_position_size(self, symbol: str, portfolio_value: float, 
                         current_price: float) -> float:
        """Calculate position size based on portfolio value"""
        max_position_size = self.config.get("max_position_size", 0.1)
        position_value = portfolio_value * max_position_size
        quantity = position_value / current_price
        return quantity


class MomentumStrategy(TradingStrategy):
    """Momentum strategy using RSI and MACD"""
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.rsi_period = config.get("rsi_period", 14)
        self.macd_fast = config.get("macd_fast", 12)
        self.macd_slow = config.get("macd_slow", 26)
        self.macd_signal = config.get("macd_signal", 9)
    
    def generate_signal(self, symbol: str, prices: List[float], 
                       current_price: float) -> Signal:
        """Generate signal based on momentum indicators"""
        if len(prices) < self.macd_slow:
            return Signal.HOLD
        
        # Calculate RSI
        rsi = TechnicalIndicators.rsi(prices, self.rsi_period)
        
        # Calculate MACD
        macd_line, signal_line, histogram = TechnicalIndicators.macd(
            prices, self.macd_fast, self.macd_slow, self.macd_signal
        )
        
        # Buy signal: RSI crosses above 50 and MACD positive
        if rsi > 50 and macd_line > signal_line and histogram > 0:
            return Signal.BUY
        
        # Sell signal: RSI crosses below 50 and MACD negative
        if rsi < 50 and macd_line < signal_line and histogram < 0:
            return Signal.SELL
        
        return Signal.HOLD
    
    def get_position_size(self, symbol: str, portfolio_value: float, 
                         current_price: float) -> float:
        """Calculate position size based on portfolio value"""
        max_position_size = self.config.get("max_position_size", 0.1)
        position_value = portfolio_value * max_position_size
        quantity = position_value / current_price
        return quantity


def create_strategy(strategy_type: str, config: Dict) -> TradingStrategy:
    """Factory function to create strategy instances"""
    strategies = {
        "trend_following": TrendFollowingStrategy,
        "mean_reversion": MeanReversionStrategy,
        "momentum": MomentumStrategy,
    }
    
    strategy_class = strategies.get(strategy_type)
    if strategy_class is None:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    
    return strategy_class(config)
