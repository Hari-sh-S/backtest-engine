import pandas as pd
import numpy as np
import ta

class IndicatorLibrary:
    @staticmethod
    def calculate_sma(df, window, column='Close'):
        return ta.trend.sma_indicator(df[column], window=window)

    @staticmethod
    def calculate_ema(df, window, column='Close'):
        return ta.trend.ema_indicator(df[column], window=window)

    @staticmethod
    def calculate_rsi(df, window=14, column='Close'):
        return ta.momentum.rsi(df[column], window=window)

    @staticmethod
    def calculate_macd(df, window_slow=26, window_fast=12, window_sign=9, column='Close'):
        macd = ta.trend.MACD(df[column], window_slow=window_slow, window_fast=window_fast, window_sign=window_sign)
        return macd.macd(), macd.macd_signal(), macd.macd_diff()

    @staticmethod
    def calculate_momentum_metrics(df, window=21):
        """Calculates performance, volatility, and distance metrics."""
        close = df['Close']
        returns = close.pct_change()
        
        metrics = {}
        metrics['performance'] = close.pct_change(periods=window)
        metrics['volatility'] = returns.rolling(window).std() * np.sqrt(252)
        metrics['max_drawdown'] = (close / close.rolling(window).max() - 1).rolling(window).min()
        metrics['distance_from_sma200'] = (close - close.rolling(200).mean()) / close.rolling(200).mean() * 100
        
        return metrics

def get_indicator_value(df, indicator_type, params):
    """Helper to calculate any indicator based on type and parameters."""
    lib = IndicatorLibrary()
    if indicator_type == "SMA":
        return lib.calculate_sma(df, params.get('window', 50))
    elif indicator_type == "EMA":
        return lib.calculate_ema(df, params.get('window', 20))
    elif indicator_type == "RSI":
        return lib.calculate_rsi(df, params.get('window', 14))
    elif indicator_type == "MACD":
        m, s, d = lib.calculate_macd(df)
        return m # Return main MACD line by default
    elif indicator_type == "Momentum":
        return lib.calculate_momentum_metrics(df, params.get('window', 21))['performance']
    return None
