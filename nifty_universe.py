import pandas as pd
import streamlit as st
import os

# Broad Market Indices
INDEX_NAMES = [
    "NIFTY 50",
    "NIFTY NEXT 50",
    "NIFTY 100",
    "NIFTY 200",
    "NIFTY 500",
    "NIFTY MIDCAP 150",
    "NIFTY MIDCAP 50",
    "NIFTY MIDCAP 100",
    "NIFTY SMLCAP 250",
    "NIFTY SMLCAP 50",
    "NIFTY SMLCAP 100",
]

DISPLAY_NAMES = {
    "NIFTY 50": "Nifty 50",
    "NIFTY NEXT 50": "Nifty Next 50",
    "NIFTY 100": "Nifty 100",
    "NIFTY 200": "Nifty 200",
    "NIFTY 500": "Nifty 500",
    "NIFTY MIDCAP 150": "Nifty Midcap 150",
    "NIFTY MIDCAP 50": "Nifty Midcap 50",
    "NIFTY MIDCAP 100": "Nifty Midcap 100",
    "NIFTY SMLCAP 250": "Nifty Smallcap 250",
    "NIFTY SMLCAP 50": "Nifty Smallcap 50",
    "NIFTY SMLCAP 100": "Nifty Smallcap 100",
}

# Mapping of index names to their official NSE CSV URLs
NSE_URLS = {
    "NIFTY 50": "https://archives.nseindia.com/content/indices/ind_nifty50list.csv",
    "NIFTY NEXT 50": "https://archives.nseindia.com/content/indices/ind_niftynext50list.csv",
    "NIFTY 100": "https://archives.nseindia.com/content/indices/ind_nifty100list.csv",
    "NIFTY 200": "https://archives.nseindia.com/content/indices/ind_nifty200list.csv",
    "NIFTY 500": "https://archives.nseindia.com/content/indices/ind_nifty500list.csv",
    "NIFTY MIDCAP 150": "https://archives.nseindia.com/content/indices/ind_niftymidcap150list.csv",
    "NIFTY MIDCAP 50": "https://archives.nseindia.com/content/indices/ind_niftymidcap50list.csv",
    "NIFTY MIDCAP 100": "https://archives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "NIFTY SMLCAP 250": "https://archives.nseindia.com/content/indices/ind_niftysmallcap250list.csv",
    "NIFTY SMLCAP 50": "https://archives.nseindia.com/content/indices/ind_niftysmallcap50list.csv",
    "NIFTY SMLCAP 100": "https://archives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
}

def get_universe_tickers(index_name):
    """Fetches tickers for a given index from NSE."""
    url = NSE_URLS.get(index_name)
    if not url:
        return []
    
    try:
        df = pd.read_csv(url)
        # Ensure we handle different CSV formats
        col = 'Symbol' if 'Symbol' in df.columns else df.columns[0]
        tickers = df[col].tolist()
        return [f"{t}.NS" for t in tickers]
    except Exception as e:
        print(f"Error fetching {index_name}: {e}")
        return []

def get_all_universes():
    return DISPLAY_NAMES
