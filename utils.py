import pandas as pd
import numpy as np

def calculate_performance_metrics(equity_df):
    """Calculates performance metrics from an equity curve DataFrame."""
    if equity_df.empty:
        return {}
    
    equity = equity_df['equity']
    returns = equity.pct_change().dropna()
    
    # CAGR
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
    days = (equity_df['date'].iloc[-1] - equity_df['date'].iloc[0]).days
    cagr = ((1 + total_return) ** (365 / days)) - 1 if days > 0 else 0
    
    # Sharpe Ratio (assuming 0 risk-free rate for simplicity)
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    # Max Drawdown
    cumulative_max = equity.cummax()
    drawdown = (equity - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()
    
    # Volatility (Annualized)
    volatility = returns.std() * np.sqrt(252)
    
    return {
        "Total Return": f"{total_return:.2%}",
        "CAGR": f"{cagr:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Max Drawdown": f"{max_drawdown:.2%}",
        "Volatility": f"{volatility:.2%}"
    }

def get_drawdown_series(equity_df):
    """Returns the drawdown series for plotting."""
    equity = equity_df['equity']
    cumulative_max = equity.cummax()
    drawdown = (equity - cumulative_max) / cumulative_max
    return pd.DataFrame({'date': equity_df['date'], 'drawdown': drawdown})
