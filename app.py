import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time
from stock_utils import get_nse_stock_data, format_currency, calculate_percentage_difference
from email_utils import setup_email_notifications, check_email_notifications
from database import (
    init_database, add_stock_to_db, get_watchlist_from_db, 
    remove_stock_from_db, log_notification, get_watchlist_stats
)
from backup_utils import show_backup_restore_interface, get_backup_instructions
# Technical analysis imports removed per user request

# Page configuration
st.set_page_config(
    page_title="NSE Stock Analysis Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = init_database()
    if not st.session_state.db_initialized:
        st.error("Failed to initialize database. Please refresh the page.")
        st.stop()

# Initialize session state
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

def add_stock_to_watchlist(stock_symbol, target_price, watchlist_type):
    """Add a stock to the specified watchlist"""
    success, message = add_stock_to_db(stock_symbol, target_price, watchlist_type)
    
    if success:
        st.success(message)
    else:
        st.warning(message)

def remove_stock_from_watchlist(stock_symbol, watchlist_type):
    """Remove a stock from the specified watchlist"""
    success, message = remove_stock_from_db(stock_symbol, watchlist_type)
    
    if success:
        st.success(message)
    else:
        st.warning(message)

def display_watchlist(watchlist, watchlist_type, email_enabled=False, recipient_email=None):
    """Display the watchlist with current prices and analysis"""
    if not watchlist:
        st.info(f"No stocks in {watchlist_type.title()} Watchlist. Add some stocks to get started!")
        return
    
    # Create a progress bar for data fetching
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    watchlist_data = []
    total_stocks = len(watchlist)
    
    for i, stock in enumerate(watchlist):
        status_text.text(f"Fetching data for {stock['symbol']}...")
        progress_bar.progress((i + 1) / total_stocks)
        
        current_price, change, change_percent = get_nse_stock_data(stock['symbol'])
        
        if current_price is not None:
            target_price = stock['target_price']
            price_diff = calculate_percentage_difference(current_price, target_price)
            
            # Determine status and color coding
            # Calculate percentage difference: positive means current > target, negative means current < target
            percent_from_target = ((current_price - target_price) / target_price) * 100
            
            if watchlist_type == 'buy':
                # For buy watchlist, we want to buy when price is at or below target
                if current_price <= target_price:
                    status = "🎯 TARGET REACHED"
                    status_color = "green"
                elif -1 <= percent_from_target <= 1:  # Within -1% to +1% of target
                    status = "🔥 CLOSE TO TARGET"
                    status_color = "orange"
                else:
                    status = "⏳ WAITING"
                    status_color = "blue"
            else:
                # For sell watchlist, we want to sell when price is at or above target
                if current_price >= target_price:
                    status = "🎯 TARGET REACHED"
                    status_color = "green"
                elif -1 <= percent_from_target <= 1:  # Within -1% to +1% of target
                    status = "🔥 CLOSE TO TARGET"
                    status_color = "orange"
                else:
                    status = "⏳ WAITING"
                    status_color = "blue"
            
            watchlist_data.append({
                'Symbol': stock['symbol'],
                'Current Price': f"₹{current_price:.2f}",
                'Target Price': f"₹{target_price:.2f}",
                'Change': f"{change:.2f} ({change_percent:.2f}%)",
                'Price Difference': f"{price_diff:.2f}%",
                'Status': status,
                'Status Color': status_color,
                'Added Date': stock['added_date']
            })
        else:
            watchlist_data.append({
                'Symbol': stock['symbol'],
                'Current Price': "Error",
                'Target Price': f"₹{target_price:.2f}",
                'Change': "N/A",
                'Price Difference': "N/A",
                'Status': "❌ ERROR",
                'Status Color': "red",
                'Added Date': stock['added_date']
            })
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display the watchlist
    if watchlist_data:
        df = pd.DataFrame(watchlist_data)
        
        # Check for email notifications if enabled
        if email_enabled and recipient_email:
            notifications_sent = check_email_notifications(watchlist_data, watchlist_type, recipient_email)
            
            if notifications_sent:
                st.info(f"📧 Email notifications would be sent for: {', '.join(notifications_sent)}")
        
        # Display highlighted stocks that reached targets
        target_reached = df[df['Status'] == '🎯 TARGET REACHED']
        if not target_reached.empty:
            st.subheader("🚨 Stocks at Target Price")
            for _, row in target_reached.iterrows():
                st.success(f"**{row['Symbol']}** has reached your target price of {row['Target Price']}!")
        
        # Display stocks close to target
        close_to_target = df[df['Status'] == '🔥 CLOSE TO TARGET']
        if not close_to_target.empty:
            st.subheader("🔥 Stocks Close to Target (Within -1% to +1%)")
            for _, row in close_to_target.iterrows():
                st.warning(f"**{row['Symbol']}** is close to your target price. Current: {row['Current Price']}, Target: {row['Target Price']}")
                if email_enabled and recipient_email:
                    st.info(f"📧 Email alert would be sent to {recipient_email}")
        
        # Display full watchlist table
        st.subheader(f"{watchlist_type.title()} Watchlist")
        
        # Create columns for better layout
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write("**Stock Details**")
        with col2:
            st.write("**Price Analysis**")
        with col3:
            st.write("**Actions**")
        
        for _, row in df.iterrows():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Stock symbol and basic info
                st.write(f"**{row['Symbol']}**")
                st.write(f"Added: {row['Added Date']}")
            
            with col2:
                # Price information
                st.write(f"Current: {row['Current Price']}")
                st.write(f"Target: {row['Target Price']}")
                st.write(f"Change: {row['Change']}")
                st.write(f"Diff: {row['Price Difference']}")
                
                # Status with color
                if row['Status Color'] == 'green':
                    st.success(row['Status'])
                elif row['Status Color'] == 'orange':
                    st.warning(row['Status'])
                elif row['Status Color'] == 'red':
                    st.error(row['Status'])
                else:
                    st.info(row['Status'])
            
            with col3:
                # Remove button
                if st.button(f"Remove {row['Symbol']}", key=f"remove_{watchlist_type}_{row['Symbol']}"):
                    remove_stock_from_watchlist(row['Symbol'], watchlist_type)
                    st.rerun()
            
            st.divider()

def main():
    st.title("📈 NSE Stock Analysis Dashboard")
    st.markdown("Track your buy and sell targets for NSE stocks with real-time price monitoring")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose Dashboard", ["Buy Dashboard", "Sell Dashboard", "Data Backup Guide"])
    
    # Email notification setup
    email_enabled, recipient_email = setup_email_notifications()
    
    # Backup and restore interface
    show_backup_restore_interface()
    
    # Technical analysis removed per user request
    
    # Auto-refresh settings
    st.sidebar.subheader("Auto Refresh")
    auto_refresh = st.sidebar.checkbox("Enable Auto Refresh (30 seconds)")
    
    if auto_refresh:
        # Check if it's time to refresh
        time_since_update = (datetime.now() - st.session_state.last_update).total_seconds()
        if time_since_update >= 30:
            st.session_state.last_update = datetime.now()
            st.rerun()
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.session_state.last_update = datetime.now()
        st.rerun()
    
    # Display last update time
    st.sidebar.write(f"Last updated: {st.session_state.last_update.strftime('%H:%M:%S')}")
    
    # Display watchlist statistics
    st.sidebar.subheader("📊 Watchlist Stats")
    stats = get_watchlist_stats()
    st.sidebar.metric("Buy Watchlist", stats['buy_count'])
    st.sidebar.metric("Sell Watchlist", stats['sell_count'])
    st.sidebar.metric("Total Stocks", stats['total_stocks'])
    
    # Show backup reminder if user has stocks
    if stats['total_stocks'] > 0:
        st.sidebar.warning("💾 Remember to backup your data! Database expires in 6 days.")
    
    # Main content area
    if page == "Buy Dashboard":
        st.header("🟢 Buy Dashboard")
        st.markdown("Add stocks you want to buy when they reach your target price")
        
        # Add stock form
        with st.expander("➕ Add Stock to Buy Watchlist"):
            col1, col2 = st.columns(2)
            with col1:
                buy_symbol = st.text_input("Stock Symbol (e.g., RELIANCE.NS)", key="buy_symbol")
            with col2:
                buy_target = st.number_input("Target Buy Price (₹)", min_value=0.01, key="buy_target")
            
            if st.button("Add to Buy Watchlist", key="add_buy"):
                if buy_symbol and buy_target:
                    add_stock_to_watchlist(buy_symbol, buy_target, 'buy')
                    st.rerun()
                else:
                    st.error("Please enter both stock symbol and target price")
        
        # Display buy watchlist
        buy_stocks = get_watchlist_from_db('buy')
        display_watchlist(buy_stocks, 'buy', email_enabled, recipient_email)
    
    elif page == "Sell Dashboard":
        st.header("🔴 Sell Dashboard")
        st.markdown("Add stocks you want to sell when they reach your target price")
        
        # Add stock form
        with st.expander("➕ Add Stock to Sell Watchlist"):
            col1, col2 = st.columns(2)
            with col1:
                sell_symbol = st.text_input("Stock Symbol (e.g., RELIANCE.NS)", key="sell_symbol")
            with col2:
                sell_target = st.number_input("Target Sell Price (₹)", min_value=0.01, key="sell_target")
            
            if st.button("Add to Sell Watchlist", key="add_sell"):
                if sell_symbol and sell_target:
                    add_stock_to_watchlist(sell_symbol, sell_target, 'sell')
                    st.rerun()
                else:
                    st.error("Please enter both stock symbol and target price")
        
        # Display sell watchlist
        sell_stocks = get_watchlist_from_db('sell')
        display_watchlist(sell_stocks, 'sell', email_enabled, recipient_email)
    
    elif page == "Data Backup Guide":
        st.header("💾 Data Backup Guide")
        st.markdown("**Important:** Free trial database expires in 6 days. Save your data to keep it safe!")
        
        # Display backup instructions
        st.markdown(get_backup_instructions())
        
        # Add warning about database expiration
        st.warning("⚠️ **Database Expiration Notice:** Your free trial database will pause after 6 days and be deleted later. Export your data now to avoid losing your watchlists!")
        
        # Quick stats
        stats = get_watchlist_stats()
        if stats['total_stocks'] > 0:
            st.info(f"📊 You currently have {stats['total_stocks']} stocks in your watchlists ({stats['buy_count']} buy, {stats['sell_count']} sell)")
        else:
            st.info("📊 No stocks in watchlists yet. Add some stocks first, then come back to backup your data.")
        
        # Additional tips
        st.subheader("💡 Pro Tips")
        st.markdown("""
        - **Export regularly**: Set a reminder to export your data every few days
        - **Multiple backups**: Keep backup files in different locations (computer, cloud storage)
        - **File naming**: Backup files include date/time, so you can track versions
        - **After restore**: Check your watchlists to ensure all data imported correctly
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("**Note:** NSE stock symbols should end with '.NS' (e.g., RELIANCE.NS, TCS.NS)")
    st.markdown("**Tip:** Use the exact NSE symbol for accurate data. Check NSE website for correct symbols.")
    st.markdown("**Email Alerts:** Enable email notifications to get alerts when stocks are within -1% to +1% of your target price.")

if __name__ == "__main__":
    main()
