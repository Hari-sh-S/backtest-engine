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
    Fetches historical data for a list of tickers.
    Uses local caching to avoid redundant downloads.
    """
    all_data = {}
    
    # Check what we have in cache
    for ticker in tickers:
        cache_file = os.path.join(CACHE_DIR, f"{ticker}.parquet")
        needs_download = True
        
        if os.path.exists(cache_file):
            df = pd.read_parquet(cache_file)
            if not df.empty:
                last_date = df.index[-1].strftime('%Y-%m-%d')
                if last_date >= end_date:
                    all_data[ticker] = df[(df.index >= start_date) & (df.index <= end_date)]
                    needs_download = False
        
        if needs_download:
            try:
                # Download with a bit of buffer for indicators
                download_start = (datetime.strptime(start_date, '%Y-%m-%d') - timedelta(days=365)).strftime('%Y-%m-%d')
                df = yf.download(ticker, start=download_start, end=end_date, progress=False)
                if not df.empty:
                    df.to_parquet(cache_file)
                    all_data[ticker] = df[(df.index >= start_date) & (df.index <= end_date)]
            except Exception as e:
                print(f"Error downloading {ticker}: {e}")
                
    return all_data

def get_combined_data(tickers, start_date, end_date, column='Adj Close'):
    """
    Returns a single DataFrame with columns as tickers and values as the specified column.
    """
    data = fetch_data(tickers, start_date, end_date)
    combined = pd.DataFrame()
    for ticker, df in data.items():
        if column in df.columns:
            combined[ticker] = df[column]
    return combined
