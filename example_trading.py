"""
Example usage of the AI Trading Agent
"""

from trading_agent import (
    TradingAgent,
    TrendFollowingStrategy,
    MeanReversionStrategy,
    PydanticAutoTradingAgent,
)
from trading_agent.config import TradingConfig
from trading_agent.data import SimulatedMarketDataProvider


def example_trend_following():
    """Example using trend following strategy"""
    print("=" * 60)
    print("AI Trading Agent - Trend Following Strategy")
    print("=" * 60)
    
    # Configure the agent
    config = TradingConfig(
        initial_capital=100000.0,
        strategy_type="trend_following",
        symbols=["AAPL", "GOOGL", "MSFT", "AMZN"],
        lookback_period=20,
        max_position_size=0.15,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
        use_ai_predictions=True,
        confidence_threshold=0.7,
    )
    
    # Create market data provider
    data_provider = SimulatedMarketDataProvider(
        initial_price=150.0,
        volatility=0.02
    )
    
    # Create and run the agent
    agent = TradingAgent(config=config, data_provider=data_provider)
    final_summary = agent.run(steps=100)
    
    print("\n" + "=" * 60)
    print("Final Results:")
    print("=" * 60)
    print(f"Starting Capital: ${config.initial_capital:,.2f}")
    print(f"Ending Value: ${final_summary['total_value']:,.2f}")
    print(f"Total Return: ${final_summary['total_pnl']:,.2f} ({final_summary['total_pnl_pct']:.2f}%)")
    print(f"Number of Trades: {agent.trade_count}")
    print(f"Final Cash: ${final_summary['cash']:,.2f}")
    print(f"Open Positions: {final_summary['num_positions']}")


def example_mean_reversion():
    """Example using mean reversion strategy"""
    print("\n" + "=" * 60)
    print("AI Trading Agent - Mean Reversion Strategy")
    print("=" * 60)
    
    # Configure the agent
    config = TradingConfig(
        initial_capital=100000.0,
        strategy_type="mean_reversion",
        symbols=["AAPL", "GOOGL"],
        lookback_period=20,
        max_position_size=0.2,
        stop_loss_pct=0.03,
        take_profit_pct=0.08,
        use_ai_predictions=True,
        confidence_threshold=0.65,
    )
    
    # Create market data provider with higher volatility for mean reversion
    data_provider = SimulatedMarketDataProvider(
        initial_price=200.0,
        volatility=0.03
    )
    
    # Create and run the agent
    agent = TradingAgent(config=config, data_provider=data_provider)
    final_summary = agent.run(steps=100)
    
    print("\n" + "=" * 60)
    print("Final Results:")
    print("=" * 60)
    print(f"Starting Capital: ${config.initial_capital:,.2f}")
    print(f"Ending Value: ${final_summary['total_value']:,.2f}")
    print(f"Total Return: ${final_summary['total_pnl']:,.2f} ({final_summary['total_pnl_pct']:.2f}%)")
    print(f"Number of Trades: {agent.trade_count}")
    print(f"Final Cash: ${final_summary['cash']:,.2f}")
    print(f"Open Positions: {final_summary['num_positions']}")


def example_momentum():
    """Example using momentum strategy"""
    print("\n" + "=" * 60)
    print("AI Trading Agent - Momentum Strategy")
    print("=" * 60)
    
    # Configure the agent
    config = TradingConfig(
        initial_capital=100000.0,
        strategy_type="momentum",
        symbols=["AAPL", "MSFT", "TSLA"],
        lookback_period=30,
        max_position_size=0.12,
        stop_loss_pct=0.04,
        take_profit_pct=0.12,
        use_ai_predictions=True,
        confidence_threshold=0.75,
    )
    
    # Create market data provider
    data_provider = SimulatedMarketDataProvider(
        initial_price=180.0,
        volatility=0.025
    )
    
    # Create and run the agent
    agent = TradingAgent(config=config, data_provider=data_provider)
    final_summary = agent.run(steps=100)
    
    print("\n" + "=" * 60)
    print("Final Results:")
    print("=" * 60)
    print(f"Starting Capital: ${config.initial_capital:,.2f}")
    print(f"Ending Value: ${final_summary['total_value']:,.2f}")
    print(f"Total Return: ${final_summary['total_pnl']:,.2f} ({final_summary['total_pnl_pct']:.2f}%)")
    print(f"Number of Trades: {agent.trade_count}")
    print(f"Final Cash: ${final_summary['cash']:,.2f}")
    print(f"Open Positions: {final_summary['num_positions']}")



def example_pydantic_auto_trader():
    """Example showcasing the Pydantic AI auto-trading agent."""
    print("\n" + "=" * 60)
    print("Pydantic AI Structured Trading Agent")
    print("=" * 60)

    config = TradingConfig(
        initial_capital=75000.0,
        strategy_type="trend_following",
        symbols=["AAPL", "GOOGL", "MSFT"],
        lookback_period=30,
        max_position_size=0.12,
        stop_loss_pct=0.04,
        take_profit_pct=0.09,
        use_ai_predictions=False,
    )

    data_provider = SimulatedMarketDataProvider(
        initial_price=160.0,
        volatility=0.02,
    )

    agent = PydanticAutoTradingAgent(config=config, data_provider=data_provider)
    final_summary = agent.run(steps=60)

    print("\n" + "=" * 60)
    print("Final Results:")
    print("=" * 60)
    print(f"Starting Capital: ${config.initial_capital:,.2f}")
    print(f"Ending Value: ${final_summary['total_value']:,.2f}")
    print(f"Total Return: ${final_summary['total_pnl']:,.2f} ({final_summary['total_pnl_pct']:.2f}%)")
    print(f"Number of Trades: {agent.trade_count}")
    print(f"Final Cash: ${final_summary['cash']:,.2f}")
    print(f"Open Positions: {final_summary['num_positions']}")


if __name__ == "__main__":
    # Run all examples
    example_trend_following()
    example_mean_reversion()
    example_momentum()
    example_pydantic_auto_trader()
