# AI Agent Auto Trading System

An advanced AI-powered automated trading system implemented in Python, featuring multiple trading strategies, risk management, and portfolio optimization.

## Features

### Core Components

1. **Trading Agent** - Main AI agent that orchestrates trading operations
   - Configurable trading strategies
   - AI-powered decision making
   - Risk management integration
   - Real-time portfolio tracking

2. **Trading Strategies**
   - **Trend Following**: Uses moving average crossovers to identify and follow market trends
   - **Mean Reversion**: Utilizes Bollinger Bands and RSI to trade oversold/overbought conditions
   - **Momentum**: Combines RSI and MACD indicators for momentum-based trading

3. **Portfolio Management**
   - Real-time position tracking
   - Profit & Loss calculation
   - Trade history logging
   - Cash and position value monitoring

4. **Risk Management**
   - Stop-loss orders
   - Take-profit targets
   - Maximum drawdown protection
   - Position sizing based on portfolio value

5. **Market Data Provider**
   - Simulated market data for testing
   - Technical indicators (MA, EMA, RSI, Bollinger Bands, MACD)
   - Historical data management

6. **AI Predictor**
   - Statistical analysis for price prediction
   - Confidence scoring
   - Trend and momentum detection

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```python
from trading_agent import TradingAgent
from trading_agent.config import TradingConfig
from trading_agent.data import SimulatedMarketDataProvider

# Configure the trading agent
config = TradingConfig(
    initial_capital=100000.0,
    strategy_type="trend_following",
    symbols=["AAPL", "GOOGL", "MSFT", "AMZN"],
    lookback_period=20,
    max_position_size=0.15,
    stop_loss_pct=0.05,
    take_profit_pct=0.10,
    use_ai_predictions=True,
)

# Create market data provider
data_provider = SimulatedMarketDataProvider(
    initial_price=150.0,
    volatility=0.02
)

# Initialize and run the agent
agent = TradingAgent(config=config, data_provider=data_provider)
results = agent.run(steps=100)

# View results
print(f"Total Return: {results['total_pnl_pct']:.2f}%")
```

### Run Examples

```bash
python example_trading.py
```

This will run three different strategies:
1. Trend Following Strategy
2. Mean Reversion Strategy
3. Momentum Strategy

## Configuration Options

### TradingConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `initial_capital` | float | 100000.0 | Starting capital |
| `max_position_size` | float | 0.1 | Max position as % of portfolio |
| `max_portfolio_risk` | float | 0.02 | Max risk per trade (2%) |
| `strategy_type` | str | "trend_following" | Strategy to use |
| `lookback_period` | int | 20 | Historical data lookback |
| `entry_threshold` | float | 0.02 | Entry signal threshold |
| `stop_loss_pct` | float | 0.05 | Stop loss percentage |
| `take_profit_pct` | float | 0.10 | Take profit percentage |
| `max_drawdown_pct` | float | 0.20 | Maximum drawdown allowed |
| `use_ai_predictions` | bool | True | Enable AI predictions |
| `confidence_threshold` | float | 0.7 | Min confidence for trades |

## Architecture

```
trading_agent/
├── __init__.py           # Package initialization
├── agent.py              # Main trading agent
├── config.py             # Configuration management
├── portfolio.py          # Portfolio management
├── data/
│   ├── __init__.py
│   └── market_data.py    # Market data and indicators
├── strategies/
│   └── __init__.py       # Trading strategies
└── tests/
    └── test_agent.py     # Unit tests
```

## Trading Strategies

### 1. Trend Following

Uses moving average crossovers to identify trends:
- **Buy Signal**: Short MA crosses above Long MA
- **Sell Signal**: Short MA crosses below Long MA
- Best for trending markets

### 2. Mean Reversion

Uses Bollinger Bands and RSI:
- **Buy Signal**: Price below lower band + RSI < 30 (oversold)
- **Sell Signal**: Price above upper band + RSI > 70 (overbought)
- Best for range-bound markets

### 3. Momentum

Combines RSI and MACD indicators:
- **Buy Signal**: RSI > 50 + MACD bullish crossover
- **Sell Signal**: RSI < 50 + MACD bearish crossover
- Best for strong trending markets

## Risk Management

The system includes comprehensive risk management:

1. **Position Sizing**: Limits each position to a % of portfolio
2. **Stop Loss**: Automatic exit at predetermined loss level
3. **Take Profit**: Automatic exit at profit target
4. **Max Drawdown**: Closes positions if losses exceed threshold
5. **Portfolio Limits**: Prevents over-leveraging

## Technical Indicators

- **Moving Average (MA)**: Trend identification
- **Exponential Moving Average (EMA)**: Weighted trend analysis
- **Relative Strength Index (RSI)**: Overbought/oversold conditions
- **Bollinger Bands**: Volatility and price range
- **MACD**: Momentum and trend strength

## AI Predictions

The AI predictor uses statistical methods to:
- Analyze price trends
- Calculate momentum
- Estimate volatility
- Generate confidence scores
- Make trade recommendations

## Testing

Run the test suite:

```bash
python -m pytest trading_agent/tests/
```

Or run individual tests:

```bash
python trading_agent/tests/test_agent.py
```

## Performance Monitoring

The system logs detailed information:
- Trade entries and exits
- Price movements
- Portfolio value changes
- P&L tracking
- Risk management triggers

## Example Output

```
=== Trading Step 0 ===
Opened position: AAPL at 150.23, quantity=100.00, SL=142.72, TP=165.25
Portfolio: Value=$100000.00, Cash=$84977.00, P&L=0.00 (0.00%), Positions=1

=== Trading Step 50 ===
Closed position: AAPL at 165.50
Portfolio: Value=$105527.00, Cash=$105527.00, P&L=5527.00 (5.53%), Positions=0

=== Trading Session Complete ===
Final Portfolio Value: $108,523.50
Total P&L: $8,523.50 (8.52%)
Total Trades: 15
```

## Customization

### Create a Custom Strategy

```python
from trading_agent.strategies import TradingStrategy, Signal

class MyCustomStrategy(TradingStrategy):
    def generate_signal(self, symbol, prices, current_price):
        # Your strategy logic here
        if your_buy_condition:
            return Signal.BUY
        elif your_sell_condition:
            return Signal.SELL
        return Signal.HOLD
    
    def get_position_size(self, symbol, portfolio_value, current_price):
        # Your position sizing logic
        return quantity
```

## Best Practices

1. **Start with simulation**: Test strategies with simulated data first
2. **Adjust risk parameters**: Tune stop-loss and position sizes
3. **Monitor performance**: Track metrics and adjust strategy
4. **Diversify**: Trade multiple symbols to spread risk
5. **Use AI predictions**: Enable for better decision making

## Limitations

- This is a simulated trading system for educational purposes
- Real market conditions may differ significantly
- Past performance does not guarantee future results
- Always practice proper risk management

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is open source and available under the MIT License.

## Disclaimer

This software is for educational purposes only. It is not financial advice. Trading involves risk and may result in loss of capital. Always do your own research and consult with financial professionals before trading.
