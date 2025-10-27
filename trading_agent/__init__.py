"""
AI Agent Auto Trading System
A comprehensive AI-powered trading agent implementation
"""

__version__ = "1.0.0"
__author__ = "nof2 AI"

from .agent import TradingAgent
from .strategies import TrendFollowingStrategy, MeanReversionStrategy
from .portfolio import Portfolio

__all__ = [
    "TradingAgent",
    "TrendFollowingStrategy",
    "MeanReversionStrategy",
    "Portfolio",
]
