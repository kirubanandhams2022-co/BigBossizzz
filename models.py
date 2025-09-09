from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='participant')  # 'host', 'participant', 'admin'
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    profile_picture = db.Column(db.String(200), default='default.png')
    
    # Relationships
    created_quizzes = db.relationship('Quiz', backref='creator', lazy=True, cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', backref='participant', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_verification_token(self):
        self.verification_token = secrets.token_urlsafe(32)
        return self.verification_token
    
    def verify_email(self, token):
        if self.verification_token == token:
            self.is_verified = True
            self.verification_token = None
            return True
        return False
    
    def is_host(self):
        return self.role == 'host'
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_participant(self):
        return self.role == 'participant'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_limit = db.Column(db.Integer, default=60)  # in minutes
    is_active = db.Column(db.Boolean, default=True)
    proctoring_enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # New columns for advanced features
    allow_view_responses = db.Column(db.Boolean, default=True)
    auto_generate_from_upload = db.Column(db.Boolean, default=False)
    draft_from_upload_id = db.Column(db.Integer, db.ForeignKey('upload_record.id'))
    is_deleted = db.Column(db.Boolean, default=False)
    
    # Security settings
    max_violations_allowed = db.Column(db.Integer, default=3)
    auto_terminate_on_violation = db.Column(db.Boolean, default=True)
    face_detection_required = db.Column(db.Boolean, default=True)
    screen_recording_required = db.Column(db.Boolean, default=False)
    browser_lockdown = db.Column(db.Boolean, default=True)
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')  # 'multiple_choice', 'text', 'true_false'
    points = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer, default=0)
    
    # Relationships
    options = db.relationship('QuestionOption', backref='question', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def get_shuffled_options(self):
        """Return shuffled options for this question"""
        import random
        options = list(self.options)
        random.shuffle(options)
        return options
    
    def __repr__(self):
        return f'<Question {self.id}>'

class QuestionOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    option_text = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Option {self.option_text}>'

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    score = db.Column(db.Float)
    total_points = db.Column(db.Integer)
    status = db.Column(db.String(20), default='in_progress')  # 'in_progress', 'completed', 'abandoned', 'terminated'
    
    # Relationships
    answers = db.relationship('Answer', backref='attempt', lazy=True, cascade='all, delete-orphan')
    
    def calculate_score(self):
        correct_answers = 0
        total_points = 0
        
        for answer in self.answers:
            total_points += answer.question.points
            if answer.is_correct:
                correct_answers += answer.question.points
        
        self.score = (correct_answers / total_points * 100) if total_points > 0 else 0
        self.total_points = total_points
        return self.score
    
    def __repr__(self):
        return f'<Attempt {self.id}>'

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('question_option.id'))
    text_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Answer {self.id}>'

class ProctoringEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'tab_switch', 'window_blur', 'multiple_faces', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)  # Additional event details
    severity = db.Column(db.String(20), default='low')  # 'low', 'medium', 'high'
    
    def __repr__(self):
        return f'<ProctoringEvent {self.event_type}>'

class LoginEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # IPv6 support
    user_agent = db.Column(db.Text)
    device_info = db.Column(db.Text)  # Browser, OS details
    location_data = db.Column(db.Text)  # Location if available
    is_suspicious = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('login_events', lazy=True))
    
    def __repr__(self):
        return f'<LoginEvent {self.user_id} at {self.login_time}>'

class UserViolation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    violation_count = db.Column(db.Integer, default=0)
    is_flagged = db.Column(db.Boolean, default=False)
    flagged_at = db.Column(db.DateTime)
    flagged_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Admin who flagged
    can_retake = db.Column(db.Boolean, default=False)
    retake_approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    retake_approved_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('violations', lazy=True))
    flagged_by_admin = db.relationship('User', foreign_keys=[flagged_by])
    approved_by_admin = db.relationship('User', foreign_keys=[retake_approved_by])
    
    def __repr__(self):
        return f'<UserViolation {self.user_id} - {self.violation_count} violations>'

# New models for advanced features

class UploadRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    mime_type = db.Column(db.String(100))
    stored_path = db.Column(db.String(500))
    parsed = db.Column(db.Boolean, default=False)
    parsed_to_quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    candidate_questions_json = db.Column(db.Text)  # JSON string of candidate questions
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    host = db.relationship('User', backref='uploads')
    
    def __repr__(self):
        return f'<UploadRecord {self.filename}>'

class DeviceLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.Text)
    device_type = db.Column(db.String(50))
    browser_info = db.Column(db.Text)
    screen_resolution = db.Column(db.String(20))
    timezone = db.Column(db.String(50))
    logged_in_at = db.Column(db.DateTime, default=datetime.utcnow)
    session_duration = db.Column(db.Integer)  # in minutes
    is_suspicious = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', backref='device_logs')
    quiz = db.relationship('Quiz', backref='device_logs')
    
    def __repr__(self):
        return f'<DeviceLog {self.user_id}-{self.ip_address}>'

class SecurityAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'))
    alert_type = db.Column(db.String(50), nullable=False)  # 'multiple_faces', 'suspicious_behavior', 'device_change', etc.
    severity = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    description = db.Column(db.Text)
    auto_action_taken = db.Column(db.String(100))  # 'warning_sent', 'quiz_terminated', 'flagged_for_review'
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='security_alerts')
    quiz = db.relationship('Quiz', backref='security_alerts')
    attempt = db.relationship('QuizAttempt', backref='security_alerts')
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f'<SecurityAlert {self.alert_type}-{self.severity}>'
