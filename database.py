import os
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Watchlist(Base):
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    target_price = Column(Float, nullable=False)
    watchlist_type = Column(String, nullable=False)  # 'buy' or 'sell'
    added_date = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    user_id = Column(String, default="default_user")  # For future multi-user support

class NotificationLog(Base):
    __tablename__ = "notification_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    watchlist_type = Column(String, nullable=False)
    current_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    notification_type = Column(String, nullable=False)  # 'email', 'app'
    sent_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, default="default_user")

def init_database():
    """Initialize the database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        st.error(f"Failed to initialize database: {e}")
        return False

def get_db_session():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def add_stock_to_db(symbol, target_price, watchlist_type, user_id="default_user"):
    """Add a stock to the database watchlist"""
    db = get_db_session()
    if not db:
        return False, "Database connection failed"
    
    try:
        # Check if stock already exists
        existing = db.query(Watchlist).filter(
            Watchlist.symbol == symbol.upper(),
            Watchlist.watchlist_type == watchlist_type,
            Watchlist.user_id == user_id,
            Watchlist.is_active == True
        ).first()
        
        if existing:
            db.close()
            return False, f"{symbol.upper()} already exists in {watchlist_type} watchlist"
        
        # Add new stock
        new_stock = Watchlist(
            symbol=symbol.upper(),
            target_price=target_price,
            watchlist_type=watchlist_type,
            user_id=user_id
        )
        
        db.add(new_stock)
        db.commit()
        db.close()
        return True, f"Added {symbol.upper()} to {watchlist_type} watchlist"
        
    except Exception as e:
        db.close()
        return False, f"Error adding stock: {e}"

def get_watchlist_from_db(watchlist_type, user_id="default_user"):
    """Get watchlist from database"""
    db = get_db_session()
    if not db:
        return []
    
    try:
        stocks = db.query(Watchlist).filter(
            Watchlist.watchlist_type == watchlist_type,
            Watchlist.user_id == user_id,
            Watchlist.is_active == True
        ).order_by(Watchlist.added_date.desc()).all()
        
        result = []
        for stock in stocks:
            result.append({
                'id': stock.id,
                'symbol': stock.symbol,
                'target_price': stock.target_price,
                'added_date': stock.added_date.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        db.close()
        return result
        
    except Exception as e:
        db.close()
        st.error(f"Error fetching watchlist: {e}")
        return []

def remove_stock_from_db(symbol, watchlist_type, user_id="default_user"):
    """Remove a stock from the database watchlist"""
    db = get_db_session()
    if not db:
        return False, "Database connection failed"
    
    try:
        stock = db.query(Watchlist).filter(
            Watchlist.symbol == symbol,
            Watchlist.watchlist_type == watchlist_type,
            Watchlist.user_id == user_id,
            Watchlist.is_active == True
        ).first()
        
        if stock:
            stock.is_active = False  # Soft delete
            db.commit()
            db.close()
            return True, f"Removed {symbol} from {watchlist_type} watchlist"
        else:
            db.close()
            return False, f"Stock {symbol} not found in {watchlist_type} watchlist"
            
    except Exception as e:
        db.close()
        return False, f"Error removing stock: {e}"

def log_notification(symbol, watchlist_type, current_price, target_price, notification_type, user_id="default_user"):
    """Log notification to database"""
    db = get_db_session()
    if not db:
        return False
    
    try:
        notification = NotificationLog(
            symbol=symbol,
            watchlist_type=watchlist_type,
            current_price=current_price,
            target_price=target_price,
            notification_type=notification_type,
            user_id=user_id
        )
        
        db.add(notification)
        db.commit()
        db.close()
        return True
        
    except Exception as e:
        db.close()
        st.error(f"Error logging notification: {e}")
        return False

def get_recent_notifications(user_id="default_user", hours=24):
    """Get recent notifications from database"""
    db = get_db_session()
    if not db:
        return []
    
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        notifications = db.query(NotificationLog).filter(
            NotificationLog.user_id == user_id,
            NotificationLog.sent_at >= cutoff_time
        ).order_by(NotificationLog.sent_at.desc()).all()
        
        result = []
        for notif in notifications:
            result.append({
                'symbol': notif.symbol,
                'watchlist_type': notif.watchlist_type,
                'current_price': notif.current_price,
                'target_price': notif.target_price,
                'notification_type': notif.notification_type,
                'sent_at': notif.sent_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        db.close()
        return result
        
    except Exception as e:
        db.close()
        st.error(f"Error fetching notifications: {e}")
        return []

@st.cache_data(ttl=5)
def get_watchlist_stats(user_id="default_user"):
    """Get watchlist statistics"""
    db = get_db_session()
    if not db:
        return {"buy_count": 0, "sell_count": 0, "total_stocks": 0}
    
    try:
        buy_count = db.query(Watchlist).filter(
            Watchlist.watchlist_type == "buy",
            Watchlist.user_id == user_id,
            Watchlist.is_active == True
        ).count()
        
        sell_count = db.query(Watchlist).filter(
            Watchlist.watchlist_type == "sell",
            Watchlist.user_id == user_id,
            Watchlist.is_active == True
        ).count()
        
        db.close()
        return {
            "buy_count": buy_count,
            "sell_count": sell_count,
            "total_stocks": buy_count + sell_count
        }
        
    except Exception as e:
        db.close()
        return {"buy_count": 0, "sell_count": 0, "total_stocks": 0}