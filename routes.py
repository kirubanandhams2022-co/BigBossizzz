from flask import render_template, request, redirect, url_for, flash, jsonify, session, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from app import app, db
from models import User, Quiz, Question, QuestionOption, QuizAttempt, Answer, ProctoringEvent, LoginEvent, UserViolation, UploadRecord, Course, HostCourseAssignment, ParticipantEnrollment, DeviceLog, SecurityAlert
from forms import RegistrationForm, LoginForm, QuizForm, QuestionForm, ProfileForm
from email_service import send_verification_email, send_credentials_email, send_login_notification, send_host_login_notification
from datetime import datetime, timedelta
import json
import logging
import os
import re
import csv
import pandas as pd
import PyPDF2
import docx
from io import BytesIO
from sqlalchemy import func, text
from utils import get_time_greeting, get_greeting_icon

# Excel/Spreadsheet generation imports
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

# PDF generation imports  
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/default-accounts')
def default_accounts():
    """Show default login accounts"""
    return render_template('default_accounts.html')

@app.route('/loading')
def loading():
    """Loading page with eye animation"""
    return render_template('loading.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered. Please use a different email.', 'error')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken. Please choose a different username.', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        if send_verification_email(user):
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return render_template('verify_email.html', user=user, resent=False)
        else:
            flash('Registration successful, but we could not send the verification email. You can request a new one from the login page.', 'warning')
            return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/verify/<token>')
def verify_email(token):
    """Verify email address"""
    user = User.query.filter_by(verification_token=token).first()
    
    if not user:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('login'))
    
    if user.verify_email(token):
        # Store the original password temporarily to send in email
        # In production, you might want to generate a temporary password instead
        temp_password = "Please change this password after login"
        
        db.session.commit()
        
        # Send credentials email
        if send_credentials_email(user, temp_password):
            flash('Email verified successfully! Your login credentials have been sent to your email.', 'success')
        else:
            flash('Email verified successfully! You can now log in with your credentials.', 'success')
    else:
        flash('Email verification failed. Please try again.', 'error')
    
    return redirect(url_for('login'))

@app.route('/resend-verification/<email>')
def resend_verification(email):
    """Resend email verification"""
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login'))
    
    if user.is_verified:
        flash('Your email is already verified. You can log in now.', 'info')
        return redirect(url_for('login'))
    
    # Generate new verification token
    user.generate_verification_token()
    db.session.commit()
    
    # Send verification email
    if send_verification_email(user):
        flash('Verification email sent successfully! Please check your inbox and spam folder.', 'success')
        return render_template('verify_email.html', user=user, resent=True)
    else:
        flash('Failed to send verification email. Please try again later.', 'error')
    
    return redirect(url_for('login'))

