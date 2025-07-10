import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta
import time

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_nse_stock_data(symbol):
    """
    Fetch NSE stock data using yfinance
    Returns: (current_price, change, change_percent)
    """
    try:
        # Ensure symbol has .NS suffix for NSE stocks
        if not symbol.endswith('.NS'):
            symbol += '.NS'
        
        # Create ticker object
        ticker = yf.Ticker(symbol)
        
        # Get current data
        info = ticker.info
        hist = ticker.history(period='2d')
        
        if hist.empty:
            return None, None, None
        
        # Get current price (last close)
        current_price = hist['Close'].iloc[-1]
        
        # Calculate change from previous day
        if len(hist) >= 2:
            previous_price = hist['Close'].iloc[-2]
            change = current_price - previous_price
            change_percent = (change / previous_price) * 100
        else:
            change = 0
            change_percent = 0
        
        return float(current_price), float(change), float(change_percent)
        
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, None, None

def format_currency(amount):
    """Format currency in Indian Rupees"""
    return f"₹{amount:,.2f}"

def calculate_percentage_difference(current_price, target_price):
    """
    Calculate percentage difference between current and target price
    Positive value means current price is higher than target
    Negative value means current price is lower than target
    """
    if target_price == 0:
        return 0
    
    difference = ((current_price - target_price) / target_price) * 100
    return abs(difference)

def get_stock_recommendation(current_price, target_price, watchlist_type):
    """
    Get recommendation based on current price vs target price
    """
    if current_price is None or target_price is None:
        return "Unable to analyze", "gray"
    
    percentage_diff = calculate_percentage_difference(current_price, target_price)
    
    if watchlist_type == 'buy':
        if current_price <= target_price:
            return "🎯 BUY NOW - Target Reached!", "green"
        elif percentage_diff <= 1:
            return "🔥 Close to Buy Target", "orange"
        elif percentage_diff <= 5:
            return "⚠️ Getting Close", "yellow"
        else:
            return "⏳ Wait for Better Price", "blue"
    else:  # sell
        if current_price >= target_price:
            return "🎯 SELL NOW - Target Reached!", "green"
        elif percentage_diff <= 1:
            return "🔥 Close to Sell Target", "orange"
        elif percentage_diff <= 5:
            return "⚠️ Getting Close", "yellow"
        else:
            return "⏳ Wait for Better Price", "blue"

def validate_nse_symbol(symbol):
    """
    Validate if the symbol is a valid NSE stock symbol
    """
    if not symbol:
        return False, "Symbol cannot be empty"
    
    # Basic validation
    symbol = symbol.upper().strip()
    
    # Check if symbol already has .NS suffix
    if symbol.endswith('.NS'):
        base_symbol = symbol[:-3]
    else:
        base_symbol = symbol
    
    # Basic symbol validation (alphanumeric, no spaces)
    if not base_symbol.replace('&', '').replace('-', '').isalnum():
        return False, "Invalid symbol format"
    
    return True, f"{base_symbol}.NS"

def get_popular_nse_stocks():
    """
    Return a list of popular NSE stock symbols for reference
    """
    return [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HINDUNILVR.NS",
        "ICICIBANK.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "LT.NS",
        "ASIANPAINT.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS", "TITAN.NS",
        "ULTRACEMCO.NS", "WIPRO.NS", "NESTLEIND.NS", "HCLTECH.NS", "POWERGRID.NS"
    ]

def format_stock_change(change, change_percent):
    """
    Format stock change with appropriate color coding
    """
    if change > 0:
        return f"🟢 +{change:.2f} (+{change_percent:.2f}%)"
    elif change < 0:
        return f"🔴 {change:.2f} ({change_percent:.2f}%)"
    else:
        return f"⚪ {change:.2f} ({change_percent:.2f}%)"

def get_market_status():
    """
    Get current market status (open/closed)
    NSE trading hours: 9:15 AM to 3:30 PM (IST)
    """
    now = datetime.now()
    
    # Check if it's a weekday (Monday = 0, Sunday = 6)
    if now.weekday() >= 5:  # Saturday or Sunday
        return "Market Closed (Weekend)"
    
    # Check trading hours (9:15 AM to 3:30 PM)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if market_open <= now <= market_close:
        return "Market Open"
    else:
        return "Market Closed"
