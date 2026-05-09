import pandas as pd
import numpy as np

class BacktestEngine:
    def __init__(self, tickers, data, entry_signals, exit_signals, ranking_scores, 
                 initial_capital=1000000, max_positions=20,
                 sizing_mode="Equal Weight"):
        self.tickers = tickers
        self.data = data
        self.entry_signals = entry_signals  # DataFrame of booleans
        self.exit_signals = exit_signals    # DataFrame of booleans
        self.ranking_scores = ranking_scores # DataFrame of scores
        self.initial_capital = initial_capital
        self.max_positions = max_positions
        self.sizing_mode = sizing_mode
        
        self.cash = initial_capital
        self.positions = {}
        self.equity_curve = []
        self.trades = []
        
    def run(self):
        dates = self.data.index
        
        for date in dates:
            portfolio_value = self.cash
            current_prices = self.data.loc[date]
            
            # 1. Exit Logic
            to_remove = []
            for ticker, pos in self.positions.items():
                price = current_prices[ticker]
                if pd.isna(price): continue
                
                # Exit Conditions: Manual Signal
                if self.exit_signals.loc[date, ticker]:
                    self.cash += pos['units'] * price
                    self.trades.append({
                        'ticker': ticker,
                        'exit_date': date,
                        'exit_price': price,
                        'entry_price': pos['entry_price'],
                        'units': pos['units'],
                        'pnl': (price - pos['entry_price']) * pos['units'],
                        'return': (price / pos['entry_price']) - 1
                    })
                    to_remove.append(ticker)
                else:
                    portfolio_value += pos['units'] * price
            
            for t in to_remove:
                del self.positions[t]
            
            # 2. Entry Logic
            if len(self.positions) < self.max_positions:
                eligible = self.entry_signals.loc[date]
                candidates = eligible[eligible].index.tolist()
                candidates = [c for c in candidates if c not in self.positions]
                
                if candidates:
                    # Rank by manual score
                    scores = self.ranking_scores.loc[date, candidates]
                    top_candidates = scores.sort_values(ascending=False).head(self.max_positions - len(self.positions))
                    
                    for ticker in top_candidates.index:
                        price = current_prices[ticker]
                        if pd.isna(price) or price <= 0: continue
                        
                        # Position Sizing
                        if self.sizing_mode == "Equal Weight":
                            target_size = portfolio_value / self.max_positions
                        elif self.sizing_mode == "Score-Weighted":
                            # Simple normalization: score / total_score_of_top_N
                            # Actually, a better way is score / sum(top_scores) * portfolio_value
                            total_score = top_candidates.sum()
                            if total_score > 0:
                                target_size = (scores[ticker] / total_score) * portfolio_value
                            else:
                                target_size = portfolio_value / self.max_positions
                        else:
                            target_size = portfolio_value / self.max_positions
                            
                        if self.cash >= target_size:
                            units = target_size // price
                            if units > 0:
                                self.cash -= units * price
                                self.positions[ticker] = {
                                    'units': units,
                                    'entry_price': price
                                }
            
            self.equity_curve.append({'date': date, 'equity': portfolio_value})
            
        return pd.DataFrame(self.equity_curve), pd.DataFrame(self.trades)
