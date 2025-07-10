# NSE Stock Analysis Dashboard

## Overview

This is a Streamlit-based web application for analyzing NSE (National Stock Exchange) stocks. The application provides a dashboard interface for tracking stock prices, managing watchlists, and performing basic stock analysis. It uses the yfinance library to fetch real-time stock data and provides functionality to maintain buy and sell watchlists with target prices.

## User Preferences

Preferred communication style: Simple, everyday language.
Close to target threshold: -1% to +1% range (updated from 1%)
Email notifications: jatin.infomail@gmail.com for stocks within -1% to +1% of target price
Technical analysis: Removed per user request - user prefers manual target price entry

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit - A Python web framework for rapid development of data applications
- **Layout**: Wide layout with expandable sidebar for navigation
- **UI Components**: Native Streamlit components for forms, charts, and data display
- **State Management**: Streamlit session state for maintaining user data across interactions

### Backend Architecture
- **Language**: Python
- **Data Processing**: Pandas for data manipulation and analysis
- **API Integration**: yfinance library for fetching stock market data
- **Caching**: Streamlit's built-in caching mechanism with 30-second TTL for stock data

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Main application entry point and UI orchestration
- **Key Features**:
  - Dashboard configuration and layout
  - Session state management for watchlists
  - Stock addition/removal functionality
  - Real-time data display

### 2. Stock Utilities (stock_utils.py)
- **Purpose**: Core stock data fetching and processing logic
- **Key Features**:
  - NSE stock data retrieval with automatic .NS suffix handling
  - Data caching for performance optimization
  - Currency formatting for Indian Rupees
  - Percentage calculation utilities

### 3. Watchlist Management
- **Buy Watchlist**: Tracks stocks user wants to purchase at target prices
- **Sell Watchlist**: Tracks stocks user wants to sell at target prices
- **Persistence**: Uses PostgreSQL database for permanent storage
- **Email Notifications**: System tracks and logs when stocks reach within 1% of target prices

### 4. Database Layer (database.py)
- **Purpose**: Persistent data storage and retrieval for watchlists and notifications
- **Key Features**:
  - PostgreSQL integration with SQLAlchemy ORM
  - Watchlist CRUD operations (Create, Read, Update, Delete)
  - Notification logging system
  - Database statistics and analytics
  - Soft delete functionality for maintaining data integrity

### 5. Email Notification System (email_utils.py)
- **Purpose**: Email alert system for price target notifications
- **Key Features**:
  - SMTP email sending capabilities
  - Notification tracking to prevent spam
  - Configurable email templates
  - Integration with database logging

### 6. Data Backup System (backup_utils.py)
- **Purpose**: Export and import system to preserve user data beyond free trial limitations
- **Key Features**:
  - JSON export/import for complete data preservation
  - CSV export/import for Excel compatibility
  - Automated backup file naming with timestamps
  - Data validation during import process
  - User-friendly backup guide and instructions

### 7. Technical Analysis Module (technical_analysis.py)
- **Purpose**: Advanced technical analysis for automatic target price calculation and breakout detection
- **Key Features**:
  - Support and resistance level calculation using pivot points
  - Daily closing price monitoring for breakout detection
  - Automatic target price setting based on technical levels
  - Real-time breakout alerts and email notifications
  - Integration with buy/sell watchlists for enhanced analysis

## Data Flow

1. **User Input**: User enters stock symbols and target prices through Streamlit UI
2. **Data Validation**: Application validates stock symbols and ensures no duplicates
3. **API Call**: yfinance fetches real-time data from Yahoo Finance for NSE stocks
4. **Data Processing**: Raw data is processed, formatted, and cached
5. **Display**: Processed data is displayed in the dashboard with appropriate formatting
6. **Database Storage**: Watchlist changes are permanently stored in PostgreSQL database
7. **Notification Logging**: Email alerts and app notifications are logged to database

## External Dependencies

### Core Libraries
- **streamlit**: Web application framework
- **pandas**: Data manipulation and analysis
- **yfinance**: Yahoo Finance API wrapper for stock data
- **datetime**: Date and time handling
- **sqlalchemy**: Database ORM for PostgreSQL integration
- **psycopg2-binary**: PostgreSQL database adapter for Python
- **smtplib**: Built-in Python library for email notifications

### Data Sources
- **Yahoo Finance**: Primary data source for NSE stock prices and historical data
- **NSE Integration**: Automatic handling of NSE stock symbols with .NS suffix
- **PostgreSQL Database**: Persistent storage for user watchlists and notification logs

## Deployment Strategy

### Current Setup
- **Platform**: Designed for Streamlit deployment
- **Configuration**: Page configuration optimized for wide layout
- **Caching**: Implements data caching for performance optimization

### Scalability Considerations
- **Caching**: 30-second TTL on stock data to balance real-time needs with API limits
- **Database Management**: PostgreSQL with connection pooling for efficient data operations
- **Error Handling**: Graceful error handling for API failures and database connectivity issues
- **Email Rate Limiting**: Notification system prevents spam with time-based restrictions

### Recent Enhancements
- **Database Integration**: ✅ Implemented PostgreSQL persistent storage for watchlists
- **Email Notification System**: ✅ Added email alerts for stocks within 1% of target price
- **Enhanced Analytics**: ✅ Real-time watchlist statistics and notification logging
- **Improved Thresholds**: ✅ Updated "close to target" threshold from 5% to 1%
- **Data Backup System**: ✅ Added export/import functionality to preserve data beyond free trial
- **User Data Protection**: ✅ Complete backup guide and automated reminder system
- **Technical Analysis Integration**: ✅ Added automatic support/resistance level detection
- **Daily Closing Price Monitoring**: ✅ Real-time breakout detection and email alerts
- **Alert Range Update**: ✅ Updated alert threshold to -1% to +1% range per user request
- **Technical Analysis Removal**: ✅ Removed technical analysis features - user prefers manual target entry

### Future Enhancement Opportunities
- **User Authentication**: Multi-user support with personalized watchlists
- **Real-time Updates**: WebSocket connections for live price updates
- **Export Functionality**: CSV/Excel export capabilities for watchlists
- **Advanced Analytics**: Price trend analysis and prediction features

## Architecture Decisions

### Technology Choices
1. **Streamlit over Flask/Django**: Chosen for rapid development and built-in data visualization capabilities
2. **yfinance over paid APIs**: Cost-effective solution for stock data with sufficient accuracy
3. **PostgreSQL Database**: Reliable persistent storage for production-ready data management
4. **Pandas for Data Processing**: Industry standard for financial data manipulation

### Design Patterns
1. **Separation of Concerns**: Stock utilities separated from UI logic
2. **Caching Strategy**: Balances performance with data freshness
3. **Error Handling**: Graceful degradation when stock data is unavailable
4. **State Management**: Centralized session state management for consistency