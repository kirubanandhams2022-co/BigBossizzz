"""
Real-time BigBossizzz Application with WebSocket Support
This replaces the basic Flask app with Flask-SocketIO for real-time functionality
"""

import os
import logging
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_mail import Mail, Message
from sqlalchemy.orm import DeclarativeBase
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
except ImportError:
    ProxyFix = None

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
mail = Mail()

# Create the app with SocketIO support
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
if ProxyFix:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

# Initialize extensions
db.init_app(app)
mail.init_app(app)

# Initialize SocketIO with eventlet for real-time support
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import models and routes
with app.app_context():
    import models
    import routes
    db.create_all()

# Real-time WebSocket Events
@socketio.on('connect')
def on_connect(auth):
    """Handle client connection"""
    if current_user.is_authenticated:
        join_room(f"user_{current_user.id}")
        if current_user.is_host() or current_user.is_admin():
            join_room("monitors")  # Room for hosts and admins
        logging.info(f"User {current_user.username} connected to real-time monitoring")
        emit('status', {'msg': f'Welcome {current_user.username}!'})
    else:
        disconnect()

@socketio.on('disconnect')
def on_disconnect():
    """Handle client disconnection"""
    if current_user.is_authenticated:
        leave_room(f"user_{current_user.id}")
        if current_user.is_host() or current_user.is_admin():
            leave_room("monitors")
        logging.info(f"User {current_user.username} disconnected")

@socketio.on('violation_alert')
def handle_violation_alert(data):
    """Handle real-time violation alerts"""
    if current_user.is_authenticated:
        try:
            # Log the violation to database
            from models import ProctoringEvent
            
            violation = ProctoringEvent(
                attempt_id=data.get('attemptId'),
                event_type=data.get('violationType', 'unknown'),
                details=data.get('message', 'Real-time violation detected'),
                severity=data.get('severity', 'medium')
            )
            db.session.add(violation)
            db.session.commit()
            
            # Send real-time alert to all monitors (hosts and admins)
            socketio.emit('new_violation', {
                'student': data.get('student', {}),
                'violation': data.get('message', 'Violation detected'),
                'severity': data.get('severity', 'medium'),
                'timestamp': datetime.utcnow().isoformat(),
                'attemptId': data.get('attemptId')
            }, to='monitors')
            
            # Send email for high severity violations
            if data.get('severity') == 'high':
                send_violation_email(data)
            
        except Exception as e:
            logging.error(f"Error handling violation alert: {e}")

@socketio.on('join_monitoring')
def on_join_monitoring(data):
    """Allow hosts/admins to join monitoring room"""
    if current_user.is_authenticated and (current_user.is_host() or current_user.is_admin()):
        join_room('monitors')
        emit('status', {'msg': 'Joined live monitoring room'})

def send_violation_email(data):
    """Send email notification for high severity violations"""
    try:
        from models import QuizAttempt, Quiz, User
        
        attempt_id = data.get('attemptId')
        attempt = QuizAttempt.query.get(attempt_id)
        if attempt:
            quiz = attempt.quiz
            host = quiz.creator
            student = attempt.participant
            
            msg = Message(
                subject=f'🚨 URGENT: Quiz Violation Alert - {student.username}',
                recipients=[host.email],
                body=f'''
URGENT VIOLATION ALERT

Student: {student.username} ({student.email})
Quiz: {quiz.title}
Violation: {data.get('message', 'Unknown violation')}
Severity: {data.get('severity', 'high').upper()}
Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please check the live monitoring dashboard immediately.
                '''
            )
            mail.send(msg)
            logging.info(f"Violation email sent to {host.email}")
            
    except Exception as e:
        logging.error(f"Failed to send violation email: {e}")

if __name__ == '__main__':
    # Use socketio.run for real-time support
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)