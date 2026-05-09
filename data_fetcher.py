import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta
import streamlit as st

CACHE_DIR = "data_cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def get_nifty500_tickers():
    """
    Fetches the Nifty 500 ticker list from NSE.
    Returns a list of tickers formatted for yfinance (e.g., 'RELIANCE.NS').
    """
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        tickers = df['Symbol'].tolist()
        return [f"{t}.NS" for t in tickers]
    except Exception as e:
        st.error(f"Error fetching Nifty 500 list: {e}")
        # Fallback to a small list for testing if NSE is down
        return ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS"]

def fetch_data(tickers, start_date, end_date):
    """
    Fetches historical data for a list of tickers using batch download.
    Uses local caching to avoid redundant downloads.
    """
    all_data = {}
    to_download = []
    
    # 1. Identify what needs downloading
    for ticker in tickers:
        cache_file = os.path.join(CACHE_DIR, f"{ticker}.parquet")
        if os.path.exists(cache_file):
            try:
                df = pd.read_parquet(cache_file)
                if not df.empty:
                    last_date = df.index[-1].strftime('%Y-%m-%d')
                    # If cached data is up to date, use it
                    if last_date >= end_date:
                        all_data[ticker] = df
                        continue
            except:
                pass
        to_download.append(ticker)
    
    # 2. Batch Download missing data
    if to_download:
        try:
            # Download with 1 year buffer for indicators (SMA 200)
            download_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
            
            # Use chunks for large universes to avoid timeouts
            chunk_size = 50
            for i in range(0, len(to_download), chunk_size):
                chunk = to_download[i:i+chunk_size]
                df_chunk = yf.download(chunk, start=download_start, end=end_date, progress=False, group_by='ticker')
                
                for ticker in chunk:
                    if ticker in df_chunk.columns.get_level_values(0):
                        ticker_df = df_chunk[ticker].dropna(how='all')
                        if not ticker_df.empty:
                            cache_file = os.path.join(CACHE_DIR, f"{ticker}.parquet")
                            ticker_df.to_parquet(cache_file)
                            all_data[ticker] = ticker_df
        except Exception as e:
            st.warning(f"Batch download failed: {e}. Falling back to individual downloads.")
            # Fallback logic if batch fails
            for ticker in to_download:
                try:
                    df = yf.download(ticker, start=download_start, end=end_date, progress=False)
                    if not df.empty:
                        df.to_parquet(os.path.join(CACHE_DIR, f"{ticker}.parquet"))
                        all_data[ticker] = df
                except:
                    continue
                
    return all_data

def get_combined_data(tickers, start_date, end_date, column='Adj Close'):
    """
    Returns a single DataFrame with columns as tickers and values as the specified column.
    """
    data = fetch_data(tickers, start_date, end_date)
    combined = pd.DataFrame()
    
    for ticker, df in data.items():
        # Check both 'Adj Close' and 'Close'
        col_to_use = None
        if column in df.columns:
            col_to_use = column
        elif 'Close' in df.columns:
            col_to_use = 'Close'
            
        if col_to_use:
            # Select and filter by date
            series = df[col_to_use]
            combined[ticker] = series
            
    # Filter for the requested date range after combining
    if not combined.empty:
        combined = combined[(combined.index >= start_date) & (combined.index <= end_date)]
        
    return combined
