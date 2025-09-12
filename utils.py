from datetime import datetime, timezone, timedelta

def get_time_greeting():
    """Get time-based greeting based on user's local time"""
    # Use UTC+5:30 (IST) as default timezone for better user experience
    # In production, this should be configurable per user
    user_timezone = timezone(timedelta(hours=5, minutes=30))
    current_hour = datetime.now(user_timezone).hour
    
    if 5 <= current_hour < 12:
        return "Good Morning"
    elif 12 <= current_hour < 17:
        return "Good Afternoon"
    elif 17 <= current_hour < 21:
        return "Good Evening"
    else:
        return "Good Night"

def get_greeting_icon():
    """Get greeting icon based on user's local time"""
    # Use UTC+5:30 (IST) as default timezone for better user experience
    user_timezone = timezone(timedelta(hours=5, minutes=30))
    current_hour = datetime.now(user_timezone).hour
    
    if 5 <= current_hour < 12:
        return "🌅"
    elif 12 <= current_hour < 17:
        return "☀️"
    elif 17 <= current_hour < 21:
        return "🌆"
    else:
        return "🌙"