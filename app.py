import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
import redis
# Simple ProxyFix implementation for compatibility
class ProxyFix:
    def __init__(self, app, x_proto=1, x_host=1):
        self.app = app
        
    def __call__(self, environ, start_response):
        return self.app(environ, start_response)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
mail = Mail()
socketio = SocketIO()

# Redis connection for real-time features
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()  # Test connection
except:
    redis_client = None  # Fallback to in-memory storage

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database with performance optimizations
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://localhost/proctoring_db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Disable event system for performance

# Configure email
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')

# Initialize extensions
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)
socketio.init_app(app, async_mode='eventlet', cors_allowed_origins="*", message_queue=f'redis://localhost:6379/0' if redis_client else None)

# Configure login manager  
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    try:
        # Import User lazily to avoid circular imports
        from models import User
        return User.query.get(int(user_id))
    except (ValueError, TypeError, ImportError):
        return None

with app.app_context():
    # Import models once to ensure tables are created
    try:
        import models
        db.create_all()
        
        # Use the already imported User model
        User = models.User
    except Exception as e:
        logging.error(f"Database initialization error: {e}")
        # Import User as fallback
        from models import User
    
    # Default Admin Account
    if not User.query.filter_by(email='admin@platform.com').first():
        admin = User()
        admin.username = 'admin'
        admin.email = 'admin@platform.com'
        admin.role = 'admin'
        admin.set_password('admin123')
        admin.is_verified = True
        db.session.add(admin)
    
    # Default Host Account
    if not User.query.filter_by(email='host@platform.com').first():
        host = User()
        host.username = 'host'
        host.email = 'host@platform.com'
        host.role = 'host'
        host.set_password('host123')
        host.is_verified = True
        db.session.add(host)
    
    # Default Participant Account
    if not User.query.filter_by(email='participant@platform.com').first():
        participant = User()
        participant.username = 'participant'
        participant.email = 'participant@platform.com'
        participant.role = 'participant'
        participant.set_password('participant123')
        participant.is_verified = True
        db.session.add(participant)
    
    db.session.commit()

# Import routes
from routes import *

# Only define run functionality if needed
def run_app():
    """Start the application server"""
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logging.error(f"Failed to start application: {e}")

if __name__ == '__main__':
    run_app()
