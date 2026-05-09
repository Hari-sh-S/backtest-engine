import pandas as pd
import numpy as np

def calculate_sma(df, window):
    """Calculates Simple Moving Average."""
    return df.rolling(window=window).mean()

def calculate_momentum_score(price, sma200):
    """
    Momentum Strength = (Price - SMA200) / SMA200 * 100
    Higher % indicates stronger momentum.
    """
    return (price - sma200) / sma200 * 100

def get_strategy_indicators(df, sma_fast=50, sma_slow=200):
    """
    Calculates all indicators needed for the strategy.
    Returns a dictionary of DataFrames/Series.
    """
    indicators = {}
    indicators['sma_fast'] = calculate_sma(df, sma_fast)
    indicators['sma_slow'] = calculate_sma(df, sma_slow)
    indicators['momentum'] = calculate_momentum_score(df, indicators['sma_slow'])
    
    # Entry Condition: Price > SMA50 AND SMA50 > SMA200
    indicators['bullish_regime'] = (df > indicators['sma_fast']) & (indicators['sma_fast'] > indicators['sma_slow'])
    
    # Exit Condition: Price < SMA50
    indicators['trend_break'] = (df < indicators['sma_fast'])
    
    return indicators
