"""
Configuration management for the trading agent
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class TradingConfig:
    """Configuration for trading agent"""
    
    # Portfolio settings
    initial_capital: float = 100000.0
    max_position_size: float = 0.1  # Maximum 10% of portfolio per position
    max_portfolio_risk: float = 0.02  # Maximum 2% risk per trade
    
    # Strategy settings
    strategy_type: str = "trend_following"  # or "mean_reversion"
    lookback_period: int = 20
    entry_threshold: float = 0.02  # 2% price movement threshold
    exit_threshold: float = 0.01  # 1% exit threshold
    
    # Risk management
    stop_loss_pct: float = 0.05  # 5% stop loss
    take_profit_pct: float = 0.10  # 10% take profit
    max_drawdown_pct: float = 0.20  # 20% max drawdown
    
    # Data settings
    data_source: str = "simulation"  # or "binance", "historical"
    symbols: list = None

    # Binance integration settings
    binance_api_key: Optional[str] = None
    binance_api_secret: Optional[str] = None
    binance_testnet: bool = True
    binance_interval: str = "1h"

    # Execution settings
    enable_live_trading: bool = False
    
    # AI settings
    use_ai_predictions: bool = True
    confidence_threshold: float = 0.7
    
    def __post_init__(self):
        if self.symbols is None:
            self.symbols = ["AAPL", "GOOGL", "MSFT", "AMZN"]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "initial_capital": self.initial_capital,
            "max_position_size": self.max_position_size,
            "max_portfolio_risk": self.max_portfolio_risk,
            "strategy_type": self.strategy_type,
            "lookback_period": self.lookback_period,
            "entry_threshold": self.entry_threshold,
            "exit_threshold": self.exit_threshold,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "max_drawdown_pct": self.max_drawdown_pct,
            "data_source": self.data_source,
            "symbols": self.symbols,
            "binance_api_key": self.binance_api_key,
            "binance_api_secret": self.binance_api_secret,
            "binance_testnet": self.binance_testnet,
            "binance_interval": self.binance_interval,
            "enable_live_trading": self.enable_live_trading,
            "use_ai_predictions": self.use_ai_predictions,
            "confidence_threshold": self.confidence_threshold,
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'TradingConfig':
        """Create config from dictionary"""
        return cls(**config_dict)
