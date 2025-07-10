import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_stock_historical_data(symbol, period="3mo"):
    """Get historical data for technical analysis"""
    try:
        if not symbol.endswith('.NS'):
            symbol += '.NS'
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
        
        return hist
    except Exception as e:
        st.error(f"Error fetching historical data for {symbol}: {e}")
        return None

def find_support_levels(data, lookback=20):
    """Find support levels using pivot lows"""
    if data is None or len(data) < lookback * 2:
        return []
    
    lows = data['Low'].values
    support_levels = []
    
    for i in range(lookback, len(lows) - lookback):
        if lows[i] == min(lows[i-lookback:i+lookback+1]):
            support_levels.append(lows[i])
    
    # Remove duplicates and sort
    support_levels = sorted(list(set(support_levels)))
    
    # Get recent support levels (last 3)
    current_price = data['Close'].iloc[-1]
    valid_supports = [level for level in support_levels if level < current_price]
    
    return sorted(valid_supports, reverse=True)[:3]

def find_resistance_levels(data, lookback=20):
    """Find resistance levels using pivot highs"""
    if data is None or len(data) < lookback * 2:
        return []
    
    highs = data['High'].values
    resistance_levels = []
    
    for i in range(lookback, len(highs) - lookback):
        if highs[i] == max(highs[i-lookback:i+lookback+1]):
            resistance_levels.append(highs[i])
    
    # Remove duplicates and sort
    resistance_levels = sorted(list(set(resistance_levels)))
    
    # Get recent resistance levels (last 3)
    current_price = data['Close'].iloc[-1]
    valid_resistances = [level for level in resistance_levels if level > current_price]
    
    return sorted(valid_resistances)[:3]

def get_daily_closing_price(symbol):
    """Get today's closing price and previous close"""
    try:
        if not symbol.endswith('.NS'):
            symbol += '.NS'
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='2d')
        
        if len(hist) < 1:
            return None, None
        
        current_close = hist['Close'].iloc[-1]
        previous_close = hist['Close'].iloc[-2] if len(hist) >= 2 else current_close
        
        return float(current_close), float(previous_close)
    except Exception as e:
        return None, None

def calculate_technical_targets(symbol, watchlist_type):
    """Calculate technical analysis based target prices"""
    hist_data = get_stock_historical_data(symbol)
    
    if hist_data is None:
        return None, None, "Unable to fetch historical data"
    
    current_price = hist_data['Close'].iloc[-1]
    
    if watchlist_type == 'sell':
        # For sell watchlist, find support levels
        support_levels = find_support_levels(hist_data)
        if support_levels:
            target_price = support_levels[0]  # Strongest support
            analysis = f"Support at ₹{target_price:.2f} (Current: ₹{current_price:.2f})"
            return float(target_price), analysis, None
        else:
            return None, "No clear support levels found", "Insufficient data for support analysis"
    
    elif watchlist_type == 'buy':
        # For buy watchlist, find resistance levels
        resistance_levels = find_resistance_levels(hist_data)
        if resistance_levels:
            target_price = resistance_levels[0]  # Nearest resistance
            analysis = f"Resistance at ₹{target_price:.2f} (Current: ₹{current_price:.2f})"
            return float(target_price), analysis, None
        else:
            return None, "No clear resistance levels found", "Insufficient data for resistance analysis"
    
    return None, "Invalid watchlist type", "Error in analysis"

def check_daily_close_breakout(symbol, target_price, watchlist_type):
    """Check if daily close has broken support/resistance"""
    current_close, previous_close = get_daily_closing_price(symbol)
    
    if current_close is None:
        return False, "Unable to get closing price"
    
    if watchlist_type == 'sell':
        # Check if price closed below support
        if current_close < target_price and previous_close >= target_price:
            return True, f"Support broken: Closed at ₹{current_close:.2f}, below support of ₹{target_price:.2f}"
        elif current_close < target_price:
            return True, f"Below support: Closed at ₹{current_close:.2f}, support at ₹{target_price:.2f}"
    
    elif watchlist_type == 'buy':
        # Check if price closed above resistance
        if current_close > target_price and previous_close <= target_price:
            return True, f"Resistance broken: Closed at ₹{current_close:.2f}, above resistance of ₹{target_price:.2f}"
        elif current_close > target_price:
            return True, f"Above resistance: Closed at ₹{current_close:.2f}, resistance at ₹{target_price:.2f}"
    
    return False, f"Target not reached: Current close ₹{current_close:.2f}, target ₹{target_price:.2f}"

def get_technical_analysis_summary(symbol):
    """Get comprehensive technical analysis for a stock"""
    hist_data = get_stock_historical_data(symbol)
    
    if hist_data is None:
        return "Unable to perform technical analysis"
    
    current_price = hist_data['Close'].iloc[-1]
    supports = find_support_levels(hist_data)
    resistances = find_resistance_levels(hist_data)
    
    summary = f"**{symbol} Technical Analysis:**\n"
    summary += f"Current Price: ₹{current_price:.2f}\n\n"
    
    if supports:
        summary += "**Support Levels:**\n"
        for i, support in enumerate(supports[:3], 1):
            summary += f"{i}. ₹{support:.2f}\n"
        summary += "\n"
    
    if resistances:
        summary += "**Resistance Levels:**\n"
        for i, resistance in enumerate(resistances[:3], 1):
            summary += f"{i}. ₹{resistance:.2f}\n"
    
    return summary

def show_technical_analysis_interface():
    """Show technical analysis interface in the sidebar"""
    st.sidebar.subheader("📊 Technical Analysis")
    
    # Stock analysis lookup
    analysis_symbol = st.sidebar.text_input(
        "Analyze Stock",
        placeholder="Enter symbol (e.g., RELIANCE)",
        help="Get support/resistance levels for any stock"
    )
    
    if analysis_symbol and st.sidebar.button("📈 Analyze"):
        with st.sidebar.expander(f"Analysis: {analysis_symbol.upper()}"):
            summary = get_technical_analysis_summary(analysis_symbol)
            st.write(summary)
    
    # Auto-target price feature
    st.sidebar.write("**Auto Target Prices:**")
    st.sidebar.info("Enable this to automatically set support/resistance as target prices when adding stocks")
    
    return st.sidebar.checkbox("🎯 Use Technical Targets", value=True)

def enhanced_add_stock_with_technical_analysis(symbol, manual_target, watchlist_type, use_technical=True):
    """Enhanced stock addition with technical analysis"""
    if use_technical and manual_target is None:
        # Use technical analysis to set target
        target_price, analysis, error = calculate_technical_targets(symbol, watchlist_type)
        
        if target_price is not None:
            return target_price, f"Technical target set: {analysis}"
        else:
            return None, f"Technical analysis failed: {error}"
    
    elif manual_target is not None:
        # Use manual target price
        return manual_target, "Manual target price set"
    
    else:
        return None, "No target price specified"