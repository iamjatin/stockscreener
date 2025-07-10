import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_email_notification(stock_symbol, current_price, target_price, watchlist_type, recipient_email, notification_reason="close_to_target"):
    """
    Send email notification when stock reaches target conditions
    """
    try:
        # Email configuration (using Gmail SMTP)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # You'll need to set up app-specific password for Gmail
        sender_email = "your_app_email@gmail.com"  # This would need to be configured
        sender_password = "your_app_password"  # This would need to be configured
        
        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = f"Stock Alert: {stock_symbol} is close to your target!"
        
        # Email body based on notification reason
        if notification_reason == "support_broken":
            action_word = "Sell"
            alert_type = "Support Level Broken"
            body = f"""
            Hi,
            
            ALERT: {stock_symbol} has broken below its support level!
            
            Current Closing Price: ₹{current_price:.2f}
            Support Level: ₹{target_price:.2f}
            Action: Consider selling immediately
            Alert Type: Daily close below support
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            This is an automated technical analysis alert from your NSE Stock Dashboard.
            
            Best regards,
            Your Stock Dashboard
            """
        elif notification_reason == "resistance_broken":
            action_word = "Buy"
            alert_type = "Resistance Level Broken"
            body = f"""
            Hi,
            
            ALERT: {stock_symbol} has broken above its resistance level!
            
            Current Closing Price: ₹{current_price:.2f}
            Resistance Level: ₹{target_price:.2f}
            Action: Consider buying on momentum
            Alert Type: Daily close above resistance
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            This is an automated technical analysis alert from your NSE Stock Dashboard.
            
            Best regards,
            Your Stock Dashboard
            """
        else:
            # Default close to target notification
            percentage_diff = abs(((current_price - target_price) / target_price) * 100)
            action_word = "Buy" if watchlist_type == "buy" else "Sell"
            alert_type = "Close to Target"
            
            body = f"""
            Hi,
            
            Your stock {stock_symbol} is now close to your target price!
            
            Current Price: ₹{current_price:.2f}
            Your Target Price: ₹{target_price:.2f}
            Difference: {percentage_diff:.2f}%
            Action: Consider {action_word.lower()}ing
            
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            This is an automated notification from your NSE Stock Dashboard.
            
            Best regards,
            Your Stock Dashboard
            """
        
        message.attach(MIMEText(body, "plain"))
        
        # Connect to server and send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        
        return True, "Email sent successfully!"
        
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def check_email_notifications(watchlist_data, watchlist_type, recipient_email):
    """
    Check if any stocks need email notifications and send them
    """
    notifications_sent = []
    
    # Initialize session state for tracking sent notifications
    if 'email_notifications_sent' not in st.session_state:
        st.session_state.email_notifications_sent = set()
    
    for stock_data in watchlist_data:
        if stock_data.get('Status') == '🔥 CLOSE TO TARGET':
            # Create unique key for this notification
            notification_key = f"{stock_data['Symbol']}_{watchlist_type}_{datetime.now().strftime('%Y-%m-%d_%H')}"
            
            # Only send one notification per stock per hour
            if notification_key not in st.session_state.email_notifications_sent:
                # Extract price values (remove ₹ symbol and convert to float)
                current_price_str = stock_data['Current Price'].replace('₹', '')
                target_price_str = stock_data['Target Price'].replace('₹', '')
                
                try:
                    current_price = float(current_price_str)
                    target_price = float(target_price_str)
                    
                    # Send email notification (this would work if email credentials were set up)
                    success, message = send_email_notification(
                        stock_data['Symbol'], 
                        current_price, 
                        target_price, 
                        watchlist_type, 
                        recipient_email
                    )
                    
                    if success:
                        st.session_state.email_notifications_sent.add(notification_key)
                        notifications_sent.append(stock_data['Symbol'])
                        
                except ValueError:
                    # Handle price parsing errors
                    pass
    
    return notifications_sent

def setup_email_notifications():
    """
    Setup email notification configuration in sidebar
    """
    st.sidebar.subheader("📧 Email Notifications")
    
    # Email configuration
    email_enabled = st.sidebar.checkbox("Enable Email Alerts")
    
    if email_enabled:
        recipient_email = st.sidebar.text_input(
            "Your Email", 
            value="jatin.infomail@gmail.com",
            help="Email address to receive notifications when stocks are within -1% to +1% of target"
        )
        
        st.sidebar.info("📧 You'll get email alerts when stocks are within -1% to +1% of your target price!")
        st.sidebar.warning("⚠️ Note: Email feature requires email server configuration. Currently showing notifications in the app only.")
        
        return email_enabled, recipient_email
    
    return False, None


def send_technical_breakout_alert(stock_symbol, closing_price, target_price, watchlist_type, recipient_email):
    """
    Send email alert for technical breakouts (support/resistance breaks)
    """
    if watchlist_type == "sell":
        notification_reason = "support_broken"
    else:  # buy
        notification_reason = "resistance_broken"
    
    return send_email_notification(
        stock_symbol, closing_price, target_price, watchlist_type, 
        recipient_email, notification_reason
    )