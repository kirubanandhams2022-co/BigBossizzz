from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db
from models import User, Quiz, Question, QuestionOption, QuizAttempt, Answer, ProctoringEvent, LoginEvent, UserViolation
from forms import RegistrationForm, LoginForm, QuizForm, QuestionForm, ProfileForm
from email_service import send_verification_email, send_credentials_email, send_login_notification, send_host_login_notification
from datetime import datetime
import json
import logging
from sqlalchemy import func

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

@app.route('/participant/dashboard')
@login_required
def participant_dashboard():
    """Participant dashboard"""
    # Get available quizzes (you might want to implement invitation system)
    available_quizzes = Quiz.query.filter_by(is_active=True).all()
    
    # Get participant's quiz attempts
    my_attempts = QuizAttempt.query.filter_by(participant_id=current_user.id).order_by(QuizAttempt.started_at.desc()).all()
    
    return render_template('participant_dashboard.html', available_quizzes=available_quizzes, my_attempts=my_attempts)

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
    user = User(
        username=username,
        email=email,
        role=role
    )
    user.set_password(password)
    user.is_verified = True  # Admin-created users are pre-verified
    user.is_active = True
    
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
    
    # Get recent login events for participants
    login_events = db.session.query(LoginEvent, User).join(User).filter(
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
    """Download participant report as PDF"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    if attempt.participant_id != current_user.id:
        flash('Access denied.', 'error')
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
        current_user.email = form.email.data
        
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
    """View all system violations"""
    if not current_user.is_admin():
        flash('Access denied.', 'error')
        return redirect(url_for('dashboard'))
    
    violations = ProctoringEvent.query.join(QuizAttempt).join(User).order_by(ProctoringEvent.timestamp.desc()).limit(100).all()
    return render_template('admin_violations.html', violations=violations)

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
