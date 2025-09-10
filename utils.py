from datetime import datetime

def get_time_greeting():
    """Get time-based greeting based on current hour"""
    current_hour = datetime.now().hour
    
    if 0 <= current_hour < 12:
        return "Good Morning"
    elif 12 <= current_hour < 17:
        return "Good Afternoon"
    elif 17 <= current_hour <= 23:
        return "Good Evening"
    else:
        return "Good Night"

def get_greeting_icon():
    """Get greeting icon based on current time"""
    current_hour = datetime.now().hour
    
    if 0 <= current_hour < 12:
        return "🌅"
    elif 12 <= current_hour < 17:
        return "☀️"
    elif 17 <= current_hour <= 23:
        return "🌆"
    else:
        return "🌙"