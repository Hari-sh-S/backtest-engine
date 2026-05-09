import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import data_fetcher
import indicators
import backtest_engine
import utils
import nifty_universe
import re

# Page Config
st.set_page_config(page_title="Advanced Strategy Builder", layout="wide")

st.title("🛡️ Advanced Trend Following Dashboard")
st.markdown("---")

# Sidebar - Universe & Dates
st.sidebar.title("🌍 Core Settings")
all_universes = nifty_universe.get_all_universes()
selected_universe_display = st.sidebar.selectbox("Universe", list(all_universes.values()), index=4)
selected_universe_key = [k for k, v in all_universes.items() if v == selected_universe_display][0]

start_date = st.sidebar.date_input("Backtest Start", datetime(2023, 1, 1))
end_date = st.sidebar.date_input("Backtest End", datetime.now())

# Main Area - Strategy Builder
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Define Indicators")
    if 'indicators' not in st.session_state:
        st.session_state.indicators = [
            {'type': 'SMA', 'period': 50, 'alias': 'SMA_Fast'},
            {'type': 'SMA', 'period': 200, 'alias': 'SMA_Slow'}
        ]

    for i, ind in enumerate(st.session_state.indicators):
        with st.expander(f"Indicator {i+1}: {ind['alias']}", expanded=True):
            c1, c2, c3 = st.columns(3)
            ind['type'] = c1.selectbox("Type", ["SMA", "EMA", "RSI", "MACD", "Momentum"], key=f"type_{i}", index=["SMA", "EMA", "RSI", "MACD", "Momentum"].index(ind['type']))
            ind['period'] = c2.number_input("Period", value=ind['period'], key=f"period_{i}")
            ind['alias'] = c3.text_input("Alias (for formula)", value=ind['alias'], key=f"alias_{i}")

    if st.button("➕ Add Indicator"):
        st.session_state.indicators.append({'type': 'SMA', 'period': 20, 'alias': f'Ind_{len(st.session_state.indicators)}'})
        st.rerun()

with col2:
    st.subheader("2. Signals & Ranking")
    entry_formula = st.text_input("Entry Signal (e.g. Price > SMA_Fast and SMA_Fast > SMA_Slow)", "Price > SMA_Fast and SMA_Fast > SMA_Slow")
    exit_formula = st.text_input("Exit Signal (e.g. Price < SMA_Fast)", "Price < SMA_Fast")
    ranking_formula = st.text_input("Ranking Score (e.g. (Price - SMA_Slow)/SMA_Slow)", "(Price - SMA_Slow) / SMA_Slow")
    
    st.subheader("3. Risk & Sizing")
    sizing_mode = st.selectbox("Position Sizing", ["Equal Weight", "Score-Weighted"])
    max_positions = st.slider("Max Positions", 5, 50, 20)
    initial_cap = st.number_input("Capital (₹)", value=1000000)

st.markdown("---")

if st.button("🚀 Run Advanced Backtest", use_container_width=True):
    with st.spinner("Processing Strategy..."):
        # 1. Fetch Data
        tickers = nifty_universe.get_universe_tickers(selected_universe_key)
        data = data_fetcher.get_combined_data(tickers, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        if data.empty:
            st.error("No data available.")
        else:
            # 2. Calculate All Indicators
            all_ind_data = {}
            for ind in st.session_state.indicators:
                ind_results = {}
                for ticker in tickers:
                    if ticker in data.columns:
                        # Fetch individual ticker history for calculation
                        ticker_df = pd.DataFrame({'Close': data[ticker]})
                        val = indicators.get_indicator_value(ticker_df, ind['type'], {'window': ind['period']})
                        ind_results[ticker] = val
                all_ind_data[ind['alias']] = pd.DataFrame(ind_results, index=data.index)

            # 3. Parse Formulas and Create Signal Matrices
            # Create a safe evaluation context
            context = {'Price': data}
            for alias, matrix in all_ind_data.items():
                context[alias] = matrix
            
            try:
                # Improve formula parsing:
                # 1. Wrap comparisons in parentheses to fix & / | precedence
                def wrap_comparisons(formula):
                    # Simple regex to find comparison patterns and wrap them
                    # Matches something like: Alias > Value or Alias < Alias
                    pattern = r'([\w\.]+)\s*(>|<|>=|<=|==|!=)\s*([\w\.]+)'
                    return re.sub(pattern, r'(\1 \2 \3)', formula)

                processed_entry = wrap_comparisons(entry_formula).replace("and", "&").replace("or", "|")
                processed_exit = wrap_comparisons(exit_formula).replace("and", "&").replace("or", "|")
                
                entry_signals = eval(processed_entry, {}, context)
                # Ensure it's a boolean mask
                if not isinstance(entry_signals, pd.DataFrame):
                    entry_signals = entry_signals.to_frame()
                entry_signals = entry_signals.fillna(False).astype(bool)
                
                exit_signals = eval(processed_exit, {}, context)
                if not isinstance(exit_signals, pd.DataFrame):
                    exit_signals = exit_signals.to_frame()
                exit_signals = exit_signals.fillna(False).astype(bool)
                
                ranking_scores = eval(ranking_formula, {}, context).fillna(0)
                
                # 4. Run Backtest
                engine = backtest_engine.BacktestEngine(
                    tickers=tickers,
                    data=data,
                    entry_signals=entry_signals,
                    exit_signals=exit_signals,
                    ranking_scores=ranking_scores,
                    initial_capital=initial_cap,
                    max_positions=max_positions,
                    sizing_mode=sizing_mode
                )
                
                equity_curve, trades = engine.run()
                
                # 5. UI Tabs
                metrics = utils.calculate_performance_metrics(equity_curve)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("CAGR", metrics.get("CAGR", "N/A"))
                c2.metric("Sharpe", metrics.get("Sharpe Ratio", "N/A"))
                c3.metric("Max DD", metrics.get("Max Drawdown", "N/A"))
                c4.metric("Win Rate", metrics.get("Win Rate", "N/A"))
                
                t1, t2, t3, t4 = st.tabs(["Performance", "Drawdown", "Monthly Heatmap", "Trades"])
                with t1:
                    fig = px.line(equity_curve, x='date', y='equity', title="Portfolio Equity Curve")
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                with t2:
                    dd = utils.get_drawdown_series(equity_curve)
                    fig = px.area(dd, x='date', y='drawdown', title="Drawdown Profile")
                    fig.update_layout(template="plotly_dark")
                    st.plotly_chart(fig, use_container_width=True)
                with t3:
                    heatmap = utils.get_monthly_returns(equity_curve)
                    if not heatmap.empty:
                        fig = px.imshow(heatmap * 100, text_auto=".1f", color_continuous_scale="RdYlGn")
                        fig.update_layout(template="plotly_dark")
                        st.plotly_chart(fig, use_container_width=True)
                with t4:
                    st.dataframe(trades, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Formula Error: {e}")
                st.info("Check your indicator aliases and formula syntax.")
