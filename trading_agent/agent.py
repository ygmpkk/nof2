"""
AI-powered Trading Agent
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import numpy as np

from .config import TradingConfig
from .portfolio import Portfolio
from .data.market_data import MarketDataProvider, SimulatedMarketDataProvider
from .strategies import create_strategy, Signal, TradingStrategy


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class AIPredictor:
    """Simple AI predictor using statistical methods"""
    
    def __init__(self, confidence_threshold: float = 0.7):
        self.confidence_threshold = confidence_threshold
    
    def predict_direction(self, prices: List[float]) -> tuple[str, float]:
        """
        Predict price direction using simple statistical analysis
        Returns: (direction, confidence)
        """
        if len(prices) < 10:
            return "HOLD", 0.0
        
        # Calculate recent trend
        recent_prices = prices[-10:]
        trend = np.polyfit(range(len(recent_prices)), recent_prices, 1)[0]
        
        # Calculate volatility
        volatility = np.std(recent_prices) / np.mean(recent_prices)
        
        # Calculate momentum
        momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Simple prediction logic
        if trend > 0 and momentum > 0.01:
            confidence = min(0.5 + abs(momentum) * 10, 0.95)
            return "UP", confidence
        elif trend < 0 and momentum < -0.01:
            confidence = min(0.5 + abs(momentum) * 10, 0.95)
            return "DOWN", confidence
        else:
            return "HOLD", 0.3
    
    def should_trade(self, prices: List[float]) -> bool:
        """Determine if we should trade based on AI prediction"""
        direction, confidence = self.predict_direction(prices)
        return confidence >= self.confidence_threshold


class TradingAgent:
    """Main AI Trading Agent"""
    
    def __init__(self, config: Optional[TradingConfig] = None, 
                 data_provider: Optional[MarketDataProvider] = None):
        """Initialize the trading agent"""
        self.config = config or TradingConfig()
        self.portfolio = Portfolio(initial_capital=self.config.initial_capital)
        self.data_provider = data_provider or SimulatedMarketDataProvider()
        self.strategy = create_strategy(self.config.strategy_type, self.config.to_dict())
        self.ai_predictor = AIPredictor(confidence_threshold=self.config.confidence_threshold)
        self.logger = logging.getLogger(__name__)
        self.trade_count = 0
        self.start_time = datetime.now()
    
    def _get_historical_prices(self, symbol: str) -> List[float]:
        """Get historical prices for analysis"""
        historical_data = self.data_provider.get_historical_data(
            symbol, self.config.lookback_period
        )
        return [data.close for data in historical_data]
    
    def _calculate_stop_loss(self, entry_price: float, is_long: bool) -> float:
        """Calculate stop loss price"""
        if is_long:
            return entry_price * (1 - self.config.stop_loss_pct)
        else:
            return entry_price * (1 + self.config.stop_loss_pct)
    
    def _calculate_take_profit(self, entry_price: float, is_long: bool) -> float:
        """Calculate take profit price"""
        if is_long:
            return entry_price * (1 + self.config.take_profit_pct)
        else:
            return entry_price * (1 - self.config.take_profit_pct)
    
    def _check_risk_management(self, symbol: str, current_price: float) -> bool:
        """Check if position should be closed due to risk management rules"""
        position = self.portfolio.get_position(symbol)
        if position is None:
            return False
        
        # Check stop loss
        if position.stop_loss and current_price <= position.stop_loss:
            self.logger.warning(f"Stop loss triggered for {symbol} at {current_price}")
            return True
        
        # Check take profit
        if position.take_profit and current_price >= position.take_profit:
            self.logger.info(f"Take profit triggered for {symbol} at {current_price}")
            return True
        
        # Check max drawdown
        if position.pnl_pct < -self.config.max_drawdown_pct * 100:
            self.logger.warning(f"Max drawdown exceeded for {symbol}")
            return True
        
        return False
    
    def _should_open_position(self, symbol: str, signal: Signal, 
                             prices: List[float]) -> bool:
        """Determine if we should open a new position"""
        if signal != Signal.BUY:
            return False
        
        # Check if we already have a position
        if self.portfolio.has_position(symbol):
            return False
        
        # Check AI prediction if enabled
        if self.config.use_ai_predictions:
            if not self.ai_predictor.should_trade(prices):
                self.logger.debug(f"AI predictor suggests not to trade {symbol}")
                return False
            
            direction, confidence = self.ai_predictor.predict_direction(prices)
            if direction != "UP":
                return False
            
            self.logger.info(f"AI prediction for {symbol}: {direction} (confidence: {confidence:.2f})")
        
        return True
    
    def _should_close_position(self, symbol: str, signal: Signal, 
                              current_price: float) -> bool:
        """Determine if we should close an existing position"""
        if not self.portfolio.has_position(symbol):
            return False
        
        # Check risk management rules first
        if self._check_risk_management(symbol, current_price):
            return True
        
        # Check strategy signal
        if signal == Signal.SELL:
            return True
        
        return False
    
    def process_symbol(self, symbol: str):
        """Process trading logic for a single symbol"""
        try:
            # Get current price and historical data
            current_price = self.data_provider.get_latest_price(symbol)
            prices = self._get_historical_prices(symbol)
            
            # Update position prices
            self.portfolio.update_prices({symbol: current_price})
            
            # Generate trading signal
            signal = self.strategy.generate_signal(symbol, prices, current_price)
            
            self.logger.debug(f"{symbol}: Price={current_price:.2f}, Signal={signal.value}")
            
            # Check if we should close existing position
            if self._should_close_position(symbol, signal, current_price):
                if self.portfolio.close_position(symbol, current_price):
                    self.trade_count += 1
                    self.logger.info(f"Closed position: {symbol} at {current_price:.2f}")
            
            # Check if we should open new position
            elif self._should_open_position(symbol, signal, prices):
                quantity = self.strategy.get_position_size(
                    symbol, self.portfolio.total_value, current_price
                )
                
                if quantity > 0:
                    stop_loss = self._calculate_stop_loss(current_price, is_long=True)
                    take_profit = self._calculate_take_profit(current_price, is_long=True)
                    
                    if self.portfolio.open_position(symbol, quantity, current_price, 
                                                   stop_loss, take_profit):
                        self.trade_count += 1
                        self.logger.info(
                            f"Opened position: {symbol} at {current_price:.2f}, "
                            f"quantity={quantity:.2f}, SL={stop_loss:.2f}, TP={take_profit:.2f}"
                        )
        
        except Exception as e:
            self.logger.error(f"Error processing {symbol}: {str(e)}")
    
    def run_step(self):
        """Run one step of the trading agent"""
        self.logger.info(f"=== Trading Step {self.trade_count} ===")
        
        # Process each symbol
        for symbol in self.config.symbols:
            self.process_symbol(symbol)
        
        # Log portfolio status
        summary = self.portfolio.get_summary()
        self.logger.info(
            f"Portfolio: Value=${summary['total_value']:.2f}, "
            f"Cash=${summary['cash']:.2f}, "
            f"P&L={summary['total_pnl']:.2f} ({summary['total_pnl_pct']:.2f}%), "
            f"Positions={summary['num_positions']}"
        )
    
    def run(self, steps: int = 100):
        """Run the trading agent for a number of steps"""
        self.logger.info(f"Starting trading agent with {len(self.config.symbols)} symbols")
        self.logger.info(f"Strategy: {self.config.strategy_type}")
        self.logger.info(f"Initial capital: ${self.config.initial_capital:.2f}")
        
        for step in range(steps):
            self.run_step()
            
            # Advance market simulation if using simulated data
            if isinstance(self.data_provider, SimulatedMarketDataProvider):
                self.data_provider.advance_time()
        
        # Final report
        self.logger.info("=== Trading Session Complete ===")
        final_summary = self.portfolio.get_summary()
        self.logger.info(f"Final Portfolio Value: ${final_summary['total_value']:.2f}")
        self.logger.info(f"Total P&L: ${final_summary['total_pnl']:.2f} ({final_summary['total_pnl_pct']:.2f}%)")
        self.logger.info(f"Total Trades: {self.trade_count}")
        self.logger.info(f"Final Cash: ${final_summary['cash']:.2f}")
        self.logger.info(f"Open Positions: {final_summary['num_positions']}")
        
        return final_summary
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        return self.portfolio.get_summary()
