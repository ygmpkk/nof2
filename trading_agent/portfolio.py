"""
Portfolio management for tracking positions and performance
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    @property
    def market_value(self) -> float:
        """Current market value of the position"""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> float:
        """Cost basis of the position"""
        return self.quantity * self.entry_price
    
    @property
    def pnl(self) -> float:
        """Profit and loss"""
        return self.market_value - self.cost_basis
    
    @property
    def pnl_pct(self) -> float:
        """Profit and loss percentage"""
        if self.cost_basis == 0:
            return 0.0
        return (self.pnl / self.cost_basis) * 100
    
    def update_price(self, price: float):
        """Update current price"""
        self.current_price = price


@dataclass
class Portfolio:
    """Portfolio management class"""
    initial_capital: float
    cash: float = field(init=False)
    positions: Dict[str, Position] = field(default_factory=dict)
    trade_history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        self.cash = self.initial_capital
    
    @property
    def total_value(self) -> float:
        """Total portfolio value"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + positions_value
    
    @property
    def total_pnl(self) -> float:
        """Total profit and loss"""
        return self.total_value - self.initial_capital
    
    @property
    def total_pnl_pct(self) -> float:
        """Total profit and loss percentage"""
        if self.initial_capital == 0:
            return 0.0
        return (self.total_pnl / self.initial_capital) * 100
    
    @property
    def positions_value(self) -> float:
        """Total value of all positions"""
        return sum(pos.market_value for pos in self.positions.values())
    
    def can_open_position(self, symbol: str, quantity: float, price: float) -> bool:
        """Check if we can open a new position"""
        cost = quantity * price
        return cost <= self.cash and symbol not in self.positions
    
    def open_position(self, symbol: str, quantity: float, price: float, 
                     stop_loss: Optional[float] = None, 
                     take_profit: Optional[float] = None) -> bool:
        """Open a new position"""
        cost = quantity * price
        
        if not self.can_open_position(symbol, quantity, price):
            return False
        
        self.cash -= cost
        self.positions[symbol] = Position(
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            entry_time=datetime.now(),
            current_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        # Record trade
        self.trade_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "BUY",
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "cost": cost,
        })
        
        return True
    
    def close_position(self, symbol: str, price: float) -> bool:
        """Close an existing position"""
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        proceeds = position.quantity * price
        self.cash += proceeds
        
        # Record trade
        self.trade_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": "SELL",
            "symbol": symbol,
            "quantity": position.quantity,
            "price": price,
            "proceeds": proceeds,
            "pnl": position.pnl,
            "pnl_pct": position.pnl_pct,
        })
        
        del self.positions[symbol]
        return True
    
    def update_prices(self, prices: Dict[str, float]):
        """Update prices for all positions"""
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        return self.positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if we have a position in a symbol"""
        return symbol in self.positions
    
    def get_summary(self) -> Dict:
        """Get portfolio summary"""
        return {
            "total_value": self.total_value,
            "cash": self.cash,
            "positions_value": self.positions_value,
            "total_pnl": self.total_pnl,
            "total_pnl_pct": self.total_pnl_pct,
            "num_positions": len(self.positions),
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "market_value": pos.market_value,
                    "pnl": pos.pnl,
                    "pnl_pct": pos.pnl_pct,
                }
                for symbol, pos in self.positions.items()
            }
        }
    
    def to_json(self) -> str:
        """Convert portfolio to JSON"""
        return json.dumps(self.get_summary(), indent=2)
