import json
import csv
import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_watchlist_from_db, add_stock_to_db, get_recent_notifications
import io

def export_watchlists_to_json():
    """Export all watchlists to JSON format"""
    try:
        buy_stocks = get_watchlist_from_db('buy')
        sell_stocks = get_watchlist_from_db('sell')
        
        export_data = {
            'export_date': datetime.now().isoformat(),
            'buy_watchlist': buy_stocks,
            'sell_watchlist': sell_stocks,
            'total_stocks': len(buy_stocks) + len(sell_stocks)
        }
        
        return json.dumps(export_data, indent=2), True
    except Exception as e:
        return f"Error exporting data: {str(e)}", False

def export_watchlists_to_csv():
    """Export watchlists to CSV format"""
    try:
        buy_stocks = get_watchlist_from_db('buy')
        sell_stocks = get_watchlist_from_db('sell')
        
        # Combine all stocks with watchlist type
        all_stocks = []
        for stock in buy_stocks:
            stock_data = stock.copy()
            stock_data['watchlist_type'] = 'buy'
            all_stocks.append(stock_data)
        
        for stock in sell_stocks:
            stock_data = stock.copy()
            stock_data['watchlist_type'] = 'sell'
            all_stocks.append(stock_data)
        
        if not all_stocks:
            return "No data to export", False
        
        # Create DataFrame and CSV
        df = pd.DataFrame(all_stocks)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return csv_buffer.getvalue(), True
    except Exception as e:
        return f"Error exporting to CSV: {str(e)}", False

def import_watchlists_from_json(json_data):
    """Import watchlists from JSON data"""
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        data = json.loads(json_data)
        
        # Import buy watchlist
        for stock in data.get('buy_watchlist', []):
            success, message = add_stock_to_db(
                stock['symbol'], 
                stock['target_price'], 
                'buy'
            )
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(f"Buy - {stock['symbol']}: {message}")
        
        # Import sell watchlist
        for stock in data.get('sell_watchlist', []):
            success, message = add_stock_to_db(
                stock['symbol'], 
                stock['target_price'], 
                'sell'
            )
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(f"Sell - {stock['symbol']}: {message}")
        
        return success_count, error_count, errors
    except Exception as e:
        return 0, 1, [f"Error parsing JSON: {str(e)}"]

def import_watchlists_from_csv(csv_data):
    """Import watchlists from CSV data"""
    success_count = 0
    error_count = 0
    errors = []
    
    try:
        # Read CSV data
        csv_buffer = io.StringIO(csv_data)
        df = pd.read_csv(csv_buffer)
        
        for _, row in df.iterrows():
            success, message = add_stock_to_db(
                row['symbol'], 
                row['target_price'], 
                row['watchlist_type']
            )
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(f"{row['watchlist_type'].title()} - {row['symbol']}: {message}")
        
        return success_count, error_count, errors
    except Exception as e:
        return 0, 1, [f"Error parsing CSV: {str(e)}"]

def create_backup_filename(format_type):
    """Create a standardized backup filename"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"nse_watchlist_backup_{timestamp}.{format_type}"

def show_backup_restore_interface():
    """Display backup and restore interface in Streamlit"""
    st.sidebar.subheader("💾 Data Backup")
    
    # Export section
    st.sidebar.write("**Export Your Data:**")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("📄 Export JSON", help="Export as JSON file"):
            json_data, success = export_watchlists_to_json()
            if success:
                st.sidebar.download_button(
                    label="⬇️ Download JSON",
                    data=json_data,
                    file_name=create_backup_filename("json"),
                    mime="application/json"
                )
            else:
                st.sidebar.error("Export failed")
    
    with col2:
        if st.button("📊 Export CSV", help="Export as CSV file"):
            csv_data, success = export_watchlists_to_csv()
            if success:
                st.sidebar.download_button(
                    label="⬇️ Download CSV",
                    data=csv_data,
                    file_name=create_backup_filename("csv"),
                    mime="text/csv"
                )
            else:
                st.sidebar.error("Export failed")
    
    # Import section
    st.sidebar.write("**Restore Your Data:**")
    
    # File uploader for restore
    uploaded_file = st.sidebar.file_uploader(
        "Upload backup file",
        type=['json', 'csv'],
        help="Upload your previously exported JSON or CSV file"
    )
    
    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if st.sidebar.button("🔄 Restore Data"):
            file_content = uploaded_file.read().decode('utf-8')
            
            if file_extension == 'json':
                success_count, error_count, errors = import_watchlists_from_json(file_content)
            elif file_extension == 'csv':
                success_count, error_count, errors = import_watchlists_from_csv(file_content)
            else:
                st.sidebar.error("Unsupported file format")
                return
            
            # Show results
            if success_count > 0:
                st.sidebar.success(f"✅ Restored {success_count} stocks successfully")
            
            if error_count > 0:
                st.sidebar.warning(f"⚠️ {error_count} items failed to import")
                with st.sidebar.expander("Show errors"):
                    for error in errors:
                        st.write(f"• {error}")
            
            if success_count > 0:
                st.rerun()

def get_backup_instructions():
    """Get backup instructions for users"""
    return """
    ## 📋 How to Keep Your Data Safe:
    
    **Before Database Expires (within 6 days):**
    1. Click "Export JSON" or "Export CSV" in the sidebar
    2. Download the backup file to your computer
    3. Keep this file safe
    
    **After Database Resets:**
    1. Upload your backup file using "Upload backup file"
    2. Click "Restore Data" to get all your stocks back
    3. Your watchlists will be exactly as before
    
    **Tips:**
    - Export regularly to keep backups updated
    - JSON format preserves all data perfectly
    - CSV format can be opened in Excel for viewing
    - Keep multiple backup copies for safety
    """