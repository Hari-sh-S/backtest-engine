import pandas as pd
import numpy as np
from datetime import datetime

class BacktestEngine:
    def __init__(self, tickers, data, indicators, initial_capital=1000000, max_positions=20, stop_loss_pct=0.15):
        self.tickers = tickers
        self.data = data  # Combined price data
        self.indicators = indicators
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.stop_loss_pct = stop_loss_pct
        
        # Portfolio state
        self.cash = initial_capital
        self.positions = {}  # {ticker: {'units': n, 'entry_price': p, 'trailing_stop': s}}
        self.equity_curve = []
        self.trades = []
        
    def run(self):
        dates = self.data.index
        
        for date in dates:
            # 1. Update Portfolio Value
            portfolio_value = self.cash
            current_prices = self.data.loc[date]
            
            # Remove positions that hit stop loss or exit signal
            to_remove = []
            for ticker, pos in self.positions.items():
                current_price = current_prices[ticker]
                if pd.isna(current_price): continue
                
                # Update trailing stop (high water mark)
                new_stop = current_price * (1 - self.stop_loss_pct)
                pos['trailing_stop'] = max(pos['trailing_stop'], new_stop)
                
                # Check Stop Loss (Trailing or SMA200)
                sma200 = self.indicators['sma_slow'].loc[date, ticker]
                exit_signal = self.indicators['trend_break'].loc[date, ticker]
                
                if current_price < pos['trailing_stop'] or current_price < sma200 or exit_signal:
                    # SELL
                    self.cash += pos['units'] * current_price
                    self.trades.append({
                        'ticker': ticker,
                        'exit_date': date,
                        'exit_price': current_price,
                        'entry_price': pos['entry_price'],
                        'units': pos['units'],
                        'pnl': (current_price - pos['entry_price']) * pos['units'],
                        'return': (current_price / pos['entry_price']) - 1
                    })
                    to_remove.append(ticker)
                else:
                    portfolio_value += pos['units'] * current_price
            
            for t in to_remove:
                del self.positions[t]
            
            # 2. Rebalance / New Entries
            # Get candidates in Bullish Regime
            bullish_mask = self.indicators['bullish_regime'].loc[date]
            candidates = bullish_mask[bullish_mask].index.tolist()
            
            # Filter candidates not already in portfolio
            candidates = [c for c in candidates if c not in self.positions]
            
            if candidates and len(self.positions) < self.max_positions:
                # Rank candidates by Momentum Strength
                momentum_scores = self.indicators['momentum'].loc[date, candidates]
                top_candidates = momentum_scores.sort_values(ascending=False).head(self.max_positions - len(self.positions))
                
                # Calculate target position size (Equal Weight)
                # Note: We use initial_capital / max_positions for simplicity or current equity / max_positions
                target_pos_size = portfolio_value / self.max_positions
                
                for ticker in top_candidates.index:
                    price = current_prices[ticker]
                    if pd.isna(price) or price <= 0: continue
                    
                    if self.cash >= target_pos_size:
                        units = target_pos_size // price
                        if units > 0:
                            self.cash -= units * price
                            self.positions[ticker] = {
                                'units': units,
                                'entry_price': price,
                                'trailing_stop': price * (1 - self.stop_loss_pct)
                            }
            
            self.equity_curve.append({'date': date, 'equity': portfolio_value})
            
        return pd.DataFrame(self.equity_curve), pd.DataFrame(self.trades)
