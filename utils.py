import pandas as pd
import numpy as np

def calculate_performance_metrics(equity_df):
    """Calculates performance metrics from an equity curve DataFrame."""
    if equity_df.empty or len(equity_df) < 2:
        return {}
    
    equity = equity_df['equity']
    returns = equity.pct_change().dropna()
    
    # CAGR
    total_return = (equity.iloc[-1] / equity.iloc[0]) - 1
    days = (equity_df['date'].iloc[-1] - equity_df['date'].iloc[0]).days
    cagr = ((1 + total_return) ** (365 / days)) - 1 if days > 0 else 0
    
    # Sharpe Ratio
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
    
    # Max Drawdown
    cumulative_max = equity.cummax()
    drawdown = (equity - cumulative_max) / cumulative_max
    max_drawdown = drawdown.min()
    
    # Win Rate (of days)
    win_rate = (returns > 0).mean()
    
    return {
        "Total Return": f"{total_return:.2%}",
        "CAGR": f"{cagr:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Max Drawdown": f"{max_drawdown:.2%}",
        "Win Rate": f"{win_rate:.2%}"
    }

def get_monthly_returns(equity_df):
    """Calculates monthly returns for a heatmap."""
    df = equity_df.copy()
    df.set_index('date', inplace=True)
    monthly_equity = df['equity'].resample('ME').last()
    monthly_returns = monthly_equity.pct_change().fillna(0)
    
    returns_df = monthly_returns.to_frame()
    returns_df['Year'] = returns_df.index.year
    returns_df['Month'] = returns_df.index.month_name()
    
    pivot_table = returns_df.pivot_table(index='Year', columns='Month', values='equity')
    # Sort months correctly
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 
                   'July', 'August', 'September', 'October', 'November', 'December']
    pivot_table = pivot_table.reindex(columns=month_order)
    return pivot_table

def get_drawdown_series(equity_df):
    """Returns the drawdown series for plotting."""
    equity = equity_df['equity']
    cumulative_max = equity.cummax()
    drawdown = (equity - cumulative_max) / cumulative_max
    return pd.DataFrame({'date': equity_df['date'], 'drawdown': drawdown})