@app.route('/request-verification', methods=['GET', 'POST'])
def request_verification():
    """Request email verification page"""
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Please enter your email address.', 'error')
            return render_template('request_verification.html')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'error')
            return render_template('request_verification.html')
        
        if user.is_verified:
            flash('Your email is already verified. You can log in now.', 'info')
            return redirect(url_for('login'))
        
        # Generate new verification token
        user.generate_verification_token()
        db.session.commit()
        
        # Send verification email
        if send_verification_email(user):
            flash('Verification email sent successfully! Please check your inbox and spam folder.', 'success')
            return render_template('verify_email.html', user=user, resent=True)
        else:
            flash('Failed to send verification email. Please try again later.', 'error')
    
    return render_template('request_verification.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_verified:
                flash('Please verify your email address before logging in.', 'warning')
                # Add resend verification option
                resend_link = url_for('resend_verification', email=user.email)
                flash(f'Need a new verification email? <a href="{resend_link}">Click here to resend</a>', 'info')
                return render_template('login.html', form=form)
            
            # Update last login time
            user.last_login = datetime.utcnow()
            
            # Enhanced login tracking with comprehensive device/IP information
            ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'Unknown'))
            user_agent = request.headers.get('User-Agent', '')
            
            # Enhanced device fingerprinting and location tracking
            device_info = {
                'user_agent': user_agent,
                'ip_address': ip_address,
                'accept_language': request.headers.get('Accept-Language', ''),
                'accept_encoding': request.headers.get('Accept-Encoding', ''),
                'remote_addr': request.environ.get('REMOTE_ADDR'),
                'x_forwarded_for': request.headers.get('X-Forwarded-For', ''),
                'x_real_ip': request.headers.get('X-Real-IP', ''),
                'host': request.headers.get('Host', ''),
                'referer': request.headers.get('Referer', ''),
                'connection': request.headers.get('Connection', '')
            }
            
            # Check for suspicious login patterns
            from datetime import timedelta
            recent_logins = LoginEvent.query.filter_by(user_id=user.id).filter(
                LoginEvent.login_time > datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            # Check for different IP addresses in short time (potential location jumping)
            different_ips = db.session.query(LoginEvent.ip_address).distinct().filter(
                LoginEvent.user_id == user.id,
                LoginEvent.login_time > datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # Check for different user agents (device switching)
            different_devices = db.session.query(LoginEvent.user_agent).distinct().filter(
                LoginEvent.user_id == user.id,
                LoginEvent.login_time > datetime.utcnow() - timedelta(days=7)
            ).count()
            
            is_suspicious = recent_logins > 5 or different_ips > 3 or different_devices > 5
            
            # Create login event record
            login_event = LoginEvent(
                user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                device_info=json.dumps(device_info),
                is_suspicious=is_suspicious
            )
            
            db.session.add(login_event)
            db.session.commit()
            
            # Send email notifications
            try:
                # Send notification to user
                send_login_notification(user, login_event)
                
                # If participant, notify all hosts
                if user.role == 'participant':
                    hosts = User.query.filter_by(role='host').all()
                    for host in hosts:
                        send_host_login_notification(host, user, login_event)
                        
            except Exception as e:
                logging.error(f"Failed to send login notifications: {e}")
            
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - redirects based on user role"""
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_host():
        return redirect(url_for('host_dashboard'))
    else:
        return redirect(url_for('participant_dashboard'))

@app.route('/host/dashboard')
@login_required
def host_dashboard():
    """Enhanced Host dashboard with participant management"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    quizzes = Quiz.query.filter_by(creator_id=current_user.id).order_by(Quiz.created_at.desc()).all()
    
    # Get recent quiz attempts for host's quizzes
    recent_attempts = []
    for quiz in quizzes:
        attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).order_by(QuizAttempt.started_at.desc()).limit(5).all()
        recent_attempts.extend(attempts)
    
    recent_attempts.sort(key=lambda x: x.started_at, reverse=True)
    recent_attempts = recent_attempts[:10]  # Show only 10 most recent
    
    # Get participant statistics
    participants = User.query.filter_by(role='participant').all()
    recent_logins = LoginEvent.query.join(User).filter(User.role == 'participant').order_by(LoginEvent.login_time.desc()).limit(10).all()
    
    # Get violation statistics
    quiz_ids = [quiz.id for quiz in quizzes]
    if quiz_ids:
        high_violations = db.session.query(QuizAttempt, func.count(ProctoringEvent.id).label('violation_count')).join(ProctoringEvent).filter(
            QuizAttempt.quiz_id.in_(quiz_ids),
            ProctoringEvent.severity == 'high'
        ).group_by(QuizAttempt.id).having(func.count(ProctoringEvent.id) > 2).all()
    else:
        high_violations = []
    
    return render_template('host_dashboard.html', 
                         quizzes=quizzes, 
                         recent_attempts=recent_attempts,
                         participants=participants,
                         recent_logins=recent_logins,
                         high_violations=high_violations)

@app.route('/host/monitoring')
@login_required  
def host_monitoring():
    """Real-time participant monitoring panel"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get active quiz attempts
    active_attempts = QuizAttempt.query.filter_by(status='in_progress').join(Quiz).filter(
        Quiz.creator_id == current_user.id if not current_user.is_admin() else True
    ).all()
    
    # Get recent login events
    recent_logins = LoginEvent.query.order_by(LoginEvent.login_time.desc()).limit(20).all()
    
    # Get recent proctoring events
    recent_violations = ProctoringEvent.query.join(QuizAttempt).join(Quiz).filter(
        Quiz.creator_id == current_user.id if not current_user.is_admin() else True
    ).order_by(ProctoringEvent.timestamp.desc()).limit(50).all()
    
    # Get participant device info
    participants_online = []
    for attempt in active_attempts:
        # Get latest login for this participant
        latest_login = LoginEvent.query.filter_by(user_id=attempt.participant_id).order_by(
            LoginEvent.login_time.desc()
        ).first()
        
        # Get violation count for this attempt
        violation_count = ProctoringEvent.query.filter_by(attempt_id=attempt.id).count()
        
        participants_online.append({
            'attempt': attempt,
            'latest_login': latest_login,
            'violation_count': violation_count,
            'time_elapsed': datetime.utcnow() - attempt.started_at,
            'quiz_title': attempt.quiz.title
        })
    
    return render_template('host_monitoring.html',
                         active_attempts=active_attempts,
                         participants_online=participants_online,
                         recent_logins=recent_logins,
                         recent_violations=recent_violations)

@app.route('/api/monitoring/live-data')
@login_required
def get_live_monitoring_data():
    """API endpoint for real-time monitoring data"""
    if not current_user.is_host() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    # Get active attempts
    active_attempts = QuizAttempt.query.filter_by(status='in_progress').join(Quiz).filter(
        Quiz.creator_id == current_user.id if not current_user.is_admin() else True
    ).all()
    
    participants_data = []
    for attempt in active_attempts:
        # Get latest violations
        recent_violations = ProctoringEvent.query.filter_by(attempt_id=attempt.id).order_by(
            ProctoringEvent.timestamp.desc()
        ).limit(5).all()
        
        # Calculate time remaining
        time_elapsed = datetime.utcnow() - attempt.started_at
        time_remaining = timedelta(minutes=attempt.quiz.time_limit) - time_elapsed
        
        participants_data.append({
            'attempt_id': attempt.id,
            'participant_name': attempt.participant.username,
            'quiz_title': attempt.quiz.title,
            'time_elapsed': str(time_elapsed).split('.')[0],
            'time_remaining': str(time_remaining).split('.')[0] if time_remaining.total_seconds() > 0 else 'Overtime',
            'violation_count': len(recent_violations),
            'latest_violation': recent_violations[0].event_type if recent_violations else None,
            'questions_answered': len(attempt.answers),
            'total_questions': len(attempt.quiz.questions),
            'progress_percentage': round((len(attempt.answers) / len(attempt.quiz.questions)) * 100) if attempt.quiz.questions else 0
        })
    
    return jsonify({
        'participants': participants_data,
        'total_active': len(participants_data),
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/participant/dashboard')
@login_required
def participant_dashboard():
    """Participant dashboard"""
    # Get available quizzes (you might want to implement invitation system)
    available_quizzes = Quiz.query.filter_by(is_active=True).all()
    
    # Get participant's quiz attempts
    my_attempts = QuizAttempt.query.filter_by(participant_id=current_user.id).order_by(QuizAttempt.started_at.desc()).all()
    
    return render_template('participant_dashboard.html', available_quizzes=available_quizzes, my_attempts=my_attempts)

@app.route('/quiz_listing')
@login_required
def quiz_listing():
    """Quiz listing page with mobile interface"""
    if current_user.role != 'participant':
        flash('Access denied. Participants only.', 'error')
        return redirect(url_for('index'))
    
    # Get available quizzes for this participant
    available_quizzes = Quiz.query.filter_by(is_active=True).all()
    
    # Get participant's quiz attempts
    my_attempts = QuizAttempt.query.filter_by(participant_id=current_user.id).order_by(QuizAttempt.started_at.desc()).all()
    
    return render_template('quiz_listing.html', 
                         available_quizzes=available_quizzes,
                         my_attempts=my_attempts)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get system statistics
    total_users = User.query.count()
    total_hosts = User.query.filter_by(role='host').count()
    total_participants = User.query.filter_by(role='participant').count()
    total_quizzes = Quiz.query.count()
    total_attempts = QuizAttempt.query.count()
    
    # Recent registrations
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    stats = {
        'total_users': total_users,
        'total_hosts': total_hosts,
        'total_participants': total_participants,
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts
    }
    
    return render_template('admin_dashboard.html', stats=stats, recent_users=recent_users)

@app.route('/admin/export-database')
@login_required
def admin_export_database():
    """Export complete database to Excel with comprehensive error handling"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        from io import BytesIO
        
        wb = Workbook()
        
        # Users Sheet
        ws_users = wb.active
        ws_users.title = "Users"
        users_headers = ['ID', 'Username', 'Email', 'Role', 'Is Verified', 'Created At']
        
        for col, header in enumerate(users_headers, 1):
            cell = ws_users.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        
        # Fetch users with error handling
        try:
            users = User.query.all()
        except Exception as e:
            logging.error(f"Database error fetching users: {e}")
            flash('Error accessing user data for export.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        for row, user in enumerate(users, 2):
            try:
                ws_users.cell(row=row, column=1, value=user.id)
                ws_users.cell(row=row, column=2, value=user.username or 'N/A')
                ws_users.cell(row=row, column=3, value=user.email or 'N/A')
                ws_users.cell(row=row, column=4, value=user.role or 'N/A')
                ws_users.cell(row=row, column=5, value='Yes' if user.is_verified else 'No')
                ws_users.cell(row=row, column=6, value=user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A')
            except Exception as e:
                logging.warning(f"Error exporting user {user.id}: {e}")
                continue
        
        # Save to BytesIO with error handling
        try:
            buffer = BytesIO()
            wb.save(buffer)
            buffer.seek(0)
        except Exception as e:
            logging.error(f"Error creating Excel file: {e}")
            flash('Error generating export file.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        return send_file(
            BytesIO(buffer.read()),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'database_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        
    except Exception as e:
        logging.error(f"Unexpected error in database export: {e}")
        flash('Database export failed due to an unexpected error.', 'error')
        return redirect(url_for('admin_dashboard'))

# File Upload and Auto-Question Generation System

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'csv', 'xlsx', 'txt'}
UPLOAD_FOLDER = 'uploads'

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload-quiz-file', methods=['POST'])
@login_required
def upload_quiz_file():
    """Upload file and extract candidate questions with enhanced security"""
    if not current_user.is_host() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not supported. Use PDF, DOCX, CSV, XLSX, or TXT files.'}), 400
    
    # Check file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file.seek(0, 2)  # Seek to end to get size
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 400
    
    if file_size == 0:
        return jsonify({'error': 'File is empty.'}), 400
    
    try:
        # Secure filename and save
        filename = secure_filename(file.filename or 'upload')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Create upload record with proper validation
        try:
            upload_record = UploadRecord(
                host_id=current_user.id,
                filename=filename,
                mime_type=file.content_type or 'application/octet-stream',
                stored_path=file_path,
                file_size=file_size,
                parsed=False
            )
            db.session.add(upload_record)
            db.session.commit()
        except Exception as e:
            logging.error(f"Database error creating upload record: {e}")
            return jsonify({'error': 'Failed to save upload record'}), 500
        
        # Parse file and extract candidate questions
        candidate_questions = parse_file_for_questions(file_path, file.content_type)
        
        # Store candidate questions as JSON
        upload_record.candidate_questions_json = json.dumps(candidate_questions)
        upload_record.parsed = True
        db.session.commit()
        
        return jsonify({
            'upload_record_id': upload_record.id,
            'candidate_count': len(candidate_questions),
            'filename': filename,
            'message': f'Successfully extracted {len(candidate_questions)} candidate questions'
        })
        
    except Exception as e:
        logging.error(f"File upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/upload-quiz-create-draft', methods=['POST'])
@login_required
def upload_quiz_create_draft():
    """Create draft quiz from uploaded file"""
    if not current_user.is_host() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    upload_record_id = data.get('upload_record_id')
    num_questions = data.get('N', 10)
    quiz_title = data.get('title', 'Auto-Generated Quiz')
    quiz_description = data.get('description', 'Quiz generated from uploaded file')
    
    upload_record = UploadRecord.query.get_or_404(upload_record_id)
    
    if upload_record.host_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Load candidate questions
        candidate_questions = json.loads(upload_record.candidate_questions_json)
        
        # Select top N questions
        selected_questions = select_top_questions(candidate_questions, num_questions)
        
        # Create draft quiz
        quiz = Quiz(
            title=quiz_title,
            description=quiz_description,
            creator_id=current_user.id,
            auto_generate_from_upload=True,
            draft_from_upload_id=upload_record.id,
            is_active=False  # Draft mode
        )
        db.session.add(quiz)
        db.session.flush()  # Get quiz ID
        
        # Create questions and options
        for i, q_data in enumerate(selected_questions):
            question = Question(
                quiz_id=quiz.id,
                question_text=q_data['question'],
                question_type=q_data.get('type', 'multiple_choice'),
                points=q_data.get('points', 1),
                order=i + 1
            )
            db.session.add(question)
            db.session.flush()  # Get question ID
            
            # Add options for multiple choice questions
            if question.question_type in ['multiple_choice', 'true_false']:
                for j, option_text in enumerate(q_data.get('options', [])):
                    option = QuestionOption(
                        question_id=question.id,
                        option_text=option_text,
                        is_correct=j == q_data.get('correct_option_index', 0),
                        order=j + 1
                    )
                    db.session.add(option)
        
        upload_record.parsed_to_quiz_id = quiz.id
        db.session.commit()
        
        return jsonify({
            'draft_quiz_id': quiz.id,
            'message': f'Created draft quiz with {len(selected_questions)} questions'
        })
        
    except Exception as e:
        logging.error(f"Draft creation error: {e}")
        db.session.rollback()
        return jsonify({'error': f'Failed to create draft: {str(e)}'}), 500

def parse_file_for_questions(file_path, mime_type):
    """Parse uploaded file to extract candidate questions"""
    candidate_questions = []
    
    try:
        if 'pdf' in mime_type:
            candidate_questions = parse_pdf_questions(file_path)
        elif 'docx' in mime_type or 'document' in mime_type:
            candidate_questions = parse_docx_questions(file_path)
        elif 'csv' in mime_type:
            candidate_questions = parse_csv_questions(file_path)
        elif 'spreadsheet' in mime_type or 'excel' in mime_type:
            candidate_questions = parse_excel_questions(file_path)
        elif 'text' in mime_type:
            candidate_questions = parse_text_questions(file_path)
        
    except Exception as e:
        logging.error(f"File parsing error: {e}")
        
    return candidate_questions

def parse_pdf_questions(file_path):
    """Extract questions from PDF file with enhanced error handling"""
    questions = []
    
    try:
        # Validate file exists and is readable
        if not os.path.exists(file_path):
            logging.error(f"PDF file not found: {file_path}")
            return questions
            
        if os.path.getsize(file_path) == 0:
            logging.error(f"PDF file is empty: {file_path}")
            return questions
        
        with open(file_path, 'rb') as file:
            try:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if len(pdf_reader.pages) == 0:
                    logging.warning(f"PDF has no pages: {file_path}")
                    return questions
                
                text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        logging.warning(f"Error extracting text from page {page_num}: {e}")
                        continue
                        
                if len(text.strip()) < 10:
                    logging.warning(f"PDF contains very little text: {file_path}")
                    return questions
                
                # Parse text for questions with error handling
                questions = extract_questions_from_text(text)
                
            except PyPDF2.errors.PdfReadError as e:
                logging.error(f"PDF read error: {e}")
            except Exception as e:
                logging.error(f"Unexpected PDF parsing error: {e}")
        
    except Exception as e:
        logging.error(f"File access error for PDF {file_path}: {e}")
    
    return questions

def parse_docx_questions(file_path):
    """Extract questions from DOCX file with enhanced error handling"""
    questions = []
    
    try:
        # Validate file exists and is readable
        if not os.path.exists(file_path):
            logging.error(f"DOCX file not found: {file_path}")
            return questions
            
        if os.path.getsize(file_path) == 0:
            logging.error(f"DOCX file is empty: {file_path}")
            return questions
        
        try:
            doc = docx.Document(file_path)
            text = ""
            
            if len(doc.paragraphs) == 0:
                logging.warning(f"DOCX has no paragraphs: {file_path}")
                return questions
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"
            
            # Also extract text from tables if present
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text += cell.text + "\n"
                            
            if len(text.strip()) < 10:
                logging.warning(f"DOCX contains very little text: {file_path}")
                return questions
            
            # Parse text for questions with error handling
            questions = extract_questions_from_text(text)
            
        except docx.opc.exceptions.PackageNotFoundError as e:
            logging.error(f"Invalid DOCX format: {e}")
        except Exception as e:
            logging.error(f"Unexpected DOCX parsing error: {e}")
        
    except Exception as e:
        logging.error(f"File access error for DOCX {file_path}: {e}")
    
    return questions

def parse_csv_questions(file_path):
    """Extract questions from CSV file with robust error handling"""
    questions = []
    
    try:
        # Try different encodings and delimiters
        for encoding in ['utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            # If all encodings fail, return empty
            logging.error(f"Could not decode CSV file: {file_path}")
            return questions
        
        if df.empty:
            return questions
            
        # Expected columns: question, option_a, option_b, option_c, option_d, correct_answer
        for idx, row in df.iterrows():
            if 'question' in df.columns and pd.notna(row.get('question')):
                question_data = {
                    'question': str(row.get('question', '')),
                    'type': 'multiple_choice',
                    'options': [],
                    'correct_option_index': 0,
                    'confidence': 0.9  # High confidence for structured data
                }
                
                # Extract options
                option_cols = [col for col in df.columns if col.startswith('option')]
                for col in option_cols:
                    if pd.notna(row[col]):
                        question_data['options'].append(str(row[col]))
                
                # Determine correct answer
                if 'correct_answer' in df.columns:
                    correct_text = str(row['correct_answer']).strip()
                    for i, option in enumerate(question_data['options']):
                        if option.strip().lower() == correct_text.lower():
                            question_data['correct_option_index'] = i
                            break
                
                if question_data['question'] and len(question_data['options']) >= 2:
                    questions.append(question_data)
        
    except Exception as e:
        logging.error(f"CSV parsing error: {e}")
    
    return questions

def parse_excel_questions(file_path):
    """Extract questions from Excel file"""
    questions = []
    
    try:
        df = pd.read_excel(file_path)
        
        # Similar to CSV parsing
        for _, row in df.iterrows():
            if 'question' in df.columns:
                question_data = {
                    'question': str(row.get('question', '')),
                    'type': 'multiple_choice',
                    'options': [],
                    'correct_option_index': 0,
                    'confidence': 0.9
                }
                
                # Extract options
                option_cols = [col for col in df.columns if 'option' in col.lower()]
                for col in option_cols:
                    if pd.notna(row[col]):
                        question_data['options'].append(str(row[col]))
                
                # Determine correct answer
                if 'correct_answer' in df.columns:
                    correct_text = str(row['correct_answer']).strip()
                    for i, option in enumerate(question_data['options']):
                        if option.strip().lower() == correct_text.lower():
                            question_data['correct_option_index'] = i
                            break
                
                if question_data['question'] and len(question_data['options']) >= 2:
                    questions.append(question_data)
        
    except Exception as e:
        logging.error(f"Excel parsing error: {e}")
    
    return questions

def parse_text_questions(file_path):
    """Extract questions from plain text file"""
    questions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        questions = extract_questions_from_text(text)
        
    except Exception as e:
        logging.error(f"Text parsing error: {e}")
    
    return questions

def extract_questions_from_text(text):
    """Extract questions from text using improved regex patterns"""
    questions = []
    
    if not text or len(text.strip()) < 20:
        return questions
    
    try:
        # Clean and normalize text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Enhanced patterns for different question formats
        patterns = [
            # Pattern 1: Numbered questions with options (1. Question? A) option B) option)
            r'(\d+\.?\s*)(.*?\?)\s*((?:[A-Da-d][\)\.].*?)(?=[A-Da-d][\)\.]|$))',
            # Pattern 2: Questions with options on new lines
            r'(Question\s*\d*:?\s*)(.*?\?)\s*((?:[A-Da-d][\)\.].*?)(?=Question|\d+\.|$))',
            # Pattern 3: Simple question-answer pairs
            r'([^.!]*\?)\s*((?:[A-Da-d][\)\.].*?)(?=[^.!]*\?|$))'
        ]
        
        # Try each pattern to extract questions
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                try:
                    if len(match.groups()) >= 2:
                        question_text = match.group(-2).strip()  # Second to last group
                        options_text = match.group(-1).strip()   # Last group
                        
                        if len(question_text) > 10:  # Meaningful question
                            question_data = {
                                'question': question_text,
                                'type': 'multiple_choice',
                                'options': [],
                                'correct_option_index': 0,
                                'confidence': 0.7
                            }
                            
                            # Extract individual options
                            option_parts = re.findall(r'[A-Da-d][\)\.]([^A-Da-d\)\.]*)(?=[A-Da-d][\)\.]|$)', options_text)
                            question_data['options'] = [opt.strip() for opt in option_parts if opt.strip()]
                            
                            if len(question_data['options']) >= 2:
                                questions.append(question_data)
                                
                except Exception as e:
                    continue  # Skip malformed questions
                    
        return questions[:20]  # Limit to 20 questions max
        
    except Exception as e:
        logging.error(f"Text extraction error: {e}")
        return []
    
    for match in matches:
        question_text = match.group(2).strip()
        options_text = match.group(3).strip()
        
        if question_text:
            # Extract options
            option_pattern = r'([A-D]\)|[A-D]\.|\([A-D]\)|[1-4]\.|[1-4]\))\s*(.*?)(?=\n[A-D]\)|\n[A-D]\.|\n\([A-D]\)|\n[1-4]\.|\n[1-4]\)|$)'
            option_matches = re.finditer(option_pattern, options_text, re.MULTILINE | re.DOTALL)
            
            options = []
            for opt_match in option_matches:
                option_text = opt_match.group(2).strip()
                if option_text:
                    options.append(option_text)
            
            if len(options) >= 2:
                # Look for answer indicators
                answer_pattern = r'(?:Answer|Ans|Correct)[:\s]*([A-D]|[1-4])'
                answer_match = re.search(answer_pattern, text[match.end():match.end()+200], re.IGNORECASE)
                
                correct_index = 0
                if answer_match:
                    answer_letter = answer_match.group(1).upper()
                    if answer_letter in 'ABCD':
                        correct_index = ord(answer_letter) - ord('A')
                    elif answer_letter in '1234':
                        correct_index = int(answer_letter) - 1
                
                question_data = {
                    'question': question_text,
                    'type': 'multiple_choice',
                    'options': options,
                    'correct_option_index': min(correct_index, len(options) - 1),
                    'confidence': 0.7 if answer_match else 0.5
                }
                
                questions.append(question_data)
    
    return questions

def select_top_questions(candidate_questions, num_questions):
    """Select top N questions based on confidence and completeness"""
    
    # Sort by confidence (highest first) and completeness
    def question_score(q):
        confidence = q.get('confidence', 0.5)
        option_count = len(q.get('options', []))
        has_answer = q.get('correct_option_index', -1) >= 0
        
        return confidence + (option_count / 10) + (0.2 if has_answer else 0)
    
    sorted_questions = sorted(candidate_questions, key=question_score, reverse=True)
    
    return sorted_questions[:num_questions]

# Enhanced Security Measures and Advanced Features

@app.route('/api/quiz/<int:quiz_id>/publish', methods=['POST'])
@login_required
def publish_quiz(quiz_id):
    """Publish a draft quiz after host review"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    lock_answers = data.get('lock_answers', True)
    
    # Activate the quiz
    quiz.is_active = True
    
    # Lock answers if requested
    if lock_answers:
        for question in quiz.questions:
            for option in question.options:
                # Mark host-reviewed answers as final
                pass  # Options are already set correctly
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Quiz published successfully'})

@app.route('/api/quiz/<int:quiz_id>/delete', methods=['DELETE'])
@login_required
def delete_quiz(quiz_id):
    """Delete quiz (soft delete by default)"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    hard_delete = request.args.get('hard', 'false').lower() == 'true'
    
    if hard_delete and current_user.is_admin():
        # Hard delete - remove completely
        # First remove related upload files
        if quiz.draft_from_upload_id:
            upload_record = UploadRecord.query.get(quiz.draft_from_upload_id)
            if upload_record and upload_record.stored_path:
                try:
                    os.remove(upload_record.stored_path)
                except:
                    pass
                db.session.delete(upload_record)
        
        db.session.delete(quiz)
        message = 'Quiz permanently deleted'
    else:
        # Soft delete
        quiz.is_deleted = True
        message = 'Quiz moved to trash'
    
    db.session.commit()
    
    return jsonify({'success': True, 'message': message})

@app.route('/api/quiz/<int:quiz_id>/restore', methods=['POST'])
@login_required
def restore_quiz(quiz_id):
    """Restore a soft-deleted quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    quiz.is_deleted = False
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Quiz restored successfully'})

@app.route('/host/participants-advanced')
@login_required
def host_participants_advanced():
    """Enhanced participant management and login activity"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get participants who have taken host's quizzes
    participants = db.session.query(User).join(QuizAttempt).join(Quiz).filter(
        Quiz.creator_id == current_user.id if not current_user.is_admin() else True,
        User.role == 'participant'
    ).distinct().all()
    
    # Get detailed info for each participant
    participant_data = []
    for participant in participants:
        # Get latest device log
        latest_device_log = DeviceLog.query.filter_by(user_id=participant.id).order_by(
            DeviceLog.logged_in_at.desc()
        ).first()
        
        # Get quiz attempts
        attempts = QuizAttempt.query.join(Quiz).filter(
            QuizAttempt.participant_id == participant.id,
            Quiz.creator_id == current_user.id if not current_user.is_admin() else True
        ).all()
        
        # Get violation count
        violation_count = 0
        for attempt in attempts:
            violation_count += ProctoringEvent.query.filter_by(attempt_id=attempt.id).count()
        
        participant_data.append({
            'user': participant,
            'latest_device': latest_device_log,
            'attempts': attempts,
            'violation_count': violation_count,
            'status': 'online' if latest_device_log and 
                     (datetime.utcnow() - latest_device_log.logged_in_at).seconds < 300 else 'offline'
        })
    
    return render_template('host_participants.html', participant_data=participant_data)

@app.route('/api/participant/<int:participant_id>/security-report')
@login_required
def participant_security_report(participant_id):
    """Generate detailed security report for a participant"""
    if not current_user.is_host() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    participant = User.query.get_or_404(participant_id)
    
    # Get all attempts by this participant for current host's quizzes
    attempts = QuizAttempt.query.join(Quiz).filter(
        QuizAttempt.participant_id == participant_id,
        Quiz.creator_id == current_user.id if not current_user.is_admin() else True
    ).all()
    
    # Compile security data
    security_data = {
        'participant': {
            'username': participant.username,
            'email': participant.email,
            'total_attempts': len(attempts)
        },
        'violations': [],
        'device_logs': [],
        'flagged_attempts': [],
        'suspicious_patterns': []
    }
    
    # Get violations
    for attempt in attempts:
        violations = ProctoringEvent.query.filter_by(attempt_id=attempt.id).all()
        for violation in violations:
            security_data['violations'].append({
                'quiz_title': attempt.quiz.title,
                'event_type': violation.event_type,
                'severity': violation.severity,
                'timestamp': violation.timestamp.isoformat(),
                'details': violation.details
            })
    
    # Get device logs
    device_logs = DeviceLog.query.filter_by(user_id=participant_id).order_by(
        DeviceLog.logged_in_at.desc()
    ).limit(20).all()
    
    for log in device_logs:
        security_data['device_logs'].append({
            'ip_address': log.ip_address,
            'device_type': log.device_type,
            'browser_info': log.browser_info,
            'timestamp': log.logged_in_at.isoformat(),
            'is_suspicious': log.is_suspicious
        })
    
    # Detect suspicious patterns
    ip_addresses = set(log.ip_address for log in device_logs)
    if len(ip_addresses) > 3:
        security_data['suspicious_patterns'].append('Multiple IP addresses detected')
    
    user_agents = set(log.user_agent for log in device_logs if log.user_agent)
    if len(user_agents) > 2:
        security_data['suspicious_patterns'].append('Multiple devices/browsers detected')
    
    # Flagged attempts
    flagged_attempts = [a for a in attempts if a.violation_count > 2]
    for attempt in flagged_attempts:
        security_data['flagged_attempts'].append({
            'quiz_title': attempt.quiz.title,
            'started_at': attempt.started_at.isoformat(),
            'violation_count': attempt.violation_count,
            'status': attempt.status
        })
    
    return jsonify(security_data)

@app.route('/api/monitoring/send-warning/<int:attempt_id>', methods=['POST'])
@login_required
def send_warning_to_participant(attempt_id):
    """Send real-time warning to participant"""
    if not current_user.is_host() and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.quiz.creator_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    warning_message = data.get('message', 'Please follow the quiz guidelines and avoid suspicious activities.')
    
    # Create security alert
    alert = SecurityAlert(
        user_id=attempt.participant_id,
        quiz_id=attempt.quiz_id,
        attempt_id=attempt_id,
        alert_type='host_warning',
        severity='medium',
        description=warning_message,
        auto_action_taken='warning_sent'
    )
    db.session.add(alert)
    db.session.commit()
    
    # In a real WebSocket implementation, this would send the message via WebSocket
    # For now, we'll store it as a security alert that can be displayed to the participant
    
    return jsonify({'success': True, 'message': 'Warning sent successfully'})

@app.route('/api/monitoring/auto-terminate/<int:attempt_id>', methods=['POST'])
@login_required
def auto_terminate_quiz(attempt_id):
    """Automatically terminate quiz due to violations"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Check if auto-termination is enabled for this quiz
    if not attempt.quiz.auto_terminate_on_violation:
        return jsonify({'error': 'Auto-termination not enabled for this quiz'}), 400
    
    data = request.json
    reason = data.get('reason', 'Multiple proctoring violations detected')
    
    # Terminate the quiz
    attempt.status = 'terminated'
    attempt.completed_at = datetime.utcnow()
    attempt.termination_reason = reason
    attempt.is_flagged = True
    
    # Create security alert
    alert = SecurityAlert(
        user_id=attempt.participant_id,
        quiz_id=attempt.quiz_id,
        attempt_id=attempt_id,
        alert_type='auto_termination',
        severity='high',
        description=f'Quiz automatically terminated: {reason}',
        auto_action_taken='quiz_terminated'
    )
    db.session.add(alert)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Quiz terminated due to violations'})

@app.route('/api/device-log', methods=['POST'])
@login_required
def log_device_info():
    """Log participant device information for security tracking"""
    data = request.json
    
    # Detect suspicious behavior
    is_suspicious = False
    
    # Check for suspicious user agents
    suspicious_keywords = ['headless', 'phantom', 'selenium', 'webdriver', 'automation']
    user_agent = data.get('userAgent', '').lower()
    if any(keyword in user_agent for keyword in suspicious_keywords):
        is_suspicious = True
    
    # Check for unusual screen resolutions
    screen_resolution = data.get('screenResolution', '')
    if screen_resolution:
        try:
            width, height = map(int, screen_resolution.split('x'))
            if width < 800 or height < 600:  # Unusually small screens
                is_suspicious = True
        except:
            pass
    
    # Get IP address
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    device_log = DeviceLog(
        user_id=current_user.id,
        quiz_id=data.get('quizId'),
        ip_address=ip_address,
        user_agent=data.get('userAgent'),
        device_type=data.get('deviceType'),
        browser_info=data.get('browserInfo'),
        screen_resolution=screen_resolution,
        timezone=data.get('timezone'),
        is_suspicious=is_suspicious
    )
    
    db.session.add(device_log)
    db.session.commit()
    
    return jsonify({'success': True, 'logged': True, 'suspicious': is_suspicious})

# Database Export for Admin
@app.route('/admin/export-database-sqlite')
@login_required
def export_database_sqlite():
    """Export database as SQLite file for admin"""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        import sqlite3
        import tempfile
        
        # Create temporary SQLite database
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_quizzes_{timestamp}.db')
        sqlite_path = temp_file.name
        temp_file.close()
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Export users
        users = User.query.all()
        sqlite_cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                email TEXT,
                role TEXT,
                is_verified BOOLEAN,
                created_at TEXT
            )
        ''')
        
        for user in users:
            sqlite_cursor.execute('''
                INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)
            ''', (user.id, user.username, user.email, user.role, user.is_verified, 
                  user.created_at.isoformat() if user.created_at else None))
        
        # Export quizzes
        quizzes = Quiz.query.filter_by(is_deleted=False).all()
        sqlite_cursor.execute('''
            CREATE TABLE quizzes (
                id INTEGER PRIMARY KEY,
                title TEXT,
                creator_username TEXT,
                time_limit INTEGER,
                proctoring_enabled BOOLEAN,
                created_at TEXT
            )
        ''')
        
        for quiz in quizzes:
            sqlite_cursor.execute('''
                INSERT INTO quizzes VALUES (?, ?, ?, ?, ?, ?)
            ''', (quiz.id, quiz.title, quiz.creator.username, quiz.time_limit, 
                  quiz.proctoring_enabled, quiz.created_at.isoformat()))
        
        # Export quiz attempts
        attempts = QuizAttempt.query.all()
        sqlite_cursor.execute('''
            CREATE TABLE quiz_attempts (
                id INTEGER PRIMARY KEY,
                participant_username TEXT,
                quiz_title TEXT,
                score REAL,
                status TEXT,
                started_at TEXT,
                completed_at TEXT,
                violation_count INTEGER
            )
        ''')
        
        for attempt in attempts:
            sqlite_cursor.execute('''
                INSERT INTO quiz_attempts VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (attempt.id, attempt.participant.username, attempt.quiz.title,
                  attempt.score, attempt.status, attempt.started_at.isoformat(),
                  attempt.completed_at.isoformat() if attempt.completed_at else None,
                  attempt.violation_count))
        
        sqlite_conn.commit()
        sqlite_conn.close()
        
        # Return file for download
        return send_file(
            sqlite_path,
            mimetype='application/x-sqlite3',
            as_attachment=True,
            download_name=f'quizzes_{timestamp}.db'
        )
        
    except Exception as e:
        logging.error(f"Database export error: {e}")
        flash('Database export failed.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/users')
@login_required
def admin_users():
    """Manage all users"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/user/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_user_status(user_id):
    """Toggle user active/inactive status"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow disabling yourself
    if user.id == current_user.id:
        flash('You cannot disable your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/change-role', methods=['POST'])
@login_required
def admin_change_user_role(user_id):
    """Change user role"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    
    if new_role not in ['admin', 'host', 'participant']:
        flash('Invalid role specified.', 'error')
        return redirect(url_for('admin_users'))
    
    # Don't allow changing your own role
    if user.id == current_user.id:
        flash('You cannot change your own role.', 'error')
        return redirect(url_for('admin_users'))
    
    old_role = user.role
    user.role = new_role
    db.session.commit()
    
    flash(f'User {user.username} role changed from {old_role} to {new_role}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete a user (admin only)"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        # Delete related data in proper order
        # 1. Delete answers and proctoring events for this user's attempts
        user_attempts = QuizAttempt.query.filter_by(participant_id=user.id).all()
        for attempt in user_attempts:
            Answer.query.filter_by(attempt_id=attempt.id).delete()
            ProctoringEvent.query.filter_by(attempt_id=attempt.id).delete()
        
        # 2. Delete quiz attempts
        QuizAttempt.query.filter_by(participant_id=user.id).delete()
        
        # 3. Handle quizzes created by this user
        user_quizzes = Quiz.query.filter_by(creator_id=user.id).all()
        for quiz in user_quizzes:
            # Delete all attempts for these quizzes first
            quiz_attempts = QuizAttempt.query.filter_by(quiz_id=quiz.id).all()
            for attempt in quiz_attempts:
                Answer.query.filter_by(attempt_id=attempt.id).delete()
                ProctoringEvent.query.filter_by(attempt_id=attempt.id).delete()
            QuizAttempt.query.filter_by(quiz_id=quiz.id).delete()
            
            # Delete questions and options
            for question in quiz.questions:
                QuestionOption.query.filter_by(question_id=question.id).delete()
            Question.query.filter_by(quiz_id=quiz.id).delete()
            
            # Delete the quiz
            db.session.delete(quiz)
        
        # 4. Finally delete the user
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User {username} has been permanently deleted.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/user/<int:user_id>/reset-password', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    """Reset user password"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return redirect(url_for('admin_users'))
    
    user.set_password(new_password)
    db.session.commit()
    
    flash(f'Password reset for user {user.username}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/create-user', methods=['POST'])
@login_required
def admin_create_user():
    """Create new user account"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    
    # Validation
    if not all([username, email, password, role]):
        flash('All fields are required.', 'error')
        return redirect(url_for('admin_users'))
    
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'error')
        return redirect(url_for('admin_users'))
    
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('admin_users'))
    
    if role not in ['admin', 'host', 'participant']:
        flash('Invalid role.', 'error')
        return redirect(url_for('admin_users'))
    
    # Create user
    user = User()
    user.username = username
    user.email = email
    user.role = role
    user.set_password(password)
    user.is_verified = True  # Admin-created users are pre-verified
    
    db.session.add(user)
    db.session.commit()
    
    flash(f'User {username} created successfully with role {role}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/host/participants')
@login_required
def host_participants():
    """Enhanced Host view of participants with management features"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all participants and their data
    participants = User.query.filter_by(role='participant').all()
    
    # Get all attempts for quizzes created by this host
    host_quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    quiz_ids = [quiz.id for quiz in host_quizzes]
    
    attempts = QuizAttempt.query.filter(QuizAttempt.quiz_id.in_(quiz_ids)).order_by(QuizAttempt.started_at.desc()).all()
    
    # Get participant statistics
    participant_stats = {}
    for participant in participants:
        participant_attempts = [attempt for attempt in attempts if attempt.participant_id == participant.id]
        completed_attempts = [attempt for attempt in participant_attempts if attempt.status == 'completed']
        avg_score = sum([attempt.score for attempt in completed_attempts if attempt.score]) / len(completed_attempts) if completed_attempts else 0
        
        # Get violation count
        violation_count = 0
        for attempt in participant_attempts:
            violation_count += ProctoringEvent.query.filter_by(attempt_id=attempt.id).count()
        
        # Get recent login
        recent_login = LoginEvent.query.filter_by(user_id=participant.id).order_by(LoginEvent.login_time.desc()).first()
        
        participant_stats[participant.id] = {
            'total_attempts': len(participant_attempts),
            'completed_attempts': len(completed_attempts),
            'avg_score': avg_score,
            'violation_count': violation_count,
            'recent_login': recent_login,
            'is_flagged': False  # Will be tracked via UserViolation model
        }
    
    return render_template('host_participants.html', 
                         participants=participants,
                         attempts=attempts, 
                         host_quizzes=host_quizzes,
                         participant_stats=participant_stats)

@app.route('/host/participant/<int:participant_id>/manage', methods=['GET', 'POST'])
@login_required
def manage_participant(participant_id):
    """Manage individual participant - credentials, performance, flags"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    participant = User.query.get_or_404(participant_id)
    if participant.role != 'participant':
        flash('Invalid participant.', 'error')
        return redirect(url_for('host_participants'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_credentials':
            # Update participant credentials
            new_username = request.form.get('username')
            new_email = request.form.get('email')
            new_password = request.form.get('password')
            
            if new_username:
                participant.username = new_username
            if new_email:
                participant.email = new_email
            if new_password:
                participant.set_password(new_password)
            
            db.session.commit()
            flash('Participant credentials updated successfully.', 'success')
            
        elif action == 'flag_user':
            # Flag user for violations
            violation_record = UserViolation.query.filter_by(user_id=participant_id).first()
            if not violation_record:
                violation_record = UserViolation(user_id=participant_id)
                db.session.add(violation_record)
            
            violation_record.is_flagged = True
            violation_record.flagged_at = datetime.utcnow()
            violation_record.flagged_by = current_user.id
            violation_record.notes = request.form.get('notes', '')
            
            db.session.commit()
            flash('Participant flagged for violations.', 'warning')
            
        elif action == 'unflag_user':
            # Remove flag
            violation_record = UserViolation.query.filter_by(user_id=participant_id).first()
            if violation_record:
                violation_record.is_flagged = False
                violation_record.notes = request.form.get('notes', '')
                db.session.commit()
            flash('Participant flag removed.', 'success')
            
        return redirect(url_for('manage_participant', participant_id=participant_id))
    
    # Get participant data for display
    attempts = QuizAttempt.query.filter_by(participant_id=participant_id).order_by(QuizAttempt.started_at.desc()).all()
    login_events = LoginEvent.query.filter_by(user_id=participant_id).order_by(LoginEvent.login_time.desc()).limit(10).all()
    
    # Get violation data
    violation_record = UserViolation.query.filter_by(user_id=participant_id).first()
    total_violations = 0
    for attempt in attempts:
        total_violations += ProctoringEvent.query.filter_by(attempt_id=attempt.id).count()
    
    return render_template('manage_participant.html', 
                         participant=participant,
                         attempts=attempts,
                         login_events=login_events,
                         violation_record=violation_record,
                         total_violations=total_violations)

@app.route('/host/participant/<int:participant_id>/violations')
@login_required
def view_participant_violations(participant_id):
    """View detailed violation history for a participant"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    participant = User.query.get_or_404(participant_id)
    attempts = QuizAttempt.query.filter_by(participant_id=participant_id).all()
    
    # Get all violations for this participant
    violations = []
    for attempt in attempts:
        attempt_violations = ProctoringEvent.query.filter_by(attempt_id=attempt.id).order_by(ProctoringEvent.timestamp.desc()).all()
        for violation in attempt_violations:
            violations.append({
                'violation': violation,
                'attempt': attempt,
                'quiz': attempt.quiz
            })
    
    violations.sort(key=lambda x: x['violation'].timestamp, reverse=True)
    
    return render_template('participant_violations.html', 
                         participant=participant,
                         violations=violations)

@app.route('/host/login-activity')
@login_required
def host_login_activity():
    """View login activity of all participants"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get recent login events for participants with proper eager loading
    login_events = LoginEvent.query.options(
        db.joinedload(LoginEvent.user)
    ).join(User).filter(
        User.role == 'participant'
    ).order_by(LoginEvent.login_time.desc()).limit(50).all()
    
    return render_template('host_login_activity.html', login_events=login_events)

@app.route('/admin/manage-flags')
@login_required
def admin_manage_flags():
    """Admin interface to manage user flags and retake permissions"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get all flagged users
    flagged_users = db.session.query(UserViolation, User).join(User).filter(
        UserViolation.is_flagged == True
    ).order_by(UserViolation.flagged_at.desc()).all()
    
    # Get recent violations
    recent_violations = db.session.query(ProctoringEvent, QuizAttempt, User, Quiz).join(
        QuizAttempt, ProctoringEvent.attempt_id == QuizAttempt.id
    ).join(
        User, QuizAttempt.participant_id == User.id
    ).join(
        Quiz, QuizAttempt.quiz_id == Quiz.id
    ).filter(
        ProctoringEvent.severity.in_(['high', 'critical'])
    ).order_by(ProctoringEvent.timestamp.desc()).limit(20).all()
    
    return render_template('admin_manage_flags.html', 
                         flagged_users=flagged_users,
                         recent_violations=recent_violations)

@app.route('/admin/unflag-user/<int:user_id>', methods=['POST'])
@login_required
def admin_unflag_user(user_id):
    """Admin action to unflag a user and grant retake permissions"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    violation_record = UserViolation.query.filter_by(user_id=user_id).first()
    if not violation_record:
        flash('User violation record not found.', 'error')
        return redirect(url_for('admin_manage_flags'))
    
    user = User.query.get_or_404(user_id)
    
    # Remove flag
    violation_record.is_flagged = False
    violation_record.unflagged_at = datetime.utcnow()
    violation_record.unflagged_by = current_user.id
    violation_record.notes = request.form.get('notes', '')
    
    db.session.commit()
    
    flash(f'User {user.username} has been unflagged and granted retake permissions.', 'success')
    return redirect(url_for('admin_manage_flags'))

@app.route('/admin/flag-user/<int:user_id>', methods=['POST'])
@login_required
def admin_flag_user(user_id):
    """Admin action to manually flag a user"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    violation_record = UserViolation.query.filter_by(user_id=user_id).first()
    if not violation_record:
        violation_record = UserViolation(user_id=user_id)
        db.session.add(violation_record)
    
    violation_record.is_flagged = True
    violation_record.flagged_at = datetime.utcnow()
    violation_record.flagged_by = current_user.id
    violation_record.notes = request.form.get('notes', 'Manually flagged by administrator')
    violation_record.violation_count = (violation_record.violation_count or 0) + 1
    
    db.session.commit()
    
    flash(f'User {user.username} has been flagged for violations.', 'warning')
    return redirect(url_for('admin_manage_flags'))

@app.route('/api/violations/<int:attempt_id>')
@login_required
def get_violations(attempt_id):
    """Get violations for a quiz attempt"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Check permissions
    if not (current_user.is_admin() or 
            (current_user.is_host() and attempt.quiz.creator_id == current_user.id)):
        return jsonify({'error': 'Access denied'}), 403
    
    violations = [{
        'event_type': event.event_type,
        'description': event.description,
        'severity': event.severity,
        'timestamp': event.timestamp.isoformat() if event.timestamp else None
    } for event in attempt.proctoring_events]
    
    return jsonify({'violations': violations})

@app.route('/api/proctoring/event', methods=['POST'])
@login_required
def log_proctoring_event():
    """Log proctoring violation events"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get current quiz attempt
        attempt_id = data.get('attemptId')
        if not attempt_id:
            return jsonify({'error': 'Attempt ID required'}), 400
        
        attempt = QuizAttempt.query.get_or_404(attempt_id)
        
        # Verify user owns this attempt
        if attempt.participant_id != current_user.id:
            return jsonify({'error': 'Access denied'}), 403
        
        # Create proctoring event
        event = ProctoringEvent(
            attempt_id=attempt_id,
            event_type=data.get('type', 'unknown'),
            details=data.get('description', 'Unknown violation'),
            severity=data.get('severity', 'medium'),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(event)
        
        # Enhanced violation tracking and termination logic
        violation_count = ProctoringEvent.query.filter_by(attempt_id=attempt_id).count() + 1
        high_severity_count = ProctoringEvent.query.filter_by(
            attempt_id=attempt_id, 
            severity='high'
        ).count()
        
        if data.get('severity') == 'high':
            high_severity_count += 1
        
        # Immediate termination conditions
        immediate_termination_types = ['quiz_terminated', 'console_access', 'multiple_instances', 'devtools_opened']
        should_terminate = (
            data.get('type') in immediate_termination_types or
            violation_count >= 3 or
            high_severity_count >= 2
        )
        
        if should_terminate:
            # Terminate the quiz attempt
            attempt.status = 'terminated'
            attempt.completed_at = datetime.utcnow()
            
            # Auto-flag the user for violations
            violation_record = UserViolation.query.filter_by(user_id=current_user.id).first()
            if not violation_record:
                violation_record = UserViolation(user_id=current_user.id)
                db.session.add(violation_record)
            
            violation_record.is_flagged = True
            violation_record.flagged_at = datetime.utcnow()
            violation_record.flagged_by = None  # System flagged
            violation_record.notes = f"Auto-flagged due to quiz termination: {data.get('type')} - {data.get('description')}"
            violation_record.violation_count = (violation_record.violation_count or 0) + 1
            
            # Save current answers before termination
            db.session.commit()
            
            return jsonify({
                'status': 'terminated',
                'message': f'Quiz terminated due to security violation: {data.get("description")}'
            })
        
        db.session.commit()
        
        response_data = {'status': 'logged'}
        
        # Add warning if approaching limits
        if violation_count >= 2:
            response_data['warning'] = f'{3 - violation_count} violations remaining before termination'
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"Error logging proctoring event: {e}")
        return jsonify({'error': 'Internal server error'}), 500

import os
import csv
import io
from werkzeug.utils import secure_filename

@app.route('/quiz/create', methods=['GET', 'POST'])
@login_required
def create_quiz():
    """Create a new quiz with optional file upload"""
    if not current_user.is_host() and not current_user.is_admin():
        flash('Access denied. Host privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    form = QuizForm()
    if form.validate_on_submit():
        # Create the quiz
        quiz = Quiz(
            title=form.title.data,
            description=form.description.data,
            time_limit=form.time_limit.data,
            proctoring_enabled=form.proctoring_enabled.data,
            creator_id=current_user.id
        )
        
        # Handle file upload if selected
        if form.create_from_file.data and form.quiz_file.data:
            file = form.quiz_file.data
            if file and file.filename:
                filename = secure_filename(file.filename)
                
                # Parse file and create questions
                try:
                    questions_data = parse_quiz_file(file)
                    db.session.add(quiz)
                    db.session.commit()
                    
                    # Create questions from parsed data
                    for q_data in questions_data:
                        create_question_from_data(quiz, q_data)
                    
                    flash(f'Quiz created successfully from file "{filename}"! {len(questions_data)} questions added.', 'success')
                    return redirect(url_for('edit_quiz', quiz_id=quiz.id))
                except Exception as e:
                    flash(f'Error parsing file: {str(e)}', 'error')
                    return render_template('create_quiz.html', form=form)
        
        db.session.add(quiz)
        db.session.commit()
        
        flash('Quiz created successfully! Now add questions to your quiz.', 'success')
        return redirect(url_for('edit_quiz', quiz_id=quiz.id))
    
    return render_template('create_quiz.html', form=form)

def parse_quiz_file(file):
    """Parse uploaded quiz file and return questions data"""
    questions_data = []
    content = file.read().decode('utf-8')
    file.seek(0)  # Reset file pointer
    
    if file.filename.endswith('.csv'):
        csv_reader = csv.reader(io.StringIO(content))
        for row in csv_reader:
            if len(row) >= 6:  # Question, Option1, Option2, Option3, Option4, CorrectAnswer
                question_data = {
                    'question_text': row[0].strip(),
                    'options': [row[i].strip() for i in range(1, 5)],
                    'correct_answer': int(row[5]) - 1 if row[5].isdigit() else 0,
                    'points': int(row[6]) if len(row) > 6 and row[6].isdigit() else 1
                }
                questions_data.append(question_data)
    else:  # TXT format
        lines = content.split('\n')
        current_question = None
        options = []
        correct_answer = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_question and options:
                    questions_data.append({
                        'question_text': current_question,
                        'options': options,
                        'correct_answer': correct_answer,
                        'points': 1
                    })
                    current_question = None
                    options = []
                    correct_answer = 0
                continue
                
            if line.startswith('Q:') or line.startswith('Question:'):
                current_question = line.split(':', 1)[1].strip()
            elif line.startswith(('A)', 'B)', 'C)', 'D)')) or line.startswith(('1.', '2.', '3.', '4.')):
                option_text = line[2:].strip() if line[1] in ').' else line[3:].strip()
                if line.startswith('*') or '(correct)' in line.lower():
                    correct_answer = len(options)
                    option_text = option_text.replace('*', '').replace('(correct)', '').strip()
                options.append(option_text)
        
        # Add last question if exists
        if current_question and options:
            questions_data.append({
                'question_text': current_question,
                'options': options,
                'correct_answer': correct_answer,
                'points': 1
            })
    
    return questions_data

def create_question_from_data(quiz, question_data):
    """Create a question and its options from parsed data"""
    question = Question(
        quiz_id=quiz.id,
        question_text=question_data['question_text'],
        question_type='multiple_choice',
        points=question_data.get('points', 1),
        order=len(quiz.questions)
    )
    
    db.session.add(question)
    db.session.commit()
    
    # Create options
    for i, option_text in enumerate(question_data['options']):
        option = QuestionOption(
            question_id=question.id,
            option_text=option_text,
            is_correct=(i == question_data['correct_answer']),
            order=i
        )
        db.session.add(option)
    
    db.session.commit()

@app.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    """Edit quiz and manage questions"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied. You can only edit your own quizzes.', 'error')
        return redirect(url_for('host_dashboard'))
    
    form = QuizForm(obj=quiz)
    question_form = QuestionForm()
    
    if form.validate_on_submit() and 'update_quiz' in request.form:
        quiz.title = form.title.data
        quiz.description = form.description.data
        quiz.time_limit = form.time_limit.data
        quiz.proctoring_enabled = form.proctoring_enabled.data
        quiz.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('edit_quiz', quiz_id=quiz.id))
    
    return render_template('edit_quiz.html', quiz=quiz, form=form, question_form=question_form)

@app.route('/question/<int:question_id>/edit', methods=['POST'])
@login_required
def edit_question(question_id):
    """Edit a specific question"""
    question = Question.query.get_or_404(question_id)
    quiz = question.quiz
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('host_dashboard'))
    
    question.question_text = request.form.get('question_text')
    question.question_type = request.form.get('question_type')
    question.points = int(request.form.get('points', 1))
    
    # Update options for multiple choice questions
    if question.question_type == 'multiple_choice':
        # Remove old options
        QuestionOption.query.filter_by(question_id=question.id).delete()
        
        # Add new options
        for i in range(1, 5):  # Support up to 4 options
            option_text = request.form.get(f'option_{i}')
            if option_text:
                is_correct = request.form.get('correct_option') == str(i)
                option = QuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=is_correct
                )
                db.session.add(option)
    
    db.session.commit()
    flash('Question updated successfully!', 'success')
    return redirect(url_for('edit_quiz', quiz_id=quiz.id))

@app.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    question = Question.query.get_or_404(question_id)
    quiz = question.quiz
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('host_dashboard'))
    
    # Delete associated options first
    QuestionOption.query.filter_by(question_id=question.id).delete()
    # Delete the question
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully!', 'success')
    return redirect(url_for('edit_quiz', quiz_id=quiz.id))

@app.route('/quiz/<int:quiz_id>/add_question', methods=['POST'])
@login_required
def add_question(quiz_id):
    """Add a question to quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('host_dashboard'))
    
    question_text = request.form.get('question_text')
    question_type = request.form.get('question_type', 'multiple_choice')
    points = int(request.form.get('points', 1))
    
    if not question_text:
        flash('Question text is required.', 'error')
        return redirect(url_for('edit_quiz', quiz_id=quiz_id))
    
    question = Question(
        quiz_id=quiz_id,
        question_text=question_text,
        question_type=question_type,
        points=points,
        order=len(quiz.questions)
    )
    
    db.session.add(question)
    db.session.commit()
    
    # Add options for multiple choice questions
    if question_type == 'multiple_choice':
        for i in range(4):  # Default 4 options
            option_text = request.form.get(f'option_{i}')
            is_correct = request.form.get(f'correct_{i}') == 'on'
            
            if option_text:
                option = QuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    is_correct=is_correct,
                    order=i
                )
                db.session.add(option)
    
    elif question_type == 'true_false':
        # Add True/False options
        true_option = QuestionOption(
            question_id=question.id,
            option_text='True',
            is_correct=request.form.get('correct_answer') == 'true',
            order=0
        )
        false_option = QuestionOption(
            question_id=question.id,
            option_text='False',
            is_correct=request.form.get('correct_answer') == 'false',
            order=1
        )
        db.session.add(true_option)
        db.session.add(false_option)
    
    db.session.commit()
    flash('Question added successfully!', 'success')
    return redirect(url_for('edit_quiz', quiz_id=quiz_id))

@app.route('/quiz/<int:quiz_id>')
@login_required
def view_quiz(quiz_id):
    """View quiz details"""
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz_list.html', quiz=quiz)

@app.route('/quiz/<int:quiz_id>/take')
@login_required
def take_quiz(quiz_id):
    """Take a quiz with enhanced security checks"""
    if not current_user.is_participant():
        flash('Access denied. Participant privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if user is flagged for violations - ADMIN ONLY RETAKE PERMISSIONS
    violation_record = UserViolation.query.filter_by(user_id=current_user.id).first()
    if violation_record and violation_record.is_flagged:
        flash('❌ Access denied. Your account has been flagged for security violations. Contact an administrator for retake permissions.', 'error')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if not quiz.is_active:
        flash('This quiz is not currently active.', 'error')
        return redirect(url_for('participant_dashboard'))
    
    # Check if user already has an active attempt
    existing_attempt = QuizAttempt.query.filter_by(
        participant_id=current_user.id,
        quiz_id=quiz_id,
        status='in_progress'
    ).first()
    
    if existing_attempt:
        return redirect(url_for('continue_quiz', attempt_id=existing_attempt.id))
    
    # Create new attempt
    attempt = QuizAttempt(
        participant_id=current_user.id,
        quiz_id=quiz_id
    )
    
    db.session.add(attempt)
    db.session.commit()
    
    return redirect(url_for('continue_quiz', attempt_id=attempt.id))

@app.route('/attempt/<int:attempt_id>')
@login_required
def continue_quiz(attempt_id):
    """Continue taking a quiz"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.participant_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('participant_dashboard'))
    
    if attempt.status != 'in_progress':
        flash('This quiz attempt has already been completed.', 'error')
        return redirect(url_for('quiz_results', attempt_id=attempt_id))
    
    quiz = attempt.quiz
    questions = quiz.questions
    
    # Get existing answers
    existing_answers = {answer.question_id: answer for answer in attempt.answers}
    
    return render_template('take_quiz.html', 
                         attempt=attempt, 
                         quiz=quiz, 
                         questions=questions,
                         existing_answers=existing_answers)

@app.route('/attempt/<int:attempt_id>/submit', methods=['POST'])
@login_required
def submit_quiz(attempt_id):
    """Submit quiz answers"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.participant_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('participant_dashboard'))
    
    if attempt.status != 'in_progress':
        flash('This quiz has already been submitted.', 'error')
        return redirect(url_for('quiz_results', attempt_id=attempt_id))
    
    quiz = attempt.quiz
    
    # Process answers
    for question in quiz.questions:
        answer_key = f'question_{question.id}'
        
        # Check if answer already exists
        existing_answer = Answer.query.filter_by(
            attempt_id=attempt_id,
            question_id=question.id
        ).first()
        
        if existing_answer:
            # Update existing answer
            answer = existing_answer
        else:
            # Create new answer
            answer = Answer(
                attempt_id=attempt_id,
                question_id=question.id
            )
        
        if question.question_type == 'multiple_choice' or question.question_type == 'true_false':
            selected_option_id = request.form.get(answer_key)
            if selected_option_id:
                answer.selected_option_id = int(selected_option_id)
                selected_option = QuestionOption.query.get(selected_option_id)
                answer.is_correct = selected_option.is_correct if selected_option else False
            else:
                answer.is_correct = False
        
        elif question.question_type == 'text':
            answer.text_answer = request.form.get(answer_key, '')
            # For text answers, manual grading would be needed
            answer.is_correct = None
        
        db.session.add(answer)
    
    # Mark attempt as completed
    attempt.completed_at = datetime.utcnow()
    attempt.status = 'completed'
    attempt.calculate_score()
    
    db.session.commit()
    
    flash('Quiz submitted successfully!', 'success')
    return redirect(url_for('quiz_results', attempt_id=attempt_id))

@app.route('/results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    """View quiz results"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.participant_id != current_user.id and attempt.quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    quiz = attempt.quiz
    questions = quiz.questions
    answers = {answer.question_id: answer for answer in attempt.answers}
    
    return render_template('quiz_results.html', 
                         attempt=attempt, 
                         quiz=quiz, 
                         questions=questions,
                         answers=answers)

@app.route('/download/participant-report/<int:attempt_id>')
@login_required
def download_participant_report(attempt_id):
    """Download participant report as PDF with comprehensive error handling"""
    try:
        attempt = QuizAttempt.query.get_or_404(attempt_id)
        
        if attempt.participant_id != current_user.id:
            flash('Access denied.', 'error')
            return redirect(url_for('participant_dashboard'))
    except Exception as e:
        logging.error(f"Error fetching quiz attempt {attempt_id}: {e}")
        flash('Quiz attempt not found.', 'error')
        return redirect(url_for('participant_dashboard'))
    
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from io import BytesIO
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.darkblue,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    
    story = []
    
    # Title
    story.append(Paragraph("Quiz Results Report", title_style))
    story.append(Spacer(1, 20))
    
    # Quiz Information
    quiz_info = [
        ['Quiz Title:', attempt.quiz.title],
        ['Participant:', attempt.participant.username],
        ['Score:', f"{attempt.score:.1f}%" if attempt.score else 'N/A'],
        ['Started:', attempt.started_at.strftime('%Y-%m-%d %H:%M:%S')],
        ['Completed:', attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.completed_at else 'Not completed'],
        ['Status:', attempt.status.title()]
    ]
    
    quiz_table = Table(quiz_info, colWidths=[2*inch, 4*inch])
    quiz_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (1, 0), (1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(quiz_table)
    story.append(Spacer(1, 30))
    
    # Questions and Answers
    story.append(Paragraph("Detailed Results", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    answers = {answer.question_id: answer for answer in attempt.answers}
    
    for i, question in enumerate(attempt.quiz.questions, 1):
        # Question
        story.append(Paragraph(f"Question {i}: {question.question_text}", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        answer = answers.get(question.id)
        
        if question.question_type in ['multiple_choice', 'true_false']:
            # Show options
            options_data = [['Option', 'Your Answer', 'Correct Answer']]
            for option in question.options:
                is_selected = '✓' if answer and answer.selected_option_id == option.id else ''
                is_correct = '✓' if option.is_correct else ''
                options_data.append([option.option_text, is_selected, is_correct])
            
            options_table = Table(options_data, colWidths=[3*inch, 1*inch, 1*inch])
            options_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(options_table)
            
            # Result
            if answer:
                if answer.is_correct:
                    result_text = f"<para><b>Result:</b> <font color='green'>Correct</font> (+{question.points} points)</para>"
                else:
                    result_text = f"<para><b>Result:</b> <font color='red'>Incorrect</font> (0 points)</para>"
            else:
                result_text = "<para><b>Result:</b> Not answered (0 points)</para>"
            
            story.append(Spacer(1, 10))
            story.append(Paragraph(result_text, styles['Normal']))
            
        elif question.question_type == 'text':
            if answer and answer.text_answer:
                story.append(Paragraph(f"<b>Your Answer:</b> {answer.text_answer}", styles['Normal']))
                if answer.is_correct == None:
                    story.append(Paragraph("<i>This answer requires manual grading.</i>", styles['Normal']))
            else:
                story.append(Paragraph("<b>Your Answer:</b> No answer provided", styles['Normal']))
        
        story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return as download
    return send_file(
        BytesIO(buffer.read()),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'quiz_report_{attempt.quiz.title}_{attempt.participant.username}.pdf'
    )

@app.route('/download/host-report/<int:attempt_id>')
@login_required
def download_host_report(attempt_id):
    """Download detailed host report as Excel"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.quiz.creator_id != current_user.id and not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('host_dashboard'))
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, Fill, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from io import BytesIO
    
    # Create workbook
    wb = Workbook()
    
    # Quiz Summary Sheet
    ws1 = wb.active
    ws1.title = "Quiz Summary"
    
    # Headers
    ws1['A1'] = "Quiz Results Summary"
    ws1['A1'].font = Font(size=16, bold=True)
    ws1['A1'].fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    
    # Quiz info
    quiz_data = [
        ["Quiz Title", attempt.quiz.title],
        ["Participant", attempt.participant.username],
        ["Email", attempt.participant.email],
        ["Score", f"{attempt.score:.1f}%" if attempt.score else 'N/A'],
        ["Points Earned", f"{attempt.score * attempt.total_points / 100:.0f}" if attempt.score and attempt.total_points else 'N/A'],
        ["Total Points", attempt.total_points or 0],
        ["Started", attempt.started_at.strftime('%Y-%m-%d %H:%M:%S')],
        ["Completed", attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.completed_at else 'Not completed'],
        ["Status", attempt.status.title()],
        ["Time Taken", str(attempt.completed_at - attempt.started_at) if attempt.completed_at else 'N/A']
    ]
    
    for row, (label, value) in enumerate(quiz_data, 3):
        ws1[f'A{row}'] = label
        ws1[f'B{row}'] = value
        ws1[f'A{row}'].font = Font(bold=True)
    
    # Detailed Answers Sheet
    ws2 = wb.create_sheet("Detailed Answers")
    headers = ["Question #", "Question Text", "Question Type", "Points", "Your Answer", "Correct Answer", "Result", "Points Earned"]
    
    for col, header in enumerate(headers, 1):
        ws2.cell(row=1, column=col, value=header)
        ws2.cell(row=1, column=col).font = Font(bold=True)
        ws2.cell(row=1, column=col).fill = PatternFill(start_color="D9E2F3", end_color="D9E2F3", fill_type="solid")
    
    answers = {answer.question_id: answer for answer in attempt.answers}
    
    for row, question in enumerate(attempt.quiz.questions, 2):
        answer = answers.get(question.id)
        
        ws2.cell(row=row, column=1, value=row-1)
        ws2.cell(row=row, column=2, value=question.question_text)
        ws2.cell(row=row, column=3, value=question.question_type.title())
        ws2.cell(row=row, column=4, value=question.points)
        
        if question.question_type in ['multiple_choice', 'true_false']:
            if answer and answer.selected_option_id:
                selected_option = next((opt for opt in question.options if opt.id == answer.selected_option_id), None)
                ws2.cell(row=row, column=5, value=selected_option.option_text if selected_option else 'Unknown')
            else:
                ws2.cell(row=row, column=5, value='Not answered')
            
            correct_option = next((opt for opt in question.options if opt.is_correct), None)
            ws2.cell(row=row, column=6, value=correct_option.option_text if correct_option else 'No correct answer set')
            
            if answer:
                if answer.is_correct:
                    ws2.cell(row=row, column=7, value='Correct')
                    ws2.cell(row=row, column=8, value=question.points)
                    ws2.cell(row=row, column=7).fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                else:
                    ws2.cell(row=row, column=7, value='Incorrect')
                    ws2.cell(row=row, column=8, value=0)
                    ws2.cell(row=row, column=7).fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            else:
                ws2.cell(row=row, column=7, value='Not answered')
                ws2.cell(row=row, column=8, value=0)
        
        elif question.question_type == 'text':
            ws2.cell(row=row, column=5, value=answer.text_answer if answer and answer.text_answer else 'Not answered')
            ws2.cell(row=row, column=6, value='Manual grading required')
            ws2.cell(row=row, column=7, value='Needs review' if answer and answer.text_answer else 'Not answered')
            ws2.cell(row=row, column=8, value='TBD')
    
    # Auto-adjust column widths
    for ws in [ws1, ws2]:
        for column in ws.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    # Save to BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    return send_file(
        BytesIO(buffer.read()),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'detailed_report_{attempt.quiz.title}_{attempt.participant.username}.xlsx'
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if username is taken by another user
        if form.username.data != current_user.username:
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already taken.', 'error')
                return render_template('profile.html', form=form)
        
        # Check if email is taken by another user
        if form.email.data != current_user.email:
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already registered.', 'error')
                return render_template('profile.html', form=form)
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename:
                import os
                from werkzeug.utils import secure_filename
                
                # Create uploads directory if it doesn't exist
                upload_dir = os.path.join('static', 'uploads', 'profiles')
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file with user id prefix
                filename = f"user_{current_user.id}_{secure_filename(file.filename)}"
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)
                
                # Update user profile picture path
                current_user.profile_picture = f"uploads/profiles/{filename}"

        # Update profile
        current_user.username = form.username.data
        
        # Handle email change without verification requirement
        if form.email.data != current_user.email:
            current_user.email = form.email.data
            current_user.is_verified = True  # Auto-verify for profile updates
            flash('Email updated successfully!', 'success')
        
        # Update password if provided
        if form.current_password.data and form.new_password.data:
            if current_user.check_password(form.current_password.data):
                current_user.set_password(form.new_password.data)
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'error')
                return render_template('profile.html', form=form)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form)


@app.route('/api/quiz/<int:quiz_id>/questions')
@login_required
def get_quiz_questions(quiz_id):
    """Get quiz questions for AJAX loading"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if quiz.creator_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    questions = []
    for question in quiz.questions:
        question_data = {
            'id': question.id,
            'text': question.question_text,
            'type': question.question_type,
            'points': question.points,
            'options': []
        }
        
        for option in question.options:
            question_data['options'].append({
                'id': option.id,
                'text': option.option_text,
                'is_correct': option.is_correct
            })
        
        questions.append(question_data)
    
    return jsonify({'questions': questions})



@app.route('/admin/violations')
@login_required
def admin_violations():
    """Enhanced violations view with filtering like Moodle Proctoring Pro"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get filter parameters
    severity_filter = request.args.get('severity', 'all')
    date_filter = request.args.get('date_range', '7')
    user_filter = request.args.get('user_id', '')
    
    # Build query with filters
    query = ProctoringEvent.query.options(
        db.joinedload(ProctoringEvent.attempt).joinedload(QuizAttempt.participant),
        db.joinedload(ProctoringEvent.attempt).joinedload(QuizAttempt.quiz).joinedload(Quiz.creator)
    )
    
    # Apply filters
    if severity_filter != 'all':
        query = query.filter(ProctoringEvent.severity == severity_filter)
    
    if date_filter != 'all':
        days_ago = datetime.utcnow() - timedelta(days=int(date_filter))
        query = query.filter(ProctoringEvent.timestamp >= days_ago)
    
    if user_filter:
        query = query.join(QuizAttempt).filter(QuizAttempt.participant_id == user_filter)
    
    violations = query.order_by(ProctoringEvent.timestamp.desc()).limit(500).all()
    
    # Get violation statistics
    total_violations = ProctoringEvent.query.count()
    high_severity = ProctoringEvent.query.filter_by(severity='high').count()
    recent_violations = ProctoringEvent.query.filter(
        ProctoringEvent.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).count()
    
    stats = {
        'total_violations': total_violations,
        'high_severity': high_severity,
        'recent_violations': recent_violations
    }
    
    # Get all users for filter dropdown
    users = User.query.filter_by(role='participant').all()
    
    return render_template('admin_violations.html', 
                         violations=violations, 
                         stats=stats,
                         users=users,
                         current_filters={
                             'severity': severity_filter,
                             'date_range': date_filter,
                             'user_id': user_filter
                         })

@app.route('/admin/user/<int:user_id>/edit-credentials', methods=['POST'])
@login_required
def admin_edit_credentials(user_id):
    """Edit user credentials"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow editing your own account
    if user.id == current_user.id:
        flash('You cannot edit your own credentials.', 'error')
        return redirect(url_for('admin_users'))
    
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Validation
    if not username or not email:
        flash('Username and email are required.', 'error')
        return redirect(url_for('admin_users'))
    
    # Check for duplicates
    if username != user.username and User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('admin_users'))
    
    if email != user.email and User.query.filter_by(email=email).first():
        flash('Email already exists.', 'error')
        return redirect(url_for('admin_users'))
    
    # Update credentials
    user.username = username
    user.email = email
    
    if password and len(password) >= 6:
        user.set_password(password)
    
    db.session.commit()
    flash(f'Credentials updated for user {username}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/quiz-management')
@login_required
def admin_quiz_management():
    """Admin quiz management system"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    return render_template('admin_quiz_management.html', quizzes=quizzes)

@app.route('/admin/system-settings')
@login_required
def admin_system_settings():
    """Admin system settings"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('admin_system_settings.html')

@app.route('/admin/violation-appeals')
@login_required
def admin_violation_appeals():
    """Admin page to manage student violation appeals"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get users with pending appeals (flagged users who requested reconsideration)
    pending_appeals = db.session.query(UserViolation, User).join(
        User, UserViolation.user_id == User.id
    ).filter(
        UserViolation.is_flagged == True,
        UserViolation.can_retake == False,
        UserViolation.notes.ilike('%appeal%')
    ).order_by(UserViolation.flagged_at.desc()).all()
    
    # Get recent violations for context
    recent_violations = db.session.query(ProctoringEvent, QuizAttempt, User, Quiz).join(
        QuizAttempt, ProctoringEvent.attempt_id == QuizAttempt.id
    ).join(
        User, QuizAttempt.participant_id == User.id
    ).join(
        Quiz, QuizAttempt.quiz_id == Quiz.id
    ).filter(
        ProctoringEvent.severity.in_(['high', 'critical'])
    ).order_by(ProctoringEvent.timestamp.desc()).limit(50).all()
    
    return render_template('admin_violation_appeals.html', 
                         pending_appeals=pending_appeals,
                         recent_violations=recent_violations)

@app.route('/admin/approve-appeal/<int:violation_id>', methods=['POST'])
@login_required
def admin_approve_appeal(violation_id):
    """Admin approves a student's violation appeal"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    violation = UserViolation.query.get_or_404(violation_id)
    decision = request.form.get('decision')  # 'approve' or 'deny'
    admin_notes = request.form.get('admin_notes', '')
    
    if decision == 'approve':
        violation.can_retake = True
        violation.retake_approved_by = current_user.id
        violation.retake_approved_at = datetime.utcnow()
        violation.notes += f"\n\n[ADMIN APPROVAL - {current_user.username}]: Appeal approved. {admin_notes}"
        flash(f'Appeal approved for {violation.user.username}. They can now retake exams.', 'success')
    else:
        violation.notes += f"\n\n[ADMIN DENIAL - {current_user.username}]: Appeal denied. {admin_notes}"
        flash(f'Appeal denied for {violation.user.username}.', 'info')
    
    db.session.commit()
    return redirect(url_for('admin_violation_appeals'))

@app.route('/student/request-appeal', methods=['GET', 'POST'])
@login_required
def student_request_appeal():
    """Student requests appeal for security violations"""
    if current_user.is_admin() or current_user.is_host():
        flash('This page is for students only.', 'error')
        return redirect(url_for('dashboard'))
    
    # Check if user has violations
    violation = UserViolation.query.filter_by(user_id=current_user.id, is_flagged=True).first()
    
    if request.method == 'POST':
        if not violation:
            flash('You do not have any flagged violations to appeal.', 'error')
            return redirect(url_for('dashboard'))
        
        appeal_reason = request.form.get('appeal_reason', '').strip()
        if not appeal_reason:
            flash('Please provide a reason for your appeal.', 'error')
            return render_template('student_appeal_form.html', violation=violation)
        
        # Add appeal to notes
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        violation.notes += f"\n\n[STUDENT APPEAL - {current_time}]: {appeal_reason}"
        db.session.commit()
        
        flash('Your appeal has been submitted. An administrator will review it shortly.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('student_appeal_form.html', violation=violation)

@app.route('/admin/audit-logs')
@login_required
def admin_audit_logs():
    """Admin audit logs"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get recent activities (for now, we'll show quiz attempts and user registrations)
    recent_attempts = QuizAttempt.query.order_by(QuizAttempt.started_at.desc()).limit(50).all()
    recent_users = User.query.order_by(User.created_at.desc()).limit(20).all()
    
    return render_template('admin_audit_logs.html', recent_attempts=recent_attempts, recent_users=recent_users)

@app.route('/admin/quiz/<int:quiz_id>/toggle-active', methods=['POST'])
@login_required
def admin_toggle_quiz_active(quiz_id):
    """Toggle quiz active status"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    quiz.is_active = not quiz.is_active
    db.session.commit()
    
    status = 'activated' if quiz.is_active else 'deactivated'
    flash(f'Quiz "{quiz.title}" has been {status}.', 'success')
    return redirect(url_for('admin_quiz_management'))

@app.route('/admin/quiz/<int:quiz_id>/delete', methods=['POST'])
@login_required
def admin_delete_quiz(quiz_id):
    """Delete a quiz (admin only)"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Delete all related data in correct order (respecting foreign keys)
    # 1. Delete answers first (they reference quiz_attempt)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()
    for attempt in attempts:
        Answer.query.filter_by(attempt_id=attempt.id).delete()
        ProctoringEvent.query.filter_by(attempt_id=attempt.id).delete()
    
    # 2. Delete quiz attempts
    QuizAttempt.query.filter_by(quiz_id=quiz_id).delete()
    
    # 3. Delete question options and questions
    for question in quiz.questions:
        QuestionOption.query.filter_by(question_id=question.id).delete()
    Question.query.filter_by(quiz_id=quiz_id).delete()
    
    # 4. Finally delete the quiz
    db.session.delete(quiz)
    db.session.commit()
    
    flash(f'Quiz "{quiz.title}" has been permanently deleted.', 'success')
    return redirect(url_for('admin_quiz_management'))

# ===== COURSE MANAGEMENT SYSTEM =====
@app.route('/admin/course-management')
@login_required
def admin_course_management():
    """Admin course management system"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    courses = Course.query.order_by(Course.created_at.desc()).all()
    hosts = User.query.filter_by(role='host').all()
    participants = User.query.filter_by(role='participant').all()
    
    # Get course statistics
    course_stats = {}
    for course in courses:
        stats = {
            'total_hosts': len(course.host_assignments),
            'total_participants': len(course.participant_enrollments),
            'total_quizzes': len(course.quizzes),
            'active_quizzes': len([q for q in course.quizzes if q.is_active])
        }
        course_stats[course.id] = stats
    
    return render_template('admin_course_management.html', 
                         courses=courses, 
                         hosts=hosts, 
                         participants=participants,
                         course_stats=course_stats)

@app.route('/admin/create-course', methods=['POST'])
@login_required
def admin_create_course():
    """Create new course"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    name = request.form.get('name')
    code = request.form.get('code')
    description = request.form.get('description')
    max_participants = request.form.get('max_participants', 100, type=int)
    
    # Validation
    if not all([name, code]):
        flash('Course name and code are required.', 'error')
        return redirect(url_for('admin_course_management'))
    
    if Course.query.filter_by(code=code).first():
        flash('Course code already exists.', 'error')
        return redirect(url_for('admin_course_management'))
    
    # Create course
    course = Course()
    course.name = name
    course.code = code.upper()
    course.description = description
    course.max_participants = max_participants
    
    db.session.add(course)
    db.session.commit()
    
    flash(f'Course "{name}" ({code}) created successfully.', 'success')
    return redirect(url_for('admin_course_management'))

@app.route('/admin/course/<int:course_id>/assign-host', methods=['POST'])
@login_required
def admin_assign_host_to_course(course_id):
    """Assign host to course"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    host_id = request.form.get('host_id', type=int)
    
    if not host_id:
        flash('Please select a host to assign.', 'error')
        return redirect(url_for('admin_course_management'))
    
    host = User.query.get_or_404(host_id)
    if host.role != 'host':
        flash('Selected user is not a host.', 'error')
        return redirect(url_for('admin_course_management'))
    
    # Check if already assigned
    existing = HostCourseAssignment.query.filter_by(host_id=host_id, course_id=course_id).first()
    if existing:
        flash(f'Host {host.username} is already assigned to course {course.name}.', 'warning')
        return redirect(url_for('admin_course_management'))
    
    # Create assignment
    assignment = HostCourseAssignment()
    assignment.host_id = host_id
    assignment.course_id = course_id
    assignment.assigned_by = current_user.id
    
    db.session.add(assignment)
    db.session.commit()
    
    flash(f'Host {host.username} assigned to course {course.name} successfully.', 'success')
    return redirect(url_for('admin_course_management'))

@app.route('/admin/course/<int:course_id>/enroll-participant', methods=['POST'])
@login_required
def admin_enroll_participant_in_course(course_id):
    """Enroll participant in course"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    participant_id = request.form.get('participant_id', type=int)
    
    if not participant_id:
        flash('Please select a participant to enroll.', 'error')
        return redirect(url_for('admin_course_management'))
    
    participant = User.query.get_or_404(participant_id)
    if participant.role != 'participant':
        flash('Selected user is not a participant.', 'error')
        return redirect(url_for('admin_course_management'))
    
    # Check participant limit
    current_enrollments = len(course.participant_enrollments)
    if current_enrollments >= course.max_participants:
        flash(f'Course {course.name} has reached maximum participant limit ({course.max_participants}).', 'error')
        return redirect(url_for('admin_course_management'))
    
    # Check if already enrolled
    existing = ParticipantEnrollment.query.filter_by(participant_id=participant_id, course_id=course_id).first()
    if existing:
        flash(f'Participant {participant.username} is already enrolled in course {course.name}.', 'warning')
        return redirect(url_for('admin_course_management'))
    
    # Create enrollment
    enrollment = ParticipantEnrollment()
    enrollment.participant_id = participant_id
    enrollment.course_id = course_id
    enrollment.enrolled_by = current_user.id
    
    db.session.add(enrollment)
    db.session.commit()
    
    flash(f'Participant {participant.username} enrolled in course {course.name} successfully.', 'success')
    return redirect(url_for('admin_course_management'))

@app.route('/admin/course/<int:course_id>/remove-host/<int:host_id>', methods=['POST'])
@login_required
def admin_remove_host_from_course(course_id, host_id):
    """Remove host from course"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    assignment = HostCourseAssignment.query.filter_by(host_id=host_id, course_id=course_id).first_or_404()
    host_name = assignment.host.username
    course_name = assignment.course.name
    
    db.session.delete(assignment)
    db.session.commit()
    
    flash(f'Host {host_name} removed from course {course_name}.', 'success')
    return redirect(url_for('admin_course_management'))

@app.route('/admin/course/<int:course_id>/remove-participant/<int:participant_id>', methods=['POST'])
@login_required
def admin_remove_participant_from_course(course_id, participant_id):
    """Remove participant from course"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    enrollment = ParticipantEnrollment.query.filter_by(participant_id=participant_id, course_id=course_id).first_or_404()
    participant_name = enrollment.participant.username
    course_name = enrollment.course.name
    
    db.session.delete(enrollment)
    db.session.commit()
    
    flash(f'Participant {participant_name} removed from course {course_name}.', 'success')
    return redirect(url_for('admin_course_management'))

@app.route('/admin/course/<int:course_id>/toggle-status', methods=['POST'])
@login_required
def admin_toggle_course_status(course_id):
    """Toggle course active status"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    course.is_active = not course.is_active
    db.session.commit()
    
    status = 'activated' if course.is_active else 'deactivated'
    flash(f'Course "{course.name}" has been {status}.', 'success')
    return redirect(url_for('admin_course_management'))

@app.route('/admin/course/<int:course_id>/delete', methods=['POST'])
@login_required
def admin_delete_course(course_id):
    """Delete course and all related data"""
    if not current_user.is_admin():
        flash('Access denied. Administrator privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    course = Course.query.get_or_404(course_id)
    course_name = course.name
    
    # Delete all related data
    HostCourseAssignment.query.filter_by(course_id=course_id).delete()
    ParticipantEnrollment.query.filter_by(course_id=course_id).delete()
    
    # Remove course association from quizzes (don't delete quizzes)
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    for quiz in quizzes:
        quiz.course_id = None
    
    db.session.delete(course)
    db.session.commit()
    
    flash(f'Course "{course_name}" has been permanently deleted.', 'success')
    return redirect(url_for('admin_course_management'))

@app.route('/api/quiz/<int:quiz_id>/stats')
@login_required
def get_quiz_stats(quiz_id):
    """Get quiz statistics for admin"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    quiz = Quiz.query.get_or_404(quiz_id)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()
    violations = ProctoringEvent.query.join(QuizAttempt).filter(QuizAttempt.quiz_id == quiz_id).all()
    
    completed_attempts = [a for a in attempts if a.status == 'completed']
    terminated_attempts = [a for a in attempts if a.status == 'terminated']
    
    stats = {
        'total_attempts': len(attempts),
        'completed_attempts': len(completed_attempts),
        'terminated_attempts': len(terminated_attempts),
        'total_violations': len(violations),
        'average_score': sum([a.score for a in completed_attempts if a.score]) / len(completed_attempts) if completed_attempts else 0,
        'highest_score': max([a.score for a in completed_attempts if a.score]) if completed_attempts else 0,
        'common_violation': violations[0].event_type.replace('_', ' ').title() if violations else 'None'
    }
    
    return jsonify(stats)

@app.route('/api/violations/count')
@login_required
def get_violations_count():
    """Get total violation count for admin dashboard"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    count = ProctoringEvent.query.count()
    return jsonify({'count': count})


@app.route('/api/export-logs')
@login_required  
def export_logs():
    """Export audit logs to CSV"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    import csv
    import io
    from flask import make_response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Date', 'User', 'Quiz', 'Action', 'Status', 'Score', 'Violations'])
    
    # Write data
    attempts = QuizAttempt.query.order_by(QuizAttempt.started_at.desc()).all()
    for attempt in attempts:
        writer.writerow([
            attempt.started_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.started_at else 'N/A',
            attempt.participant.username,
            attempt.quiz.title,
            'Quiz Attempt',
            attempt.status,
            f"{attempt.score:.1f}%" if attempt.score else 'N/A',
            len(attempt.answers) if hasattr(attempt, 'answers') else 0
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=audit_logs.csv'
    
    return response

@app.route('/api/export-users')
@login_required  
def export_users():
    """Export user data to CSV"""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    import csv
    import io
    from flask import make_response
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Username', 'Email', 'Role', 'Status', 'Verified', 'Registered', 'Last Login'])
    
    # Write data
    users = User.query.order_by(User.created_at.desc()).all()
    for user in users:
        writer.writerow([
            user.username,
            user.email,
            user.role,
            'Active' if user.is_verified else 'Inactive',
            'Yes' if user.is_verified else 'No',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A',
            user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'
        ])
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=users_export.csv'
    
    return response

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
