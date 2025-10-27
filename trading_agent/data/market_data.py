"""
Market data handling and simulation
"""

import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class MarketData:
    """Market data point"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


class MarketDataProvider:
    """Base class for market data providers"""
    
    def get_latest_price(self, symbol: str) -> float:
        """Get latest price for a symbol"""
        raise NotImplementedError
    
    def get_historical_data(self, symbol: str, periods: int) -> List[MarketData]:
        """Get historical data"""
        raise NotImplementedError
    
    def get_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get latest prices for multiple symbols"""
        return {symbol: self.get_latest_price(symbol) for symbol in symbols}


class SimulatedMarketDataProvider(MarketDataProvider):
    """Simulated market data for testing"""
    
    def __init__(self, initial_price: float = 100.0, volatility: float = 0.02):
        self.initial_price = initial_price
        self.volatility = volatility
        self.current_prices: Dict[str, float] = {}
        self.historical_data: Dict[str, List[MarketData]] = {}
        self.time_step = 0
        np.random.seed(42)  # For reproducibility
    
    def get_latest_price(self, symbol: str) -> float:
        """Get simulated latest price"""
        if symbol not in self.current_prices:
            self.current_prices[symbol] = self.initial_price
        
        # Simulate price movement using geometric Brownian motion
        current_price = self.current_prices[symbol]
        drift = 0.0001  # Small positive drift
        shock = np.random.normal(0, self.volatility)
        new_price = current_price * (1 + drift + shock)
        
        # Ensure price stays positive
        new_price = max(new_price, 0.01)
        self.current_prices[symbol] = new_price
        
        return new_price
    
    def get_historical_data(self, symbol: str, periods: int) -> List[MarketData]:
        """Generate simulated historical data"""
        if symbol not in self.historical_data:
            self.historical_data[symbol] = []
        
        # Generate historical data if needed
        while len(self.historical_data[symbol]) < periods:
            timestamp = datetime.now() - timedelta(days=periods - len(self.historical_data[symbol]))
            
            if len(self.historical_data[symbol]) == 0:
                price = self.initial_price
            else:
                last_close = self.historical_data[symbol][-1].close
                drift = 0.0001
                shock = np.random.normal(0, self.volatility)
                price = last_close * (1 + drift + shock)
                price = max(price, 0.01)
            
            # Generate OHLC data
            daily_volatility = self.volatility * 0.5
            open_price = price * (1 + np.random.normal(0, daily_volatility))
            close_price = price * (1 + np.random.normal(0, daily_volatility))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, daily_volatility)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, daily_volatility)))
            volume = np.random.randint(1000000, 10000000)
            
            data_point = MarketData(
                symbol=symbol,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume
            )
            self.historical_data[symbol].append(data_point)
        
        return self.historical_data[symbol][-periods:]
    
    def advance_time(self):
        """Advance simulation time"""
        self.time_step += 1
        # Update all current prices
        for symbol in list(self.current_prices.keys()):
            self.get_latest_price(symbol)


class TechnicalIndicators:
    """Calculate technical indicators"""
    
    @staticmethod
    def moving_average(prices: List[float], period: int) -> float:
        """Calculate simple moving average"""
        if len(prices) < period:
            return np.mean(prices)
        return np.mean(prices[-period:])
    
    @staticmethod
    def exponential_moving_average(prices: List[float], period: int) -> float:
        """Calculate exponential moving average"""
        if len(prices) < period:
            return np.mean(prices)
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> tuple:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            ma = np.mean(prices)
            std = np.std(prices)
        else:
            ma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
        
        upper_band = ma + (num_std * std)
        lower_band = ma - (num_std * std)
        
        return upper_band, ma, lower_band
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """Calculate MACD"""
        if len(prices) < slow:
            return 0.0, 0.0, 0.0
        
        ema_fast = TechnicalIndicators.exponential_moving_average(prices, fast)
        ema_slow = TechnicalIndicators.exponential_moving_average(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Simplified signal line calculation
        signal_line = macd_line * 0.9  # Approximation
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
