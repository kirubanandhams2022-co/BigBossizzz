from datetime import datetime
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import json
from sqlalchemy.ext.hybrid import hybrid_property

# New Course Management System
class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    code = db.Column(db.String(20), unique=True, nullable=False)
    max_participants = db.Column(db.Integer, default=100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)  # For drag-and-drop ordering
    
    # Relationships
    host_assignments = db.relationship('HostCourseAssignment', backref='course', lazy=True, cascade='all, delete-orphan')
    participant_enrollments = db.relationship('ParticipantEnrollment', backref='course', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='course', lazy=True)
    
    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'

class HostCourseAssignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    host = db.relationship('User', foreign_keys=[host_id], backref='host_course_assignments')
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by])
    
    def __repr__(self):
        return f'<HostAssignment {self.host_id}->{self.course_id}>'

class ParticipantEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    enrolled_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    participant = db.relationship('User', foreign_keys=[participant_id], backref='course_enrollments')
    enrolled_by_user = db.relationship('User', foreign_keys=[enrolled_by])
    
    def __repr__(self):
        return f'<Enrollment {self.participant_id}->{self.course_id}>'

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
    
    # LTI Integration fields
    lti_user_id = db.Column(db.String(255), unique=True, index=True)  # LTI user identifier
    lti_consumer_key = db.Column(db.String(255))  # LMS consumer key
    lti_context_id = db.Column(db.String(255))  # Course/context identifier
    lti_resource_link_id = db.Column(db.String(255))  # Specific resource link
    lti_grade_passback_url = db.Column(db.String(500))  # Grade passback service URL
    lti_result_sourcedid = db.Column(db.String(255))  # Grade passback identifier
    
    # Relationships
    created_quizzes = db.relationship('Quiz', backref='creator', lazy=True, cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', backref='participant', lazy=True, cascade='all, delete-orphan')
    user_roles = db.relationship('UserRole', foreign_keys='UserRole.user_id', backref='user', lazy=True, cascade='all, delete-orphan')
    
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
    
    
    # New RBAC methods
    def has_permission(self, permission_name):
        """Check if user has a specific permission through their roles"""
        try:
            for user_role in self.user_roles:
                if user_role.role:
                    for role_permission in user_role.role.role_permissions:
                        if role_permission.permission and role_permission.permission.name == permission_name:
                            return True
        except Exception:
            pass
        return False
    
    def has_any_permission(self, permission_names):
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(perm) for perm in permission_names)
    
    def has_all_permissions(self, permission_names):
        """Check if user has all of the specified permissions"""
        return all(self.has_permission(perm) for perm in permission_names)
    
    def get_all_permissions(self):
        """Get all permissions for this user through their roles"""
        permissions = set()
        try:
            for user_role in self.user_roles:
                if user_role.role:
                    for role_permission in user_role.role.role_permissions:
                        if role_permission.permission:
                            permissions.add(role_permission.permission.name)
        except Exception:
            pass
        return list(permissions)
    
    def add_role(self, role_name):
        """Add a role to this user"""
        from models import Role, UserRole  # Import here to avoid circular imports
        role = Role.query.filter_by(name=role_name).first()
        if role and not self.has_role(role_name):
            user_role = UserRole()
            user_role.user_id = self.id
            user_role.role_id = role.id
            db.session.add(user_role)
            return True
        return False
    
    def remove_role(self, role_name):
        """Remove a role from this user"""
        from models import Role, UserRole  # Import here to avoid circular imports
        role = Role.query.filter_by(name=role_name).first()
        if role:
            user_role = UserRole.query.filter_by(user_id=self.id, role_id=role.id).first()
            if user_role:
                db.session.delete(user_role)
                return True
        return False
    
    def has_role(self, role_name):
        """Check if user has a specific role"""
        try:
            return any(ur.role.name == role_name for ur in self.user_roles if ur.role)
        except Exception:
            return False
    
    def get_roles(self):
        """Get all role names for this user"""
        try:
            return [ur.role.name for ur in self.user_roles if ur.role]
        except Exception:
            return []
    
    # Legacy role methods for backward compatibility with safety checks
    def is_admin(self):
        try:
            return self.has_role('admin') if hasattr(self, 'user_roles') and self.user_roles else False
        except:
            pass
        return self.role == 'admin'
    
    def is_host(self):
        try:
            return self.has_role('host') if hasattr(self, 'user_roles') and self.user_roles else False
        except:
            pass
        return self.role == 'host'
    
    def is_participant(self):
        try:
            return self.has_role('participant') if hasattr(self, 'user_roles') and self.user_roles else False
        except:
            pass
        return self.role == 'participant'
    
    def __repr__(self):
        return f'<User {self.username}>'

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)  # Add course relationship
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
    
    # Ordering for drag-and-drop
    display_order = db.Column(db.Integer, default=0)  # For course-level quiz ordering
    
    # Relationships
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Quiz {self.title}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), default='multiple_choice')  # 'multiple_choice', 'text', 'true_false', 'code_submission', 'file_upload', 'drawing'
    points = db.Column(db.Integer, default=1)
    order = db.Column(db.Integer, default=0)
    
    # Advanced question type specific fields
    programming_language = db.Column(db.String(50))  # For code_submission: 'python', 'javascript', 'java', etc.
    starter_code = db.Column(db.Text)  # For code_submission: initial code template
    allowed_file_types = db.Column(db.String(200))  # For file_upload: 'pdf,docx,jpg,png'
    max_file_size_mb = db.Column(db.Integer, default=10)  # For file_upload: max size in MB
    canvas_width = db.Column(db.Integer, default=800)  # For drawing: canvas dimensions
    canvas_height = db.Column(db.Integer, default=600)  # For drawing: canvas dimensions
    sample_output = db.Column(db.Text)  # For code_submission: expected output example
    
    # Relationships
    options = db.relationship('QuestionOption', backref='question', lazy=True, cascade='all, delete-orphan')
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')
    
    def get_shuffled_options(self):
        """Return shuffled options for this question"""
        import random
        from app import db
        options = db.session.query(QuestionOption).filter_by(question_id=self.id).all()
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
    force_submitted = db.Column(db.Boolean, default=False)
    termination_reason = db.Column(db.Text)
    is_flagged = db.Column(db.Boolean, default=False)
    
    # Relationships (participant and quiz backrefs are defined in User and Quiz models)
    answers = db.relationship('Answer', backref='attempt', lazy=True, cascade='all, delete-orphan')
    
    def calculate_score(self):
        correct_answers = 0
        total_points = 0
        
        from app import db
        # Get answers with their associated questions
        answers_with_questions = db.session.query(Answer, Question).join(
            Question, Answer.question_id == Question.id
        ).filter(Answer.attempt_id == self.id).all()
        
        for answer, question in answers_with_questions:
            total_points += question.points
            if answer.is_correct:
                correct_answers += question.points
        
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
    
    # Advanced answer types
    code_submission = db.Column(db.Text)  # For programming code answers
    uploaded_file_path = db.Column(db.String(500))  # File path for uploaded files
    uploaded_file_name = db.Column(db.String(200))  # Original filename
    uploaded_file_size = db.Column(db.Integer)  # File size in bytes
    drawing_data = db.Column(db.Text)  # JSON data for drawing/canvas answers
    execution_output = db.Column(db.Text)  # For code execution results
    execution_error = db.Column(db.Text)  # For code execution errors
    
    def __repr__(self):
        return f'<Answer {self.id}>'

class ProctoringEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # 'tab_switch', 'window_blur', 'multiple_faces', etc.
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.Text)  # Additional event details
    severity = db.Column(db.String(20), default='low')  # 'low', 'medium', 'high'
    description = db.Column(db.Text)  # Add description field
    
    # Add the missing relationship
    attempt = db.relationship('QuizAttempt', backref='proctoring_events', lazy=True)
    
    def __repr__(self):
        return f'<ProctoringEvent {self.event_type}>'

class AlertThreshold(db.Model):
    """Model to store customizable alert thresholds for proctoring events"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # Human readable name
    event_type = db.Column(db.String(50), nullable=False)  # 'tab_switch', 'window_blur', etc.
    
    # Threshold settings
    low_threshold = db.Column(db.Integer, default=5)     # Count for low severity
    medium_threshold = db.Column(db.Integer, default=3)  # Count for medium severity  
    high_threshold = db.Column(db.Integer, default=1)    # Count for high severity
    
    # Time window for counting events (in minutes)
    time_window = db.Column(db.Integer, default=10)
    
    # Actions to take when threshold is exceeded
    send_alert = db.Column(db.Boolean, default=True)
    notify_proctor = db.Column(db.Boolean, default=True)
    auto_flag_attempt = db.Column(db.Boolean, default=False)
    auto_terminate = db.Column(db.Boolean, default=False)
    
    # Scope settings
    is_global = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    creator = db.relationship('User', backref='created_thresholds')
    quiz_overrides = db.relationship('QuizThresholdOverride', backref='threshold', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<AlertThreshold {self.name}>'

class QuizThresholdOverride(db.Model):
    """Model to override global thresholds for specific quizzes"""
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    threshold_id = db.Column(db.Integer, db.ForeignKey('alert_threshold.id'), nullable=False)
    
    # Override values (NULL means use global threshold)
    low_threshold = db.Column(db.Integer, nullable=True)
    medium_threshold = db.Column(db.Integer, nullable=True)
    high_threshold = db.Column(db.Integer, nullable=True)
    time_window = db.Column(db.Integer, nullable=True)
    
    # Action overrides
    send_alert = db.Column(db.Boolean, nullable=True)
    notify_proctor = db.Column(db.Boolean, nullable=True)
    auto_flag_attempt = db.Column(db.Boolean, nullable=True)
    auto_terminate = db.Column(db.Boolean, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz = db.relationship('Quiz', backref='threshold_overrides')
    
    def __repr__(self):
        return f'<QuizThresholdOverride Quiz:{self.quiz_id} Threshold:{self.threshold_id}>'

class AlertTrigger(db.Model):
    """Model to log when alert thresholds are exceeded"""
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    threshold_id = db.Column(db.Integer, db.ForeignKey('alert_threshold.id'), nullable=False)
    
    # Event details
    event_type = db.Column(db.String(50), nullable=False)
    trigger_count = db.Column(db.Integer, nullable=False)  # Number of events that triggered this
    severity_level = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high'
    
    # Actions taken
    alert_sent = db.Column(db.Boolean, default=False)
    proctor_notified = db.Column(db.Boolean, default=False)
    attempt_flagged = db.Column(db.Boolean, default=False)
    attempt_terminated = db.Column(db.Boolean, default=False)
    
    # Metadata
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    attempt = db.relationship('QuizAttempt', backref='alert_triggers')
    threshold = db.relationship('AlertThreshold', backref='triggered_alerts')
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f'<AlertTrigger {self.event_type} - {self.severity_level}>'

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

class CollaborationSignal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    signal_type = db.Column(db.String(50), nullable=False)  # 'answer_similarity', 'simultaneous_answers', 'timing_correlation', 'shared_ip'
    score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    severity = db.Column(db.String(20), default='info')  # 'info', 'warn', 'high'
    participants = db.Column(db.JSON)  # Array of user_ids involved
    window_start = db.Column(db.DateTime)
    window_end = db.Column(db.DateTime)
    details = db.Column(db.JSON)  # Additional signal details
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open')  # 'open', 'acknowledged', 'resolved'
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    resolved_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    # Relationships
    quiz = db.relationship('Quiz', backref='collaboration_signals')
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    def __repr__(self):
        return f'<CollaborationSignal {self.signal_type} for quiz {self.quiz_id}>'

class AttemptSimilarity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    attempt_a_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    attempt_b_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    jaccard_score = db.Column(db.Float, default=0.0)
    timing_correlation = db.Column(db.Float, default=0.0)
    coanswer_count = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz = db.relationship('Quiz', backref='attempt_similarities')
    attempt_a = db.relationship('QuizAttempt', foreign_keys=[attempt_a_id])
    attempt_b = db.relationship('QuizAttempt', foreign_keys=[attempt_b_id])
    
    # Ensure unique combination
    __table_args__ = (db.UniqueConstraint('quiz_id', 'attempt_a_id', 'attempt_b_id', name='uq_attempt_similarity'),)
    
    def __repr__(self):
        return f'<AttemptSimilarity {self.attempt_a_id}-{self.attempt_b_id}: {self.jaccard_score}>'

# Real-time Collaboration Heatmap Models
class InteractionEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=True)
    event_type = db.Column(db.String(50), nullable=False)  # 'click', 'focus', 'scroll', 'hover', 'answer_change'
    element_selector = db.Column(db.String(200))  # CSS selector or element identifier
    x_coordinate = db.Column(db.Integer)  # Click/hover position
    y_coordinate = db.Column(db.Integer)
    viewport_width = db.Column(db.Integer)
    viewport_height = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    duration = db.Column(db.Float)  # For focus/hover events - time spent
    event_metadata = db.Column(db.Text)  # JSON metadata for additional context
    
    # Relationships
    attempt = db.relationship('QuizAttempt', backref='interaction_events')
    question = db.relationship('Question', backref='interaction_events')
    
    def __repr__(self):
        return f'<InteractionEvent {self.event_type} on Question {self.question_id}>'

class QuestionHeatmapData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    
    # Aggregated metrics
    total_participants = db.Column(db.Integer, default=0)
    average_time_spent = db.Column(db.Float, default=0.0)  # in seconds
    total_clicks = db.Column(db.Integer, default=0)
    total_hovers = db.Column(db.Integer, default=0)
    correct_answer_rate = db.Column(db.Float, default=0.0)  # percentage
    difficulty_score = db.Column(db.Float, default=0.0)  # calculated difficulty
    engagement_score = db.Column(db.Float, default=0.0)  # based on interactions
    
    # Hotspot data (JSON)
    click_hotspots = db.Column(db.Text)  # JSON array of click coordinates
    hover_hotspots = db.Column(db.Text)  # JSON array of hover coordinates
    scroll_patterns = db.Column(db.Text)  # JSON data about scroll behavior
    
    # Timestamps
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz = db.relationship('Quiz', backref='heatmap_data')
    question = db.relationship('Question', backref='heatmap_data')
    
    def __repr__(self):
        return f'<HeatmapData Quiz:{self.quiz_id} Question:{self.question_id}>'

class CollaborationInsight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    insight_type = db.Column(db.String(50), nullable=False)  # 'difficulty_pattern', 'engagement_drop', 'confusion_area', 'performance_trend'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='low')  # 'low', 'medium', 'high', 'critical'
    
    # Context data
    affected_questions = db.Column(db.Text)  # JSON array of question IDs
    metric_values = db.Column(db.Text)  # JSON object with relevant metrics
    suggested_actions = db.Column(db.Text)  # JSON array of recommendations
    
    # Status and timestamps
    is_active = db.Column(db.Boolean, default=True)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    acknowledged_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quiz = db.relationship('Quiz', backref='collaboration_insights')
    acknowledger = db.relationship('User', foreign_keys=[acknowledged_by])
    
    def __repr__(self):
        return f'<CollaborationInsight {self.insight_type} for Quiz {self.quiz_id}>'

# AI-Powered Plagiarism Detection Models
class PlagiarismAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempt.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    
    # Analysis Results
    overall_similarity_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    risk_level = db.Column(db.String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    
    # Algorithm-specific scores
    cosine_similarity = db.Column(db.Float)
    jaccard_similarity = db.Column(db.Float)
    levenshtein_similarity = db.Column(db.Float)
    semantic_similarity = db.Column(db.Float)
    
    # Analysis metadata
    analyzed_text = db.Column(db.Text, nullable=False)
    analysis_method = db.Column(db.String(50), default='multi_algorithm')
    confidence_score = db.Column(db.Float)  # How confident we are in the result
    
    # Detection flags
    is_flagged = db.Column(db.Boolean, default=False)
    requires_review = db.Column(db.Boolean, default=False)
    is_reviewed = db.Column(db.Boolean, default=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime)
    review_decision = db.Column(db.String(20))  # 'innocent', 'suspicious', 'plagiarized'
    review_notes = db.Column(db.Text)
    
    # Timestamps
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    quiz_attempt = db.relationship('QuizAttempt', backref='plagiarism_analyses')
    question = db.relationship('Question', backref='plagiarism_analyses')
    answer = db.relationship('Answer', backref='plagiarism_analysis', uselist=False)
    reviewer = db.relationship('User', foreign_keys=[reviewed_by])
    matches = db.relationship('PlagiarismMatch', backref='analysis', cascade='all, delete-orphan')
    
    def get_risk_color(self):
        colors = {
            'low': 'success',
            'medium': 'warning', 
            'high': 'danger',
            'critical': 'dark'
        }
        return colors.get(self.risk_level, 'secondary')
    
    def get_risk_percentage(self):
        return round(self.overall_similarity_score * 100, 1)
    
    def __repr__(self):
        return f'<PlagiarismAnalysis {self.id}: {self.risk_level} ({self.overall_similarity_score:.2f})>'

class PlagiarismMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('plagiarism_analysis.id'), nullable=False)
    
    # Match information
    matched_against_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    match_type = db.Column(db.String(30), nullable=False)  # 'exact', 'paraphrase', 'structural', 'semantic'
    
    # Text analysis
    matched_text_segment = db.Column(db.Text)  # The specific text that matched
    original_text_segment = db.Column(db.Text)  # The text it matched against
    
    # Position information
    start_position = db.Column(db.Integer)  # Character position in original text
    end_position = db.Column(db.Integer)
    
    # Match metadata
    algorithm_used = db.Column(db.String(50))  # Which algorithm detected this match
    confidence = db.Column(db.Float)  # Confidence in this specific match
    
    # Timestamps
    detected_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    matched_against = db.relationship('Answer', foreign_keys=[matched_against_id])
    
    def __repr__(self):
        return f'<PlagiarismMatch {self.match_type}: {self.similarity_score:.2f}>'

# RBAC (Role-Based Access Control) Models

class Role(db.Model):
    """Roles that can be assigned to users (admin, host, participant, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_system_role = db.Column(db.Boolean, default=False)  # System roles cannot be deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Relationships
    role_permissions = db.relationship('RolePermission', backref='role', lazy=True, cascade='all, delete-orphan')
    user_roles = db.relationship('UserRole', backref='role', lazy=True, cascade='all, delete-orphan')
    
    @property
    def permission_count(self):
        try:
            return len(list(self.role_permissions))
        except Exception:
            return 0
    
    @property
    def user_count(self):
        try:
            return len(list(self.user_roles))
        except Exception:
            return 0
    
    def get_permissions(self):
        """Get all permission names for this role"""
        try:
            return [rp.permission.name for rp in self.role_permissions if rp.permission]
        except Exception:
            return []
    
    def has_permission(self, permission_name):
        """Check if this role has a specific permission"""
        try:
            return any(rp.permission.name == permission_name for rp in self.role_permissions if rp.permission)
        except Exception:
            return False
    
    def add_permission(self, permission_name):
        """Add a permission to this role"""
        permission = Permission.query.filter_by(name=permission_name).first()
        if permission and not self.has_permission(permission_name):
            role_permission = RolePermission()
            role_permission.role_id = self.id
            role_permission.permission_id = permission.id
            db.session.add(role_permission)
            return True
        return False
    
    def remove_permission(self, permission_name):
        """Remove a permission from this role"""
        permission = Permission.query.filter_by(name=permission_name).first()
        if permission:
            role_permission = RolePermission.query.filter_by(
                role_id=self.id, 
                permission_id=permission.id
            ).first()
            if role_permission:
                db.session.delete(role_permission)
                return True
        return False
    
    def __repr__(self):
        return f'<Role {self.name}>'

class Permission(db.Model):
    """Individual permissions that can be granted to roles"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    display_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'quiz', 'user', 'system', 'reports'
    is_active = db.Column(db.Boolean, default=True)
    is_system_permission = db.Column(db.Boolean, default=False)  # System permissions cannot be deleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    role_permissions = db.relationship('RolePermission', backref='permission', lazy=True, cascade='all, delete-orphan')
    
    @property
    def role_count(self):
        try:
            return len(list(self.role_permissions))
        except Exception:
            return 0
    
    def get_roles(self):
        """Get all role names that have this permission"""
        try:
            return [rp.role.name for rp in self.role_permissions if rp.role]
        except Exception:
            return []
    
    def __repr__(self):
        return f'<Permission {self.name}>'

class RolePermission(db.Model):
    """Association table for roles and permissions (many-to-many)"""
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey('permission.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Ensure unique combinations
    __table_args__ = (db.UniqueConstraint('role_id', 'permission_id', name='unique_role_permission'),)
    
    def __repr__(self):
        return f'<RolePermission {self.role_id}->{self.permission_id}>'

class UserRole(db.Model):
    """Association table for users and roles (many-to-many)"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    assigned_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)  # Optional expiration date
    
    # Ensure unique combinations
    __table_args__ = (db.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),)
    
    # Relationships
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by])
    
    @property
    def is_expired(self):
        return self.expires_at and datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<UserRole {self.user_id}->{self.role_id}>'

class RoleAuditLog(db.Model):
    """Audit log for role and permission changes"""
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(50), nullable=False)  # 'create', 'update', 'delete', 'assign', 'revoke'
    entity_type = db.Column(db.String(20), nullable=False)  # 'role', 'permission', 'user_role'
    entity_id = db.Column(db.Integer, nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # User affected by the change
    performed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    old_values = db.Column(db.Text)  # JSON string of old values
    new_values = db.Column(db.Text)  # JSON string of new values
    reason = db.Column(db.Text)  # Optional reason for the change
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    target_user = db.relationship('User', foreign_keys=[target_user_id])
    performed_by_user = db.relationship('User', foreign_keys=[performed_by])
    
    def __repr__(self):
        return f'<RoleAuditLog {self.action} {self.entity_type}:{self.entity_id}>'
