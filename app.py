import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import data_fetcher
import indicators
import backtest_engine
import utils
import nifty_universe

# Page Config
st.set_page_config(page_title="Trend Following Dashboard", layout="wide", initial_sidebar_state="expanded")

# Custom Styling
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #30363d;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🚀 Strategy Parameters")

# Universe Selection
all_universes = nifty_universe.get_all_universes()
selected_universe_display = st.sidebar.selectbox("Universe", list(all_universes.values()), index=4)
selected_universe_key = [k for k, v in all_universes.items() if v == selected_universe_display][0]

start_date = st.sidebar.date_input("Start Date", datetime(2023, 1, 1))
end_date = st.sidebar.date_input("End Date", datetime.now())

st.sidebar.subheader("Indicator Timeframe")
timeframe = st.sidebar.selectbox("Timeframe", ["Daily", "Weekly", "Monthly"], index=0)
interval_map = {"Daily": "1d", "Weekly": "1wk", "Monthly": "1mo"}
interval = interval_map[timeframe]

st.sidebar.subheader("Technical Indicators")
sma_fast = st.sidebar.number_input("SMA Fast (Entry Period)", value=50, min_value=5, max_value=200)
sma_slow = st.sidebar.number_input("SMA Slow (Regime Period)", value=200, min_value=20, max_value=500)

st.sidebar.subheader("Risk Management")
max_positions = st.sidebar.slider("Max Positions", 5, 50, 20)
stop_loss_pct = st.sidebar.slider("Trailing Stop Loss (%)", 5, 30, 15) / 100
initial_capital = st.sidebar.number_input("Initial Capital (₹)", value=1000000)

# Main Header
st.title("📈 Trend Following Backtest Dashboard")
st.markdown("---")

if st.sidebar.button("Run Backtest", use_container_width=True):
    with st.spinner(f"Fetching data for {selected_universe_display}..."):
        # 1. Fetch Tickers
        tickers = nifty_universe.get_universe_tickers(selected_universe_key)
            
        if not tickers:
            st.error(f"Could not fetch tickers for {selected_universe_display}")
        else:
            # 2. Fetch Data
            combined_data = data_fetcher.get_combined_data(
                tickers, 
                start_date.strftime('%Y-%m-%d'), 
                end_date.strftime('%Y-%m-%d'),
                interval=interval
            )
            
            if combined_data.empty:
                st.error("No data fetched. Please check your parameters or internet connection.")
            else:
                # 3. Calculate Indicators
                strategy_indicators = indicators.get_strategy_indicators(combined_data, sma_fast, sma_slow)
                
                # 4. Run Backtest
                engine = backtest_engine.BacktestEngine(
                    tickers=tickers,
                    data=combined_data,
                    indicators=strategy_indicators,
                    initial_capital=initial_capital,
                    max_positions=max_positions,
                    stop_loss_pct=stop_loss_pct
                )
                equity_curve, trades = engine.run()
                
                # 5. Display Results
                metrics = utils.calculate_performance_metrics(equity_curve)
                
                # Metrics Row
                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("CAGR", metrics.get("CAGR", "N/A"))
                col2.metric("Sharpe Ratio", metrics.get("Sharpe Ratio", "N/A"))
                col3.metric("Max Drawdown", metrics.get("Max Drawdown", "N/A"))
                col4.metric("Total Return", metrics.get("Total Return", "N/A"))
                col5.metric("Win Rate", metrics.get("Win Rate", "N/A"))
                
                # Tabs
                tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance", "📉 Drawdown", "📅 Monthly Returns", "📜 Trade History"])
                
                with tab1:
                    st.markdown("### Equity Curve")
                    fig_equity = go.Figure()
                    fig_equity.add_trace(go.Scatter(x=equity_curve['date'], y=equity_curve['equity'], mode='lines', name='Portfolio Value', line=dict(color='#00ff88', width=2)))
                    fig_equity.update_layout(template="plotly_dark", height=500, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_equity, use_container_width=True)
                
                with tab2:
                    st.markdown("### Drawdown Profile")
                    dd_df = utils.get_drawdown_series(equity_curve)
                    fig_dd = go.Figure()
                    fig_dd.add_trace(go.Scatter(x=dd_df['date'], y=dd_df['drawdown'] * 100, fill='tozeroy', name='Drawdown %', line=dict(color='#ff4b4b')))
                    fig_dd.update_layout(template="plotly_dark", height=400, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_dd, use_container_width=True)
                
                with tab3:
                    st.markdown("### Monthly Returns Heatmap (%)")
                    monthly_pivot = utils.get_monthly_returns(equity_curve)
                    if not monthly_pivot.empty:
                        fig_heatmap = px.imshow(
                            monthly_pivot * 100,
                            labels=dict(x="Month", y="Year", color="Return %"),
                            color_continuous_scale="RdYlGn",
                            text_auto=".2f"
                        )
                        fig_heatmap.update_layout(template="plotly_dark", height=500)
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                    else:
                        st.info("Not enough data for monthly returns heatmap.")
                
                with tab4:
                    if not trades.empty:
                        st.markdown("### Trade History")
                        st.dataframe(trades.sort_values('exit_date', ascending=False), use_container_width=True)
                    else:
                        st.info("No trades executed during this period.")

else:
    st.info("👈 Adjust parameters in the sidebar and click 'Run Backtest' to see results.")
    
    # Feature Overview
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Strategy Logic")
        st.markdown("""
        - **Bullish Regime**: Price > SMA (Fast) and SMA (Fast) > SMA (Slow)
        - **Momentum Score**: Distance from SMA (Slow) (%)
        - **Selection**: Top N stocks by Momentum
        - **Exit**: Price < SMA (Fast) or Trailing Stop Loss
        """)
    with col2:
        st.subheader("Advanced Features")
        st.markdown("""
        - **Universe**: Multiple Nifty Broad Market Indices
        - **Intervals**: Support for Daily, Weekly, and Monthly backtests
        - **Metrics**: CAGR, Sharpe, Win Rate, and Drawdown analytics
        - **Visuals**: Equity curves, Heatmaps, and detailed Trade History
        """)
